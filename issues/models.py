from django.db import models
from django.contrib.auth.models import User
from assets.models import Asset, Department, Category
from django.utils import timezone


class Issue(models.Model):
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Monitoring', 'Monitoring'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')

    # Optional asset / department context
    asset = models.ForeignKey(
        Asset, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='issues', limit_choices_to={'is_deleted': False}
    )
    department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='issues'
    )

    reported_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='reported_issues'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class IssueComment(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment on '{self.issue.title}' by {self.author}"


class Project(models.Model):
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Done', 'Done'),
        ('Rejected', 'Rejected'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    date = models.DateField(null=True, blank=True, help_text='Project start or target date')
    problem_statement = models.TextField(blank=True)
    cost_breakdown = models.TextField(
        blank=True,
        help_text='e.g. "Monitors x5 @ KES 20,000 = KES 100,000"'
    )
    conclusion = models.TextField(blank=True)

    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Medium')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    pending_reason = models.TextField(blank=True, help_text='Required when status is Pending')
    rejected_reason = models.TextField(blank=True, help_text='Required when status is Rejected')

    # Asset category links — shows available count per category
    categories = models.ManyToManyField(
        Category, blank=True,
        related_name='projects',
        help_text='Link asset categories to show available quantities'
    )

    reported_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='reported_projects'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def category_asset_counts(self):
        """Returns list of (category, available_count) for each linked category."""
        result = []
        for cat in self.categories.all():
            available = Asset.objects.filter(
                category=cat,
                is_deleted=False,
                status__name='Available'
            ).count()
            result.append((cat, available))
        return result


class ProjectItem(models.Model):
    """Individual cost line items for a project (replaces free-text cost_breakdown)"""
    ITEM_TYPE_CHOICES = [
        ('Asset', 'Asset'),
        ('Service', 'Service'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='cost_items')
    item_type = models.CharField(max_length=10, choices=ITEM_TYPE_CHOICES, default='Asset')
    item_name = models.CharField(max_length=200, verbose_name='Item / Service')
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.item_name} x{self.quantity}"

    @property
    def total_price(self):
        return self.unit_price * self.quantity


class ProjectComment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment on '{self.project.title}' by {self.author}"
