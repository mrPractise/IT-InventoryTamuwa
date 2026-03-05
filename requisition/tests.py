"""
Requisition app tests - models, views, and one-way links.
Run with: python manage.py test requisition
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from requisition.models import Requisition, RequisitionItem
from assets.models import Category, StatusOption, Asset


def make_admin(username="req_admin"):
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


def make_viewer(username="req_viewer"):
    user = User.objects.create_user(username=username, password="testpass123")
    from users.models import UserProfile
    UserProfile.objects.get_or_create(
        user=user,
        defaults={"role": "viewer", "is_first_login": False, "must_change_password": False},
    )
    return user


def make_requisition(req_no="REQ-001", company="Tamuwa", status="Pending", user=None):
    return Requisition.objects.create(
        req_no=req_no,
        company=company,
        title="Test Requisition " + req_no,
        description="Test description",
        status=status,
        created_by=user,
    )


# ---- Model Tests ----

class RequisitionModelTest(TestCase):
    def setUp(self):
        self.admin = make_admin()

    def test_create_requisition(self):
        req = make_requisition(user=self.admin)
        self.assertEqual(req.req_no, "REQ-001")
        self.assertEqual(req.status, "Pending")
        self.assertIn("REQ-001", str(req))

    def test_total_amount_only_approved(self):
        req = make_requisition(user=self.admin)
        RequisitionItem.objects.create(
            requisition=req, item_name="Laptop", item_type="Asset",
            unit_price=50000, quantity=2, is_approved=True
        )
        RequisitionItem.objects.create(
            requisition=req, item_name="Mouse", item_type="Asset",
            unit_price=1000, quantity=3, is_approved=False
        )
        self.assertEqual(req.total_amount, 100000)

    def test_total_amount_all_includes_unapproved(self):
        req = make_requisition(user=self.admin)
        RequisitionItem.objects.create(
            requisition=req, item_name="Laptop", item_type="Asset",
            unit_price=50000, quantity=1, is_approved=True
        )
        RequisitionItem.objects.create(
            requisition=req, item_name="Mouse", item_type="Asset",
            unit_price=1000, quantity=1, is_approved=False
        )
        self.assertEqual(req.total_amount_all, 51000)

    def test_unique_req_no_per_company(self):
        make_requisition("REQ-DUP", "Tera", user=self.admin)
        with self.assertRaises(Exception):
            make_requisition("REQ-DUP", "Tera", user=self.admin)

    def test_same_req_no_allowed_for_different_companies(self):
        make_requisition("REQ-SAME", "Tera", user=self.admin)
        req2 = make_requisition("REQ-SAME", "Flux", user=self.admin)
        self.assertEqual(req2.req_no, "REQ-SAME")
        self.assertEqual(req2.company, "Flux")

    def test_status_choices(self):
        valid_statuses = ["Pending", "Approved", "Rejected", "On Hold", "Bought"]
        for st in valid_statuses:
            req = Requisition.objects.create(
                req_no="REQ-" + st[:3], company="Tamuwa",
                title="Test " + st, status=st, created_by=self.admin
            )
            self.assertEqual(req.status, st)


class RequisitionItemModelTest(TestCase):
    def setUp(self):
        self.admin = make_admin()
        self.req = make_requisition(user=self.admin)

    def test_item_total_price(self):
        item = RequisitionItem.objects.create(
            requisition=self.req, item_name="Monitor", item_type="Asset",
            unit_price=15000, quantity=3
        )
        self.assertEqual(item.total_price, 45000)

    def test_item_type_choices(self):
        asset_item = RequisitionItem.objects.create(
            requisition=self.req, item_name="HDD", item_type="Asset",
            unit_price=5000, quantity=1
        )
        service_item = RequisitionItem.objects.create(
            requisition=self.req, item_name="Repair", item_type="Service",
            unit_price=2000, quantity=1
        )
        self.assertEqual(asset_item.item_type, "Asset")
        self.assertEqual(service_item.item_type, "Service")

    def test_processed_flag(self):
        from django.utils import timezone
        item = RequisitionItem.objects.create(
            requisition=self.req, item_name="Router", item_type="Asset",
            unit_price=10000, quantity=1
        )
        self.assertFalse(item.is_processed)
        item.is_processed = True
        item.processed_at = timezone.now()
        item.save()
        self.assertTrue(item.is_processed)


# ---- One-Way Linking Tests ----

class RequisitionOnewayLinkTest(TestCase):
    def setUp(self):
        self.admin = make_admin()

    def test_requisition_can_link_issue(self):
        from issues.models import Issue
        issue = Issue.objects.create(
            title="Network Down", priority="High", status="Open",
            reported_by=self.admin
        )
        req = make_requisition(user=self.admin)
        req.linked_issue = issue
        req.save()
        self.assertEqual(req.linked_issue, issue)

    def test_requisition_can_link_project(self):
        from issues.models import Project
        project = Project.objects.create(
            title="Office Setup", priority="Medium", status="Pending",
            reported_by=self.admin
        )
        req = make_requisition(user=self.admin)
        req.linked_project = project
        req.save()
        self.assertEqual(req.linked_project, project)

    def test_issue_has_reverse_requisitions(self):
        from issues.models import Issue
        issue = Issue.objects.create(
            title="Server Down", priority="Critical", status="Open",
            reported_by=self.admin
        )
        req1 = make_requisition("R-01", user=self.admin)
        req2 = make_requisition("R-02", user=self.admin)
        req1.linked_issue = issue
        req1.save()
        req2.linked_issue = issue
        req2.save()
        linked = issue.requisitions.all()
        self.assertEqual(linked.count(), 2)

    def test_issue_has_no_direct_requisition_field(self):
        from issues.models import Issue
        field_names = [f.name for f in Issue._meta.get_fields()]
        self.assertNotIn("requisition", field_names)


# ---- View Tests ----

class RequisitionViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = make_admin()
        self.viewer = make_viewer()
        self.req = make_requisition(user=self.admin)

    def test_list_requires_login(self):
        resp = self.client.get(reverse("requisition:list"))
        self.assertEqual(resp.status_code, 302)

    def test_list_accessible(self):
        self.client.login(username="req_admin", password="testpass123")
        resp = self.client.get(reverse("requisition:list"))
        self.assertEqual(resp.status_code, 200)

    def test_detail_view(self):
        self.client.login(username="req_admin", password="testpass123")
        resp = self.client.get(reverse("requisition:detail", args=[self.req.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "REQ-001")

    def test_unapproved_items_view(self):
        self.client.login(username="req_admin", password="testpass123")
        resp = self.client.get(reverse("requisition:unapproved_items"))
        self.assertEqual(resp.status_code, 200)

    def test_bought_items_queue_view(self):
        self.client.login(username="req_admin", password="testpass123")
        resp = self.client.get(reverse("requisition:bought_items_queue"))
        self.assertEqual(resp.status_code, 200)

    def test_viewer_cannot_create_requisition(self):
        self.client.login(username="req_viewer", password="testpass123")
        resp = self.client.get(reverse("requisition:create"))
        self.assertEqual(resp.status_code, 302)
