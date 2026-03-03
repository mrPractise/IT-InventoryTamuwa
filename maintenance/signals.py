from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MaintenanceLog
from assets.models import Asset, StatusOption, ActivityLog


@receiver(post_save, sender=MaintenanceLog)
def update_asset_status_on_maintenance(sender, instance, created, **kwargs):
    """Update asset status when maintenance is created or completed"""
    
    if created:
        # When maintenance is created, set asset to Under Maintenance
        under_maintenance_status = StatusOption.objects.filter(name='Under Maintenance').first()
        if under_maintenance_status and instance.asset:
            old_status = instance.asset.status.name if instance.asset.status else None
            instance.asset.status = under_maintenance_status
            instance.asset.save()
            
            # Log the activity
            ActivityLog.objects.create(
                asset=instance.asset,
                user=instance.reported_by,
                action='STATUS_CHANGE',
                description=f"Asset status changed from {old_status} to Under Maintenance (maintenance log created)"
            )
    
    elif instance.maintenance_status == 'Closed':
        # When maintenance is closed, set asset back to Available
        available_status = StatusOption.objects.filter(name='Available').first()
        if available_status and instance.asset and instance.asset.status.name == 'Under Maintenance':
            instance.asset.status = available_status
            instance.asset.save()
            
            # Log the activity
            ActivityLog.objects.create(
                asset=instance.asset,
                user=instance.completed_by,
                action='STATUS_CHANGE',
                description=f"Asset status changed to Available after maintenance completion"
            )
