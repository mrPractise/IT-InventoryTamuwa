from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import MaintenanceLog, ActionTakenOption
from assets.models import Asset, Person
from users.decorators import role_required


@login_required
def maintenance_list(request):
    """List all maintenance logs"""
    logs = MaintenanceLog.objects.select_related(
        'asset', 'action_taken', 'reported_by', 'performed_by', 'requisition'
    ).order_by('-timestamp')

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

    performed_by_filter = request.GET.get('performed_by')
    if performed_by_filter:
        logs = logs.filter(performed_by_id=performed_by_filter)

    # Pagination
    paginator = Paginator(logs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    from assets.models import Person  # already imported at top level, keeping for safety
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
        'performed_by_filter': performed_by_filter,
        'all_persons': Person.objects.all().order_by('first_name', 'last_name'),
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

            messages.success(request, f'Maintenance log for {log.asset.asset_id} created successfully!')
            return redirect('maintenance:detail', pk=log.pk)
        else:
            # Display form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label or field}: {error}")
    else:
        # Pre-select asset if passed in URL
        initial = {}
        asset_id = request.GET.get('asset')
        if asset_id:
            initial['asset'] = asset_id
        form = MaintenanceLogForm(initial=initial)

    return render(request, 'maintenance/form.html', {'form': form, 'title': 'Add Maintenance Log'})


@login_required
@role_required(['super_admin', 'admin'])
def maintenance_update(request, pk):
    """Edit an existing maintenance log — Closed logs cannot be edited."""
    from .forms import MaintenanceLogForm
    log = get_object_or_404(MaintenanceLog, pk=pk)

    if log.maintenance_status == 'Closed':
        messages.error(request, 'This maintenance log is Closed and cannot be edited.')
        return redirect('maintenance:detail', pk=log.pk)

    if request.method == 'POST':
        form = MaintenanceLogForm(request.POST, instance=log)
        if form.is_valid():
            updated_log = form.save(commit=False)
            if updated_log.maintenance_status == 'Closed' and not updated_log.completed_by:
                updated_log.completed_by = request.user
            if updated_log.maintenance_status == 'Closed' and not updated_log.date_completed:
                from django.utils import timezone
                updated_log.date_completed = timezone.now().date()
            updated_log.save()
            messages.success(request, f'Maintenance log updated successfully!')
            return redirect('maintenance:detail', pk=log.pk)
        else:
            # Display form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label or field}: {error}")
    else:
        form = MaintenanceLogForm(instance=log)

    return render(request, 'maintenance/form.html', {'form': form, 'title': 'Edit Maintenance Log', 'log': log})

