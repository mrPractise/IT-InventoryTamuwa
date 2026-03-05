"""
Users app tests - authentication, roles, profile, and access control.
Run with: python manage.py test users
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from users.models import UserProfile
from assets.models import Department


def make_user(username, role="viewer", first_login=False, must_change=False):
    user = User.objects.create_user(username=username, password="testpass123")
    if role in ("super_admin", "admin"):
        user.is_superuser = True
        user.is_staff = True
        user.save()
    UserProfile.objects.get_or_create(
        user=user,
        defaults={
            "role": role,
            "is_first_login": first_login,
            "must_change_password": must_change,
        },
    )
    return user


# ---- UserProfile Model Tests ----

class UserProfileModelTest(TestCase):
    def test_create_profile_and_str(self):
        user = make_user("proftest", role="admin")
        profile = user.profile
        self.assertIn("proftest", str(profile))
        self.assertEqual(profile.role, "admin")

    def test_is_admin_check(self):
        admin = make_user("u_admin", role="admin")
        viewer = make_user("u_viewer", role="viewer")
        self.assertTrue(admin.profile.is_admin())
        self.assertFalse(viewer.profile.is_admin())

    def test_is_super_admin_check(self):
        super_admin = make_user("u_superadmin", role="super_admin")
        self.assertTrue(super_admin.profile.is_super_admin())

    def test_can_edit_assets(self):
        admin = make_user("u_admin2", role="admin")
        technician = make_user("u_tech", role="technician")
        viewer = make_user("u_view2", role="viewer")
        self.assertTrue(admin.profile.can_edit_assets())
        self.assertFalse(technician.profile.can_edit_assets())
        self.assertFalse(viewer.profile.can_edit_assets())

    def test_needs_password_change_first_login(self):
        user = make_user("u_first", role="viewer", first_login=True)
        self.assertTrue(user.profile.needs_password_change())

    def test_needs_password_change_must_change(self):
        user = make_user("u_must", role="viewer", must_change=True)
        self.assertTrue(user.profile.needs_password_change())

    def test_no_password_change_needed(self):
        user = make_user("u_ok", role="viewer", first_login=False, must_change=False)
        self.assertFalse(user.profile.needs_password_change())

    def test_can_view_maintenance(self):
        admin = make_user("u_amaint", role="admin")
        tech = make_user("u_tmaint", role="technician")
        viewer = make_user("u_vmaint", role="viewer")
        self.assertTrue(admin.profile.can_view_maintenance())
        self.assertTrue(tech.profile.can_view_maintenance())
        self.assertFalse(viewer.profile.can_view_maintenance())


# ---- Authentication Tests ----

class AuthenticationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user("auth_user", role="viewer")

    def test_login_page_accessible(self):
        resp = self.client.get(reverse("login"))
        self.assertEqual(resp.status_code, 200)

    def test_valid_login_redirects_to_dashboard(self):
        resp = self.client.post(reverse("login"), {
            "username": "auth_user", "password": "testpass123"
        })
        self.assertRedirects(resp, reverse("dashboard:home"))

    def test_invalid_login_stays_on_page(self):
        resp = self.client.post(reverse("login"), {
            "username": "auth_user", "password": "wrongpass"
        })
        self.assertEqual(resp.status_code, 200)

    def test_first_login_redirects_to_password_change(self):
        make_user("firstlogin_user", role="viewer", first_login=True)
        resp = self.client.post(reverse("login"), {
            "username": "firstlogin_user", "password": "testpass123"
        })
        self.assertRedirects(resp, reverse("users:password_change_required"))

    def test_must_change_password_redirect(self):
        make_user("mustchange_user", role="viewer", must_change=True)
        resp = self.client.post(reverse("login"), {
            "username": "mustchange_user", "password": "testpass123"
        })
        self.assertRedirects(resp, reverse("users:password_change_required"))

    def test_logout(self):
        self.client.login(username="auth_user", password="testpass123")
        resp = self.client.post(reverse("users:logout"))
        self.assertEqual(resp.status_code, 302)


# ---- View Access Control Tests ----

class UserViewAccessTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = make_user("access_admin", role="super_admin")
        self.viewer = make_user("access_viewer", role="viewer")

    def test_profile_requires_login(self):
        resp = self.client.get(reverse("users:profile"))
        self.assertEqual(resp.status_code, 302)

    def test_profile_accessible_to_any_authenticated(self):
        self.client.login(username="access_viewer", password="testpass123")
        resp = self.client.get(reverse("users:profile"))
        self.assertEqual(resp.status_code, 200)

    def test_directory_accessible_to_any_authenticated(self):
        self.client.login(username="access_viewer", password="testpass123")
        resp = self.client.get(reverse("users:directory"))
        self.assertEqual(resp.status_code, 200)

    def test_user_management_requires_admin(self):
        self.client.login(username="access_viewer", password="testpass123")
        resp = self.client.get(reverse("users:user_list"))
        self.assertEqual(resp.status_code, 302)

    def test_user_management_accessible_to_admin(self):
        self.client.login(username="access_admin", password="testpass123")
        resp = self.client.get(reverse("users:user_list"))
        self.assertEqual(resp.status_code, 200)

    def test_add_person_requires_admin(self):
        self.client.login(username="access_viewer", password="testpass123")
        resp = self.client.get(reverse("users:add_person"))
        self.assertEqual(resp.status_code, 302)

    def test_add_person_accessible_to_admin(self):
        self.client.login(username="access_admin", password="testpass123")
        resp = self.client.get(reverse("users:add_person"))
        self.assertEqual(resp.status_code, 200)

    def test_add_department_accessible_to_admin(self):
        self.client.login(username="access_admin", password="testpass123")
        resp = self.client.get(reverse("users:add_department"))
        self.assertEqual(resp.status_code, 200)


# ---- Dashboard / Notifications View Tests ----

class DashboardViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user("dash_user", role="viewer")

    def test_dashboard_requires_login(self):
        resp = self.client.get(reverse("dashboard:home"))
        self.assertEqual(resp.status_code, 302)

    def test_dashboard_accessible(self):
        self.client.login(username="dash_user", password="testpass123")
        resp = self.client.get(reverse("dashboard:home"))
        self.assertEqual(resp.status_code, 200)

    def test_notifications_accessible(self):
        self.client.login(username="dash_user", password="testpass123")
        resp = self.client.get(reverse("dashboard:notifications"))
        self.assertEqual(resp.status_code, 200)

    def test_notifications_page_contains_header(self):
        self.client.login(username="dash_user", password="testpass123")
        resp = self.client.get(reverse("dashboard:notifications"))
        self.assertContains(resp, "System Notifications")

    def test_notifications_contains_filters(self):
        """Filter buttons appear only when there are active notifications."""
        from issues.models import Issue
        from assets.models import Department
        dept = Department.objects.get_or_create(name="TestDept")[0]
        Issue.objects.create(
            title="Critical server down",
            priority="Critical",
            status="Open",
            department=dept,
            reported_by=self.user,
        )
        self.client.login(username="dash_user", password="testpass123")
        resp = self.client.get(reverse("dashboard:notifications"))
        self.assertContains(resp, "Critical")
        self.assertContains(resp, "Warnings")


# ---- DRF API Tests ----

class UserAPITest(TestCase):
    def setUp(self):
        from rest_framework.test import APIClient
        self.client = APIClient()
        self.admin = make_user("api_user_admin", role="super_admin")
        self.viewer = make_user("api_user_viewer", role="viewer")

    def test_assets_api_accessible_to_viewer(self):
        self.client.force_authenticate(user=self.viewer)
        resp = self.client.get("/api/assets/")
        self.assertEqual(resp.status_code, 200)

    def test_api_requires_authentication(self):
        resp = self.client.get("/api/assets/")
        self.assertEqual(resp.status_code, 403)

    def test_maintenance_logs_api_accessible(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get("/api/maintenance-logs/")
        self.assertEqual(resp.status_code, 200)

    def test_action_taken_options_api_accessible(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get("/api/action-taken-options/")
        self.assertEqual(resp.status_code, 200)

    def test_technicians_api_accessible(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get("/api/technicians/")
        self.assertEqual(resp.status_code, 200)

    def test_dashboard_stats_api(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get("/api/dashboard/")
        self.assertEqual(resp.status_code, 200)
