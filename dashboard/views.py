from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from assets.models import Asset, Category, StatusOption
from maintenance.models import MaintenanceLog
from requisition.models import Requisition, RequisitionItem


@login_required
def dashboard_home(request):
    """Main dashboard view with analytics"""
    # Get all assets (excluding soft-deleted)
    assets = Asset.objects.filter(is_deleted=False)
    
    # Status counts
    status_counts = {}
    status_options = StatusOption.objects.filter(is_active=True)
    for status in status_options:
        status_counts[status.name] = assets.filter(status=status).count()
    
    # Total assets
    total_assets = assets.count()
    
    # Assets added this month
    this_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    assets_this_month = assets.filter(created_at__gte=this_month_start).count()
    
    # Assets under maintenance today
    maintenance_today = MaintenanceLog.objects.filter(
        maintenance_status='Open',
        date_reported=timezone.now().date()
    ).count()
    
    # Total items bought (from requisitions with Bought status)
    total_items_bought = RequisitionItem.objects.filter(
        requisition__status='Bought',
        is_approved=True
    ).count()
    
    # Total value of items bought
    total_value_bought = sum(
        item.total_price for item in RequisitionItem.objects.filter(
            requisition__status='Bought',
            is_approved=True
        )
    )
    
    # Category distribution
    category_distribution = Category.objects.annotate(
        asset_count=Count('assets', filter=Q(assets__is_deleted=False))
    ).values('name', 'asset_count')
    
    # Recent activity (last 10 activities)
    from assets.models import ActivityLog
    recent_activities = ActivityLog.objects.select_related('asset', 'user').order_by('-timestamp')[:10]
    
    # Assets by category
    category_data = list(category_distribution)
    
    # Prepare chart data
    status_labels = list(status_counts.keys())
    status_values = list(status_counts.values())
    category_labels = [c['name'] for c in category_data]
    category_values = [c['asset_count'] for c in category_data]
    
    # Convert to JSON-safe format
    import json
    status_labels_json = json.dumps(status_labels)
    status_values_json = json.dumps(status_values)
    category_labels_json = json.dumps(category_labels)
    category_values_json = json.dumps(category_values)
    
    context = {
        'total_assets': total_assets,
        'status_counts': status_counts,
        'status_in_use': status_counts.get('In Use', 0),
        'status_available': status_counts.get('Available', 0),
        'status_maintenance': status_counts.get('Under Maintenance', 0),
        'status_missing': status_counts.get('Missing', 0),
        'status_retired': status_counts.get('Retired', 0),
        'status_labels': status_labels_json,
        'status_values': status_values_json,
        'assets_this_month': assets_this_month,
        'maintenance_today': maintenance_today,
        'total_items_bought': total_items_bought,
        'total_value_bought': total_value_bought,
        'category_data': category_data,
        'category_labels': category_labels_json,
        'category_values': category_values_json,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'dashboard/home.html', context)


@login_required
def notifications_view(request):
    """Notifications hub — aggregates important system alerts from all apps."""
    from issues.models import Issue, Project
    from assets.models import Asset, ActivityLog
    import json

    now = timezone.now()
    today = now.date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    notifications = []

    # ── 1. Critical / High Issues that are still Open or Monitoring ──
    critical_issues = Issue.objects.filter(
        priority__in=['Critical', 'High'],
        status__in=['Open', 'Monitoring']
    ).order_by('-created_at')
    for issue in critical_issues:
        age_days = (today - issue.created_at.date()).days
        level = 'danger' if issue.priority == 'Critical' else 'warning'
        notifications.append({
            'level': level,
            'icon': 'bi-bug-fill',
            'title': f"{issue.priority} Issue: {issue.title}",
            'message': f"Status: {issue.status} · Open for {age_days} day{'s' if age_days != 1 else ''}",
            'link': f"/issues/issues/{issue.pk}/",
            'link_label': 'View Issue',
            'category': 'Issues',
            'timestamp': issue.created_at,
        })

    # ── 2. Requisitions that have been Pending for > 7 days ──
    stale_reqs = Requisition.objects.filter(
        status='Pending',
        created_at__date__lte=week_ago
    ).order_by('created_at')
    for req in stale_reqs:
        age_days = (today - req.created_at.date()).days
        notifications.append({
            'level': 'warning',
            'icon': 'bi-receipt',
            'title': f"Stale Requisition: {req.req_no} — {req.title}",
            'message': f"Pending for {age_days} days · Company: {req.company}",
            'link': f"/requisition/{req.pk}/",
            'link_label': 'View Requisition',
            'category': 'Requisitions',
            'timestamp': req.created_at,
        })

    # ── 3. Approved Requisitions with unprocessed items ──
    bought_reqs_with_unprocessed = Requisition.objects.filter(
        status='Bought'
    ).prefetch_related('items')
    for req in bought_reqs_with_unprocessed:
        unprocessed = [i for i in req.items.all() if i.is_approved and not i.is_processed]
        if unprocessed:
            notifications.append({
                'level': 'info',
                'icon': 'bi-cart-check',
                'title': f"Bought Req has unprocessed items: {req.req_no}",
                'message': f"{len(unprocessed)} item(s) not yet added to assets · {req.title}",
                'link': f"/requisition/{req.pk}/",
                'link_label': 'View Requisition',
                'category': 'Requisitions',
                'timestamp': req.updated_at,
            })

    # ── 4. Assets under maintenance for > 14 days (open logs) ──
    long_maintenance = MaintenanceLog.objects.filter(
        maintenance_status='Open',
        date_reported__lte=today - timedelta(days=14)
    ).select_related('asset').order_by('date_reported')
    for log in long_maintenance:
        age_days = (today - log.date_reported).days
        notifications.append({
            'level': 'warning',
            'icon': 'bi-tools',
            'title': f"Long maintenance: {log.asset.asset_id} — {log.asset.model_description}",
            'message': f"Under maintenance for {age_days} days · Reported: {log.date_reported.strftime('%d %b %Y')}",
            'link': f"/maintenance/{log.pk}/",
            'link_label': 'View Log',
            'category': 'Maintenance',
            'timestamp': log.timestamp,
        })

    # ── 5. Missing assets ──
    missing_assets = Asset.objects.filter(
        is_deleted=False,
        status__name='Missing'
    ).select_related('status', 'category').order_by('-updated_at')
    for asset in missing_assets:
        notifications.append({
            'level': 'danger',
            'icon': 'bi-question-circle-fill',
            'title': f"Missing Asset: {asset.asset_id} — {asset.model_description}",
            'message': f"Category: {asset.category.name if asset.category else 'N/A'}",
            'link': f"/assets/{asset.pk}/",
            'link_label': 'View Asset',
            'category': 'Assets',
            'timestamp': asset.updated_at,
        })

    # ── 6. Projects pending for > 30 days ──
    stale_projects = Project.objects.filter(
        status='Pending',
        created_at__date__lte=month_ago
    ).order_by('created_at')
    for proj in stale_projects:
        age_days = (today - proj.created_at.date()).days
        notifications.append({
            'level': 'info',
            'icon': 'bi-kanban',
            'title': f"Stale Project: {proj.title}",
            'message': f"Pending for {age_days} days · Priority: {proj.priority}",
            'link': f"/issues/projects/{proj.pk}/",
            'link_label': 'View Project',
            'category': 'Projects',
            'timestamp': proj.created_at,
        })

    # Sort by level severity first (danger > warning > info), then by timestamp desc
    level_order = {'danger': 0, 'warning': 1, 'info': 2}
    notifications.sort(key=lambda n: (level_order.get(n['level'], 3), -(n['timestamp'].timestamp() if n['timestamp'] else 0)))

    # Counts per category
    counts = {
        'total': len(notifications),
        'danger': sum(1 for n in notifications if n['level'] == 'danger'),
        'warning': sum(1 for n in notifications if n['level'] == 'warning'),
        'info': sum(1 for n in notifications if n['level'] == 'info'),
    }

    context = {
        'notifications': notifications,
        'counts': counts,
    }
    return render(request, 'dashboard/notifications.html', context)
