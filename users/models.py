from django.db import models
from django.contrib.auth.models import User
from assets.models import Department


class UserProfile(models.Model):
    """Extended user profile"""
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        ('technician', 'Technician'),
        ('viewer', 'Viewer'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    employee_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    # Password change tracking
    password_changed_at = models.DateTimeField(null=True, blank=True)
    must_change_password = models.BooleanField(default=False, verbose_name="Must Change Password on Login")
    is_first_login = models.BooleanField(default=True, verbose_name="First Login")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['employee_id']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

    def is_super_admin(self):
        return self.role == 'super_admin'

    def is_admin(self):
        return self.role in ['super_admin', 'admin']

    def can_edit_assets(self):
        return self.role in ['super_admin', 'admin']

    def can_view_maintenance(self):
        return self.role in ['super_admin', 'admin', 'technician']
    
    def needs_password_change(self):
        """Check if user needs to change password"""
        return self.must_change_password or self.is_first_login
