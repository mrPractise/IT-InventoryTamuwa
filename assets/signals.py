from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Asset, AssignmentHistory, ActivityLog, StatusOption, Person
from django.utils import timezone


@receiver(pre_save, sender=Asset)
def auto_update_status_on_assignment(sender, instance, **kwargs):
    """Auto-update status when assigned_to changes"""
    if instance.pk:  # Existing asset
        try:
            old_instance = Asset.objects.get(pk=instance.pk)

            # Only auto-set to "In Use" if assignment is being NEWLY added
            # (was None/empty before, now has a value). Do NOT override if
            # the user explicitly chose a different status (e.g. Under Maintenance).
            assignment_newly_added = (
                (instance.assigned_to and not old_instance.assigned_to) or
                (instance.department and not old_instance.department)
            )

            if assignment_newly_added and instance.status.name != 'In Use':
                in_use_status = StatusOption.objects.filter(name='In Use').first()
                if in_use_status:
                    instance.status = in_use_status

            # If both assignment and department are being cleared and status is still "In Use"
            if (not instance.assigned_to and not instance.department and
                    (old_instance.assigned_to or old_instance.department) and
                    instance.status.name == 'In Use'):
                available_status = StatusOption.objects.filter(name='Available').first()
                if available_status:
                    instance.status = available_status

            # Update last_known_person when assignment changes
            if instance.assigned_to != old_instance.assigned_to and old_instance.assigned_to:
                instance.last_known_person = old_instance.assigned_to

            # Attach old instance for post_save signals
            instance._old_instance = old_instance

        except Asset.DoesNotExist:
            instance._old_instance = None
    else:  # New asset
        instance._old_instance = None
        # If assigned_to or department is set on creation, set status to "In Use"
        if instance.assigned_to or instance.department:
            in_use_status = StatusOption.objects.filter(name='In Use').first()
            if in_use_status:
                instance.status = in_use_status



@receiver(post_save, sender=Asset)
def handle_assignment_history(sender, instance, created, **kwargs):
    """Create assignment history when assigned_to changes"""
    if created:
        # New asset - create initial assignment if assigned_to or department is set
        if instance.assigned_to or instance.department:
            AssignmentHistory.objects.create(
                asset=instance,
                person=instance.assigned_to,
                department=instance.department,
                start_date=timezone.now()
            )
    else:
        # Existing asset - check if assignment changed
        old_instance = getattr(instance, '_old_instance', None)
        if old_instance:
            old_assigned_to = old_instance.assigned_to
            
            if instance.assigned_to != old_instance.assigned_to or instance.department != old_instance.department:
                # Close previous assignment
                AssignmentHistory.objects.filter(
                    asset=instance,
                    end_date__isnull=True
                ).update(end_date=timezone.now())
                
                # Create new assignment
                if instance.assigned_to or instance.department:
                    AssignmentHistory.objects.create(
                        asset=instance,
                        person=instance.assigned_to,
                        department=instance.department,
                        start_date=timezone.now()
                    )
        # Removed broken try/except that fetched new instance


@receiver(post_save, sender=Asset)
def auto_close_maintenance_logs_on_status_change(sender, instance, created, **kwargs):
    """When asset status changes:
    - TO 'Under Maintenance': auto-create an open log with Investigation action.
    - AWAY FROM 'Under Maintenance': auto-close any open logs.
    """
    # Guard against recursive signal loops from maintenance.signals
    if getattr(instance, '_skip_maintenance_signal', False):
        return

    from maintenance.models import MaintenanceLog, ActionTakenOption

    if not created:
        old_instance = getattr(instance, '_old_instance', None)
        if old_instance:
            old_status = old_instance.status
            new_status = instance.status

            if old_status and new_status and old_status.name != new_status.name:

                # Status changed TO Under Maintenance → auto-create open log
                if new_status.name == 'Under Maintenance':
                    # Only create if no open log already exists
                    if not MaintenanceLog.objects.filter(asset=instance, maintenance_status='Open').exists():
                        investigation = ActionTakenOption.objects.filter(name='Investigation').first()
                        MaintenanceLog.objects.create(
                            asset=instance,
                            date_reported=timezone.now().date(),
                            description=f'Asset {instance.asset_id} status changed to Under Maintenance.',
                            action_taken=investigation,
                            maintenance_status='Open',
                            reported_by=instance.updated_by,
                        )

                # Status changed AWAY FROM Under Maintenance → auto-close open logs
                elif old_status.name == 'Under Maintenance':
                    MaintenanceLog.objects.filter(
                        asset=instance,
                        maintenance_status='Open'
                    ).update(
                        maintenance_status='Closed',
                        date_completed=timezone.now().date(),
                    )
    elif created:
        # New asset created already Under Maintenance
        if instance.status and instance.status.name == 'Under Maintenance':
            from maintenance.models import MaintenanceLog, ActionTakenOption
            investigation = ActionTakenOption.objects.filter(name='Investigation').first()
            MaintenanceLog.objects.create(
                asset=instance,
                date_reported=timezone.now().date(),
                description=f'Asset {instance.asset_id} added under Maintenance.',
                action_taken=investigation,
                maintenance_status='Open',
                reported_by=instance.created_by,
            )


@receiver(post_save, sender=Asset)
def log_activity(sender, instance, created, **kwargs):
    """Create activity log entry for asset changes"""
    action = 'CREATE' if created else 'UPDATE'
    description = f"Asset {instance.asset_id} was {'created' if created else 'updated'}"
    old_value = ''
    new_value = ''

    if not created:
        old_instance = getattr(instance, '_old_instance', None)
        if old_instance:
            changes = []

            if old_instance.assigned_to != instance.assigned_to:
                changes.append(f"Assigned To: {old_instance.assigned_to} -> {instance.assigned_to}")
                action = 'ASSIGN' if instance.assigned_to else 'UNASSIGN'

            if old_instance.department != instance.department:
                changes.append(f"Department: {old_instance.department} -> {instance.department}")
                if action not in ['ASSIGN', 'UNASSIGN']:
                    action = 'ASSIGN' if instance.department else 'UNASSIGN'

            if old_instance.status != instance.status:
                changes.append(f"Status: {old_instance.status} -> {instance.status}")
                action = 'STATUS_CHANGE'
                old_value = old_instance.status.name if old_instance.status else ''
                new_value = instance.status.name if instance.status else ''

            if changes:
                description = f"Asset {instance.asset_id}: " + ", ".join(changes)

    # Note: In a real implementation, you'd get the current user from request
    # For now, we'll use the created_by/updated_by fields
    user = instance.created_by if created else instance.updated_by

    ActivityLog.objects.create(
        asset=instance,
        user=user,
        action=action,
        description=description,
        old_value=old_value,
        new_value=new_value,
    )


@receiver(pre_delete, sender=Person)
def handle_person_deletion(sender, instance, **kwargs):
    """Ensure data consistency when a person is deleted"""
    # Unassign all assets assigned to this person
    Asset.objects.filter(assigned_to=instance).update(assigned_to=None)
    
    # Close any open assignment histories for this person
    AssignmentHistory.objects.filter(
        person=instance,
        end_date__isnull=True
    ).update(end_date=timezone.now())
    
    # Note: We don't delete the assignment history - it remains for audit purposes
    # The person field will be set to NULL due to on_delete=SET_NULL
