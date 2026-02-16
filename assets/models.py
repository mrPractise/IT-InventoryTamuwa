from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


class Department(models.Model):
    """Department model for organizing users"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name


class Category(models.Model):
    """Dynamic category management"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name


class StatusOption(models.Model):
    """Dynamic status options"""
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#6c757d', help_text="Hex color code")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name', 'is_active']),
        ]

    def __str__(self):
        return self.name


class Asset(models.Model):
    """Core Asset model"""
    asset_id = models.CharField(max_length=50, unique=True, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='assets')
    model_description = models.CharField(max_length=200, verbose_name="Model / Description")
    serial_number = models.CharField(max_length=100, db_index=True)
    purchase_date = models.DateField(null=True, blank=True)
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_assets',
        verbose_name="Assigned To"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assets'
    )
    last_known_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='last_known_assets'
    )
    status = models.ForeignKey(StatusOption, on_delete=models.PROTECT, related_name='assets')
    admin_comments = models.TextField(blank=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    is_deleted = models.BooleanField(default=False, db_index=True)  # Soft delete
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_assets')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_assets')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['asset_id']),
            models.Index(fields=['serial_number']),
            models.Index(fields=['status']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['is_deleted']),
            models.Index(fields=['category', 'serial_number']),  # For unique constraint
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['category', 'serial_number'],
                condition=models.Q(is_deleted=False),
                name='unique_serial_per_category'
            )
        ]

    def clean(self):
        """Validate business rules"""
        if self.assigned_to and self.status.name != 'In Use':
            # Status will be auto-updated by signal, but validate here too
            pass
        
        if not self.assigned_to and self.status.name == 'In Use':
            raise ValidationError("Cannot set status to 'In Use' without assigning to a user.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.asset_id} - {self.model_description}"


class AssignmentHistory(models.Model):
    """Track asset assignment history"""
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='assignment_history')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assignment_history')
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name_plural = "Assignment Histories"
        indexes = [
            models.Index(fields=['asset', 'start_date']),
            models.Index(fields=['user', 'start_date']),
        ]

    def __str__(self):
        return f"{self.asset.asset_id} -> {self.user.username if self.user else 'Unassigned'}"


class ActivityLog(models.Model):
    """Audit log for all critical changes"""
    ACTION_CHOICES = [
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
        ('ASSIGN', 'Assigned'),
        ('UNASSIGN', 'Unassigned'),
        ('STATUS_CHANGE', 'Status Changed'),
        ('MAINTENANCE', 'Maintenance'),
    ]

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='activity_logs', null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['asset', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.action} - {self.asset.asset_id if self.asset else 'N/A'} - {self.timestamp}"
