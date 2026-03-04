from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import MaintenanceLog
from assets.models import Asset, StatusOption, ActivityLog


@receiver(pre_save, sender=MaintenanceLog)
def track_old_maintenance_status(sender, instance, **kwargs):
    """Store old maintenance_status for comparison in post_save"""
    if instance.pk:
        try:
            instance._old_maintenance_status = MaintenanceLog.objects.get(pk=instance.pk).maintenance_status
        except MaintenanceLog.DoesNotExist:
            instance._old_maintenance_status = None
    else:
        instance._old_maintenance_status = None


@receiver(post_save, sender=MaintenanceLog)
def update_asset_status_on_maintenance(sender, instance, created, **kwargs):
    """Update asset status when maintenance log is created or closed.
    Uses _skip_signal flag to avoid loops with assets.signals."""

    if not instance.asset:
        return

    # Guard against recursive signal loops
    if getattr(instance.asset, '_skip_maintenance_signal', False):
        return

    if created:
        # New log created → set asset to Under Maintenance (if not already)
        under_maintenance_status = StatusOption.objects.filter(name='Under Maintenance').first()
        if under_maintenance_status and instance.asset.status != under_maintenance_status:
            old_status_name = instance.asset.status.name if instance.asset.status else 'Unknown'
            instance.asset._skip_maintenance_signal = True
            instance.asset.status = under_maintenance_status
            instance.asset.save(update_fields=['status', 'updated_at'])
            instance.asset._skip_maintenance_signal = False
            ActivityLog.objects.create(
                asset=instance.asset,
                user=instance.reported_by,
                action='STATUS_CHANGE',
                description=f'Asset status changed from {old_status_name} to Under Maintenance (maintenance log created)'
            )

    else:
        old_status = getattr(instance, '_old_maintenance_status', None)
        # Log just closed (was Open, now Closed)
        if old_status == 'Open' and instance.maintenance_status == 'Closed':
            # Only reset asset to Investigation if it was Under Maintenance
            if instance.asset.status and instance.asset.status.name == 'Under Maintenance':
                # Check if any other open logs still exist for this asset
                other_open = MaintenanceLog.objects.filter(
                    asset=instance.asset, maintenance_status='Open'
                ).exclude(pk=instance.pk).exists()

                if not other_open:
                    # Default back to Available
                    available_status = StatusOption.objects.filter(name='Available').first()
                    if available_status:
                        instance.asset._skip_maintenance_signal = True
                        instance.asset.status = available_status
                        instance.asset.save(update_fields=['status', 'updated_at'])
                        instance.asset._skip_maintenance_signal = False
                        ActivityLog.objects.create(
                            asset=instance.asset,
                            user=instance.completed_by,
                            action='STATUS_CHANGE',
                            description='Asset status changed to Available after maintenance completion'
                        )
