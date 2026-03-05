"""
Issues app tests - models, views, and project items.
Run with: python manage.py test issues
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from issues.models import Issue, IssueComment, Project, ProjectItem, ProjectComment


def make_admin(username="iss_admin"):
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


def make_viewer(username="iss_viewer"):
    user = User.objects.create_user(username=username, password="testpass123")
    from users.models import UserProfile
    UserProfile.objects.get_or_create(
        user=user,
        defaults={"role": "viewer", "is_first_login": False, "must_change_password": False},
    )
    return user


# ---- Issue Model Tests ----

class IssueModelTest(TestCase):
    def setUp(self):
        self.admin = make_admin()

    def test_create_issue(self):
        issue = Issue.objects.create(
            title="Printer offline",
            priority="High",
            status="Open",
            reported_by=self.admin,
        )
        self.assertEqual(str(issue), "Printer offline")
        self.assertEqual(issue.priority, "High")
        self.assertEqual(issue.status, "Open")

    def test_issue_default_status_and_priority(self):
        issue = Issue.objects.create(title="Minor Bug", reported_by=self.admin)
        self.assertEqual(issue.status, "Open")
        self.assertEqual(issue.priority, "Medium")

    def test_issue_priority_choices(self):
        for prio in ["Low", "Medium", "High", "Critical"]:
            issue = Issue.objects.create(
                title="Issue " + prio, priority=prio, reported_by=self.admin
            )
            self.assertEqual(issue.priority, prio)

    def test_issue_status_choices(self):
        for st in ["Open", "Monitoring", "Resolved", "Closed"]:
            issue = Issue.objects.create(
                title="Status " + st, status=st, reported_by=self.admin
            )
            self.assertEqual(issue.status, st)

    def test_issue_comment(self):
        issue = Issue.objects.create(title="Comment test", reported_by=self.admin)
        comment = IssueComment.objects.create(
            issue=issue, author=self.admin, body="Investigating now"
        )
        self.assertEqual(comment.issue, issue)
        self.assertIn("Comment on", str(comment))

    def test_issue_has_no_direct_requisition_fk(self):
        field_names = [f.name for f in Issue._meta.get_fields()]
        self.assertNotIn("requisition", field_names)

    def test_issue_has_reverse_requisitions(self):
        issue = Issue.objects.create(title="Reverse link test", reported_by=self.admin)
        self.assertTrue(hasattr(issue, "requisitions"))


# ---- Project Model Tests ----

class ProjectModelTest(TestCase):
    def setUp(self):
        self.admin = make_admin()

    def test_create_project(self):
        project = Project.objects.create(
            title="Network Upgrade",
            priority="High",
            status="Pending",
            reported_by=self.admin,
        )
        self.assertEqual(str(project), "Network Upgrade")
        self.assertEqual(project.status, "Pending")

    def test_project_default_values(self):
        project = Project.objects.create(title="Basic Project", reported_by=self.admin)
        self.assertEqual(project.priority, "Medium")
        self.assertEqual(project.status, "Pending")

    def test_project_has_no_requisitions_m2m(self):
        m2m_fields = [
            f.name for f in Project._meta.get_fields()
            if hasattr(f, "many_to_many") and f.many_to_many and not f.auto_created
        ]
        self.assertNotIn("requisitions", m2m_fields)

    def test_project_has_reverse_requisitions(self):
        project = Project.objects.create(title="Reverse Project", reported_by=self.admin)
        self.assertTrue(hasattr(project, "requisitions"))

    def test_project_comment(self):
        project = Project.objects.create(title="Comment Project", reported_by=self.admin)
        comment = ProjectComment.objects.create(
            project=project, author=self.admin, body="Approved"
        )
        self.assertEqual(comment.project, project)


class ProjectItemModelTest(TestCase):
    def setUp(self):
        self.admin = make_admin()
        self.project = Project.objects.create(
            title="Cost Project", reported_by=self.admin
        )

    def test_create_item(self):
        item = ProjectItem.objects.create(
            project=self.project,
            item_name="Laptop",
            item_type="Asset",
            unit_price=60000,
            quantity=3,
        )
        self.assertEqual(item.total_price, 180000)
        self.assertEqual(str(item), "Laptop x3")

    def test_service_item(self):
        item = ProjectItem.objects.create(
            project=self.project,
            item_name="Cable Installation",
            item_type="Service",
            unit_price=15000,
            quantity=1,
        )
        self.assertEqual(item.item_type, "Service")
        self.assertEqual(item.total_price, 15000)

    def test_multiple_items_sum(self):
        ProjectItem.objects.create(
            project=self.project, item_name="A", item_type="Asset",
            unit_price=10000, quantity=2
        )
        ProjectItem.objects.create(
            project=self.project, item_name="B", item_type="Service",
            unit_price=5000, quantity=1
        )
        total = sum(i.total_price for i in self.project.cost_items.all())
        self.assertEqual(total, 25000)


# ---- View Tests ----

class IssueViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = make_admin()
        self.viewer = make_viewer()
        self.issue = Issue.objects.create(
            title="View Test Issue", priority="High",
            status="Open", reported_by=self.admin
        )

    def test_list_requires_login(self):
        resp = self.client.get(reverse("issues:issue_list"))
        self.assertEqual(resp.status_code, 302)

    def test_list_accessible(self):
        self.client.login(username="iss_admin", password="testpass123")
        resp = self.client.get(reverse("issues:issue_list"))
        self.assertEqual(resp.status_code, 200)

    def test_detail_view(self):
        self.client.login(username="iss_admin", password="testpass123")
        resp = self.client.get(reverse("issues:issue_detail", args=[self.issue.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "View Test Issue")

    def test_viewer_cannot_create_issue(self):
        self.client.login(username="iss_viewer", password="testpass123")
        resp = self.client.get(reverse("issues:issue_create"))
        self.assertEqual(resp.status_code, 302)

    def test_admin_can_create_issue_get(self):
        self.client.login(username="iss_admin", password="testpass123")
        resp = self.client.get(reverse("issues:issue_create"))
        self.assertEqual(resp.status_code, 200)

    def test_search_filter(self):
        self.client.login(username="iss_admin", password="testpass123")
        resp = self.client.get(reverse("issues:issue_list") + "?i_search=View+Test")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "View Test Issue")

    def test_priority_filter(self):
        self.client.login(username="iss_admin", password="testpass123")
        resp = self.client.get(reverse("issues:issue_list") + "?i_priority=High")
        self.assertEqual(resp.status_code, 200)


class ProjectViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = make_admin()
        self.project = Project.objects.create(
            title="Test Project View", priority="Medium",
            status="Pending", reported_by=self.admin
        )

    def test_project_list_accessible(self):
        self.client.login(username="iss_admin", password="testpass123")
        resp = self.client.get(reverse("issues:project_list"))
        self.assertEqual(resp.status_code, 200)

    def test_project_detail(self):
        self.client.login(username="iss_admin", password="testpass123")
        resp = self.client.get(reverse("issues:project_detail", args=[self.project.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Test Project View")

    def test_project_create_get(self):
        self.client.login(username="iss_admin", password="testpass123")
        resp = self.client.get(reverse("issues:project_create"))
        self.assertEqual(resp.status_code, 200)

    def test_category_assets_api(self):
        from assets.models import Category
        cat = Category.objects.get_or_create(name="Switch", defaults={"short_code": "SWT"})[0]
        self.client.login(username="iss_admin", password="testpass123")
        resp = self.client.get(
            reverse("issues:category_assets_api", args=[cat.pk])
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("assets", data)
