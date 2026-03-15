"""
Context processors for the dashboard app.
Injects notification counts into every template context.
"""
from django.utils import timezone
from datetime import timedelta


def notifications_count(request):
    """
    Injects `unread_notifications_count` into every template.
    Counts: critical/high open issues + stale pending reqs + missing assets + open long-maintenance.
    Kept lightweight — no heavy queries.
    """
    if not request.user.is_authenticated:
        return {'unread_notifications_count': 0}

    try:
        from issues.models import Issue
        from requisition.models import Requisition
        from assets.models import Asset
        from maintenance.models import MaintenanceLog
        from tasks.models import Task

        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        fourteen_ago = today - timedelta(days=14)

        count = 0

        # Critical/High open issues
        count += Issue.objects.filter(
            priority__in=['Critical', 'High'],
            status__in=['Open', 'Monitoring']
        ).count()

        # Stale pending requisitions (> 7 days)
        count += Requisition.objects.filter(
            status='Pending',
            created_at__date__lte=week_ago
        ).count()

        # Missing assets
        count += Asset.objects.filter(
            is_deleted=False,
            status__name='Missing'
        ).count()

        # Open maintenance logs older than 14 days
        count += MaintenanceLog.objects.filter(
            maintenance_status='Open',
            date_reported__lte=fourteen_ago
        ).count()

        # Overdue tasks
        count += Task.objects.filter(
            status__in=['To Do', 'In Progress'],
            due_date__lt=timezone.now()
        ).count()

    except Exception:
        count = 0

    return {'unread_notifications_count': count}
