from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Asset, AssignmentHistory, ActivityLog, StatusOption
from django.utils import timezone


@receiver(pre_save, sender=Asset)
def auto_update_status_on_assignment(sender, instance, **kwargs):
    """Auto-update status when assigned_to changes"""
    if instance.pk:  # Existing asset
        try:
            old_instance = Asset.objects.get(pk=instance.pk)
            old_assigned_to = old_instance.assigned_to
            old_status = old_instance.status
            
            # If assigned_to is being set and status is not "In Use"
            if instance.assigned_to and instance.status.name != 'In Use':
                in_use_status = StatusOption.objects.filter(name='In Use').first()
                if in_use_status:
                    instance.status = in_use_status
            
            # If assigned_to is being cleared and status is "In Use"
            if not instance.assigned_to and old_assigned_to and instance.status.name == 'In Use':
                available_status = StatusOption.objects.filter(name='Available').first()
                if available_status:
                    instance.status = available_status
            
            # Update last_known_user when assignment changes
            if instance.assigned_to != old_assigned_to and old_assigned_to:
                instance.last_known_user = old_assigned_to
                
        except Asset.DoesNotExist:
            pass
    else:  # New asset
        # If assigned_to is set on creation, set status to "In Use"
        if instance.assigned_to:
            in_use_status = StatusOption.objects.filter(name='In Use').first()
            if in_use_status:
                instance.status = in_use_status


@receiver(post_save, sender=Asset)
def handle_assignment_history(sender, instance, created, **kwargs):
    """Create assignment history when assigned_to changes"""
    if created:
        # New asset - create initial assignment if assigned_to is set
        if instance.assigned_to:
            AssignmentHistory.objects.create(
                asset=instance,
                user=instance.assigned_to,
                start_date=timezone.now()
            )
    else:
        # Existing asset - check if assignment changed
        try:
            old_instance = Asset.objects.get(pk=instance.pk)
            old_assigned_to = old_instance.assigned_to
            
            if instance.assigned_to != old_assigned_to:
                # Close previous assignment
                if old_assigned_to:
                    AssignmentHistory.objects.filter(
                        asset=instance,
                        user=old_assigned_to,
                        end_date__isnull=True
                    ).update(end_date=timezone.now())
                
                # Create new assignment
                if instance.assigned_to:
                    # Check if there's already an open assignment for this user
                    existing = AssignmentHistory.objects.filter(
                        asset=instance,
                        user=instance.assigned_to,
                        end_date__isnull=True
                    ).first()
                    
                    if not existing:
                        AssignmentHistory.objects.create(
                            asset=instance,
                            user=instance.assigned_to,
                            start_date=timezone.now()
                        )
        except Asset.DoesNotExist:
            pass


@receiver(post_save, sender=Asset)
def create_maintenance_log_on_status_change(sender, instance, created, **kwargs):
    """Auto-create maintenance log when status changes to 'Under Maintenance'"""
    if not created:
        try:
            old_instance = Asset.objects.get(pk=instance.pk)
            old_status = old_instance.status
            
            if instance.status.name == 'Under Maintenance' and old_status.name != 'Under Maintenance':
                from maintenance.models import MaintenanceLog
                
                MaintenanceLog.objects.create(
                    asset=instance,
                    date_reported=timezone.now().date(),
                    maintenance_status='Open',
                    description=f"Asset automatically moved to maintenance. Previous status: {old_status.name}",
                    previous_assigned_user=instance.last_known_user
                )
        except Asset.DoesNotExist:
            pass


@receiver(post_save, sender=Asset)
def log_activity(sender, instance, created, **kwargs):
    """Create activity log entry for asset changes"""
    action = 'CREATE' if created else 'UPDATE'
    description = f"Asset {instance.asset_id} was {'created' if created else 'updated'}"
    
    if not created:
        try:
            old_instance = Asset.objects.get(pk=instance.pk)
            changes = []
            
            if old_instance.assigned_to != instance.assigned_to:
                changes.append(f"Assigned To: {old_instance.assigned_to} -> {instance.assigned_to}")
                action = 'ASSIGN' if instance.assigned_to else 'UNASSIGN'
            
            if old_instance.status != instance.status:
                changes.append(f"Status: {old_instance.status} -> {instance.status}")
                action = 'STATUS_CHANGE'
            
            if changes:
                description = f"Asset {instance.asset_id}: " + ", ".join(changes)
        except Asset.DoesNotExist:
            pass
    
    # Note: In a real implementation, you'd get the current user from request
    # For now, we'll use the created_by/updated_by fields
    user = instance.created_by if created else instance.updated_by
    
    ActivityLog.objects.create(
        asset=instance,
        user=user,
        action=action,
        description=description
    )
