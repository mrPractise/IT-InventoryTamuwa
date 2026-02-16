from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import MaintenanceLog, ActionTakenOption
from assets.models import Asset
from users.decorators import role_required


@login_required
def maintenance_list(request):
    """List all maintenance logs"""
    logs = MaintenanceLog.objects.select_related('asset', 'action_taken', 'reported_by').order_by('-timestamp')
    
    # Filters
    status_filter = request.GET.get('status')
    if status_filter:
        logs = logs.filter(maintenance_status=status_filter)
    
    search_query = request.GET.get('search', '')
    if search_query:
        logs = logs.filter(
            Q(asset__asset_id__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(logs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'maintenance/list.html', context)


@login_required
def maintenance_detail(request, pk):
    """Maintenance log detail"""
    log = get_object_or_404(MaintenanceLog, pk=pk)
    return render(request, 'maintenance/detail.html', {'log': log})
