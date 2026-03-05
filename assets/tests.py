"""
Assets app tests — models, views, signals, and DRF API.
Run with: python manage.py test assets
"""
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from assets.models import (
    Asset, Category, Department, Person,
    StatusOption, AssignmentHistory, ActivityLog,
)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def make_status(name="Available"):
    return StatusOption.objects.get_or_create(name=name, defaults={"color": "#aaa"})[0]


def make_category(name="Laptop", short_code="LAP"):
    return Category.objects.get_or_create(name=name, defaults={"short_code": short_code})[0]


def make_department(name="IT"):
    return Department.objects.get_or_create(name=name)[0]


def make_person(first="John", last="Doe", dept=None):
    return Person.objects.create(first_name=first, last_name=last, department=dept)


def make_admin_user(username="admin_user"):
    user = User.objects.create_user(username=username, password="testpass123")
    user.is_staff = True
    user.is_superuser = True
    user.save()
    from users.models import UserProfile
    UserProfile.objects.get_or_create(
        user=user,
        defaults={"role": "super_admin", "is_first_login": False, "must_change_password": False},
    )
    return user


def make_viewer_user(username="viewer_user"):
    user = User.objects.create_user(username=username, password="testpass123")
    from users.models import UserProfile
    UserProfile.objects.get_or_create(
        user=user,
        defaults={"role": "viewer", "is_first_login": False, "must_change_password": False},
    )
    return user


def make_asset(asset_id="LAP-001", category=None, status=None, user=None, **kwargs):
    """Create an asset; user is required because Asset.save() calls full_clean()."""
    if user is None:
        user = User.objects.filter(is_superuser=True).first()
        if user is None:
            user = make_admin_user("_asset_owner")
    category = category or make_category()
    status = status or make_status()
    return Asset.objects.create(
        asset_id=asset_id,
        category=category,
        status=status,
        model_description="Test Laptop",
        serial_number=f"SN-{asset_id}",
        created_by=user,
        updated_by=user,
        **kwargs,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Model Tests
# ──────────────────────────────────────────────────────────────────────────────

class CategoryModelTest(TestCase):
    def test_create_and_str(self):
        cat = make_category("Monitor", "MON")
        self.assertEqual(str(cat), "Monitor")
        self.assertEqual(cat.short_code, "MON")

    def test_unique_name(self):
        make_category("Printer", "PRT")
        with self.assertRaises(Exception):
            Category.objects.create(name="Printer", short_code="PRT2")


class StatusOptionModelTest(TestCase):
    def test_create_and_str(self):
        st = make_status("In Use")
        self.assertEqual(str(st), "In Use")
        self.assertTrue(st.is_active)


class DepartmentModelTest(TestCase):
    def test_create_and_str(self):
        dept = make_department("Finance")
        self.assertEqual(str(dept), "Finance")


class PersonModelTest(TestCase):
    def test_full_name(self):
        person = make_person("Jane", "Smith")
        self.assertEqual(person.full_name, "Jane Smith")
        self.assertEqual(str(person), "Jane Smith")

    def test_department_link(self):
        dept = make_department("HR")
        person = make_person("Bob", "Brown", dept=dept)
        self.assertEqual(person.department, dept)


class AssetModelTest(TestCase):
    def setUp(self):
        self.user = make_admin_user()

    def test_create_asset(self):
        asset = make_asset("LAP-001", user=self.user)
        self.assertEqual(asset.asset_id, "LAP-001")
        self.assertFalse(asset.is_deleted)
        self.assertEqual(str(asset), "LAP-001 - Test Laptop")

    def test_cannot_set_in_use_without_assignment(self):
        from django.core.exceptions import ValidationError
        status_in_use = make_status("In Use")
        with self.assertRaises((ValidationError, Exception)):
            make_asset("LAP-002", status=status_in_use, user=self.user)

    def test_in_use_with_person_is_valid(self):
        status_in_use = make_status("In Use")
        person = make_person()
        asset = make_asset(
            "LAP-003", status=status_in_use, assigned_to=person, user=self.user
        )
        self.assertEqual(asset.status.name, "In Use")
        self.assertEqual(asset.assigned_to, person)

    def test_soft_delete(self):
        asset = make_asset("LAP-004", user=self.user)
        asset.is_deleted = True
        asset.save()
        self.assertFalse(Asset.objects.filter(asset_id="LAP-004", is_deleted=False).exists())
        self.assertTrue(Asset.objects.filter(asset_id="LAP-004", is_deleted=True).exists())

    def test_unique_serial_per_category(self):
        cat = make_category("Keyboard", "KBD")
        make_asset("KBD-001", category=cat, user=self.user)
        with self.assertRaises(Exception):
            Asset.objects.create(
                asset_id="KBD-002",
                category=cat,
                status=make_status(),
                model_description="Another Keyboard",
                serial_number="SN-KBD-001",
                created_by=self.user,
                updated_by=self.user,
            )


# ──────────────────────────────────────────────────────────────────────────────
# Signal Tests
# ──────────────────────────────────────────────────────────────────────────────

class AssetMaintenanceSignalTest(TestCase):
    def setUp(self):
        self.user = make_admin_user("sig_user")
        make_status("Available")
        make_status("Under Maintenance")

    def test_asset_to_maintenance_status_creates_log(self):
        from maintenance.models import MaintenanceLog
        asset = make_asset("SIG-001", user=self.user)
        maintenance_status = make_status("Under Maintenance")
        asset.status = maintenance_status
        asset.save()
        self.assertTrue(
            MaintenanceLog.objects.filter(asset=asset, maintenance_status="Open").exists()
        )

    def test_closing_maintenance_log_updates_asset_status(self):
        import datetime
        from maintenance.models import MaintenanceLog
        asset = make_asset("SIG-002", user=self.user)
        maint_status = make_status("Under Maintenance")
        asset.status = maint_status
        asset.save()

        log = MaintenanceLog.objects.filter(asset=asset, maintenance_status="Open").first()
        self.assertIsNotNone(log)
        log.maintenance_status = "Closed"
        log.date_completed = datetime.date.today()
        log.save()

        asset.refresh_from_db()
        self.assertEqual(asset.status.name, "Available")


# ──────────────────────────────────────────────────────────────────────────────
# View Tests
# ──────────────────────────────────────────────────────────────────────────────

class AssetViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = make_admin_user()
        self.viewer = make_viewer_user()
        self.asset = make_asset("LAP-010", user=self.admin)

    def test_list_requires_login(self):
        resp = self.client.get(reverse("assets:list"))
        self.assertRedirects(resp, "/accounts/login/?next=/assets/")

    def test_list_accessible_to_authenticated(self):
        self.client.login(username="admin_user", password="testpass123")
        resp = self.client.get(reverse("assets:list"))
        self.assertEqual(resp.status_code, 200)

    def test_detail_view(self):
        self.client.login(username="admin_user", password="testpass123")
        resp = self.client.get(reverse("assets:detail", args=[self.asset.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "LAP-010")

    def test_viewer_cannot_create_asset(self):
        self.client.login(username="viewer_user", password="testpass123")
        resp = self.client.get(reverse("assets:create"))
        self.assertEqual(resp.status_code, 302)

    def test_admin_can_create_asset(self):
        self.client.login(username="admin_user", password="testpass123")
        resp = self.client.get(reverse("assets:create"))
        self.assertEqual(resp.status_code, 200)

    def test_soft_delete_via_post(self):
        asset = make_asset("DEL-001", user=self.admin)
        self.client.login(username="admin_user", password="testpass123")
        resp = self.client.post(reverse("assets:delete", args=[asset.pk]))
        self.assertRedirects(resp, reverse("assets:list"))
        asset.refresh_from_db()
        self.assertTrue(asset.is_deleted)

    def test_excel_export(self):
        self.client.login(username="admin_user", password="testpass123")
        resp = self.client.get(reverse("assets:export_excel"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("application/vnd", resp["Content-Type"])

    def test_get_next_asset_id(self):
        self.client.login(username="admin_user", password="testpass123")
        cat = make_category()
        resp = self.client.get(
            reverse("assets:get_next_asset_id"), {"category_id": cat.pk}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("asset_id", data)


# ──────────────────────────────────────────────────────────────────────────────
# DRF API Tests
# ──────────────────────────────────────────────────────────────────────────────

class AssetAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin_user("api_admin")
        self.viewer = make_viewer_user("api_viewer")
        self.asset = make_asset("API-001", user=self.admin)

    def test_api_list_unauthenticated(self):
        resp = self.client.get("/api/assets/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_list_authenticated(self):
        self.client.force_authenticate(user=self.viewer)
        resp = self.client.get("/api/assets/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("results", resp.data)

    def test_api_detail(self):
        self.client.force_authenticate(user=self.viewer)
        resp = self.client.get(f"/api/assets/{self.asset.pk}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["asset_id"], "API-001")

    def test_api_filter_by_category(self):
        self.client.force_authenticate(user=self.viewer)
        cat = make_category()
        resp = self.client.get(f"/api/assets/?category={cat.pk}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_api_search(self):
        self.client.force_authenticate(user=self.viewer)
        resp = self.client.get("/api/assets/?search=API-001")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(resp.data["count"], 1)

    def test_api_categories_list(self):
        self.client.force_authenticate(user=self.viewer)
        resp = self.client.get("/api/categories/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_api_statuses_list(self):
        self.client.force_authenticate(user=self.viewer)
        resp = self.client.get("/api/status-options/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_api_departments_list(self):
        self.client.force_authenticate(user=self.viewer)
        resp = self.client.get("/api/departments/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_api_viewer_cannot_delete_asset(self):
        self.client.force_authenticate(user=self.viewer)
        resp = self.client.delete(f"/api/assets/{self.asset.pk}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_activity_logs(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get("/api/activity-logs/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_api_maintenance_logs(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get("/api/maintenance-logs/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_api_assignment_history(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get("/api/assignment-history/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_api_technicians(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get("/api/technicians/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
