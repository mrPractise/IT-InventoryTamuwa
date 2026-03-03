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
