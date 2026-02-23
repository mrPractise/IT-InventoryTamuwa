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


@login_required
@role_required(['super_admin', 'admin'])
def maintenance_create(request):
    """Create new maintenance log from frontend"""
    from .forms import MaintenanceLogForm
    
    if request.method == 'POST':
        form = MaintenanceLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.reported_by = request.user
            if log.maintenance_status == 'Closed':
                log.completed_by = request.user
            log.save()
            
            # If status of maintenance is Open, we might want to update Asset status to 'Under Maintenance'
            # (Signal already creates a maintenance log when asset status changes to Under Maintenance, 
            # here we're doing the reverse, creating a maintenance log and updating the asset)
            if log.maintenance_status == 'Open' and log.asset.status.name != 'Under Maintenance':
                from assets.models import StatusOption
                maintenance_status_opt = StatusOption.objects.filter(name='Under Maintenance').first()
                if maintenance_status_opt:
                    # Update status without triggering signal (or let signal trigger but it might cause loop depending on implementation)
                    # We can let it be or just update it
                    asset = log.asset
                    asset.status = maintenance_status_opt
                    asset.save(update_fields=['status'])
            
            messages.success(request, f'Maintenance log for {log.asset.asset_id} created successfully!')
            return redirect('maintenance:detail', pk=log.pk)
    else:
        # Pre-select asset if passed in URL
        initial = {}
        asset_id = request.GET.get('asset')
        if asset_id:
            initial['asset'] = asset_id
        form = MaintenanceLogForm(initial=initial)
    
    return render(request, 'maintenance/form.html', {'form': form, 'title': 'Add Maintenance Log'})
