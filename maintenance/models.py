from django.db import models
from django.contrib.auth.models import User
from assets.models import Asset, Person


class ActionTakenOption(models.Model):
    """Dynamic action taken options for maintenance"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name', 'is_active']),
        ]

    def __str__(self):
        return self.name


class MaintenanceLog(models.Model):
    """Maintenance log entries"""
    MAINTENANCE_STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Closed', 'Closed'),
    ]

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='maintenance_logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    date_reported = models.DateField()
    date_completed = models.DateField(null=True, blank=True)
    description = models.TextField(verbose_name="Description of Issue")
    action_taken = models.ForeignKey(
        ActionTakenOption,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='maintenance_logs'
    )
    cost_of_repair = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    maintenance_status = models.CharField(max_length=10, choices=MAINTENANCE_STATUS_CHOICES, default='Open')
    previous_assigned_person = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenance_logs'
    )
    reported_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reported_maintenance'
    )
    completed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_maintenance'
    )
    notes = models.TextField(blank=True)
    requisition = models.ForeignKey(
        'requisition.Requisition',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenance_logs',
        verbose_name="Requisition No."
    )
    # New field linking to Technician model
    performed_by = models.ForeignKey(
        'technicians.Technician',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenance_logs',
        verbose_name="Performed By"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['asset', 'timestamp']),
            models.Index(fields=['maintenance_status']),
            models.Index(fields=['date_reported']),
        ]

    def __str__(self):
        return f"Maintenance for {self.asset.asset_id} - {self.maintenance_status}"
