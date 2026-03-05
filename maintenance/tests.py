"""
Maintenance app tests - models, views, and signals.
Run with: python manage.py test maintenance
"""
import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from assets.models import Asset, Category, StatusOption, Department, Person
from maintenance.models import MaintenanceLog, ActionTakenOption


def make_status(name="Available"):
    return StatusOption.objects.get_or_create(name=name, defaults={"color": "#aaa"})[0]


def make_category(name="Laptop", short_code="LAP"):
    return Category.objects.get_or_create(name=name, defaults={"short_code": short_code})[0]


def make_admin(username="m_admin"):
    user = User.objects.create_user(username=username, password="testpass123")
    user.is_superuser = True
    user.is_staff = True
    user.save()
    from users.models import UserProfile
    UserProfile.objects.get_or_create(
        user=user,
        defaults={"role": "super_admin", "is_first_login": False, "must_change_password": False},
    )
    return user


def make_asset(asset_id="LAP-001", user=None):
    if user is None:
        user = User.objects.filter(is_superuser=True).first()
        if user is None:
            user = make_admin("_maint_owner")
    return Asset.objects.create(
        asset_id=asset_id,
        category=make_category(),
        status=make_status(),
        model_description="Test Asset",
        serial_number="SN-" + asset_id,
        created_by=user,
        updated_by=user,
    )


def make_action(name="Investigation"):
    return ActionTakenOption.objects.get_or_create(name=name)[0]


# ---- Model Tests ----

class ActionTakenOptionModelTest(TestCase):
    def test_create_and_str(self):
        action = make_action("To Nairobi")
        self.assertEqual(str(action), "To Nairobi")
        self.assertTrue(action.is_active)

    def test_unique_name(self):
        make_action("Decommissioned")
        with self.assertRaises(Exception):
            ActionTakenOption.objects.create(name="Decommissioned")


class MaintenanceLogModelTest(TestCase):
    def setUp(self):
        self.user = make_admin("mlog_admin")

    def test_create_log(self):
        asset = make_asset("MNT-001", user=self.user)
        log = MaintenanceLog.objects.create(
            asset=asset,
            date_reported=datetime.date.today(),
            description="Screen cracked",
            maintenance_status="Open",
        )
        self.assertEqual(log.asset, asset)
        self.assertEqual(log.maintenance_status, "Open")
        self.assertIn("MNT-001", str(log))

    def test_log_with_action(self):
        asset = make_asset("MNT-002", user=self.user)
        action = make_action("Waiting Approval")
        log = MaintenanceLog.objects.create(
            asset=asset,
            date_reported=datetime.date.today(),
            description="Battery dead",
            action_taken=action,
            maintenance_status="Open",
        )
        self.assertEqual(log.action_taken.name, "Waiting Approval")

    def test_close_log_sets_date_completed(self):
        asset = make_asset("MNT-003", user=self.user)
        log = MaintenanceLog.objects.create(
            asset=asset,
            date_reported=datetime.date.today(),
            description="Power issue",
            maintenance_status="Open",
        )
        log.maintenance_status = "Closed"
        log.date_completed = datetime.date.today()
        log.save()
        self.assertEqual(log.maintenance_status, "Closed")
        self.assertIsNotNone(log.date_completed)


# ---- Signal Tests ----

class MaintenanceSignalTest(TestCase):
    def setUp(self):
        self.user = make_admin("msig_admin")
        make_status("Available")
        make_status("Under Maintenance")

    def test_under_maintenance_status_creates_log(self):
        asset = make_asset("SIG-M-001", user=self.user)
        under_maint = make_status("Under Maintenance")
        asset.status = under_maint
        asset.save()
        self.assertTrue(
            MaintenanceLog.objects.filter(asset=asset, maintenance_status="Open").exists()
        )

    def test_signal_loop_guard_prevents_infinite_recursion(self):
        asset = make_asset("SIG-M-002", user=self.user)
        under_maint = make_status("Under Maintenance")
        asset.status = under_maint
        asset.save()

        log = MaintenanceLog.objects.filter(asset=asset, maintenance_status="Open").first()
        log.maintenance_status = "Closed"
        log.date_completed = datetime.date.today()
        log.save()  # Should not raise RecursionError

        asset.refresh_from_db()
        self.assertNotEqual(asset.status.name, "Under Maintenance")

    def test_closing_log_sets_asset_available(self):
        asset = make_asset("SIG-M-003", user=self.user)
        under_maint = make_status("Under Maintenance")
        asset.status = under_maint
        asset.save()

        log = MaintenanceLog.objects.filter(asset=asset, maintenance_status="Open").first()
        log.maintenance_status = "Closed"
        log.date_completed = datetime.date.today()
        log.save()

        asset.refresh_from_db()
        self.assertEqual(asset.status.name, "Available")


# ---- View Tests ----

class MaintenanceViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = make_admin()
        self.asset = make_asset("MNT-V-001", user=self.admin)
        self.log = MaintenanceLog.objects.create(
            asset=self.asset,
            date_reported=datetime.date.today(),
            description="Keyboard broken",
            maintenance_status="Open",
        )

    def test_list_requires_login(self):
        resp = self.client.get(reverse("maintenance:list"))
        self.assertEqual(resp.status_code, 302)

    def test_list_accessible_to_admin(self):
        self.client.login(username="m_admin", password="testpass123")
        resp = self.client.get(reverse("maintenance:list"))
        self.assertEqual(resp.status_code, 200)

    def test_detail_view(self):
        self.client.login(username="m_admin", password="testpass123")
        resp = self.client.get(reverse("maintenance:detail", args=[self.log.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Keyboard broken")

    def test_create_view_get(self):
        self.client.login(username="m_admin", password="testpass123")
        resp = self.client.get(reverse("maintenance:create"))
        self.assertEqual(resp.status_code, 200)

    def test_edit_view(self):
        self.client.login(username="m_admin", password="testpass123")
        resp = self.client.get(reverse("maintenance:update", args=[self.log.pk]))
        self.assertEqual(resp.status_code, 200)
