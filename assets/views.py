from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone
from .models import Asset, Category, StatusOption, Department, AssignmentHistory
from .utils import export_assets_excel
from users.decorators import role_required


@login_required
def asset_list(request):
    """List all assets with search, filter, and sort"""
    assets = Asset.objects.filter(is_deleted=False).select_related(
        'category', 'status', 'assigned_to', 'department', 'requisition'
    )

    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        assets = assets.filter(
            Q(asset_id__icontains=search_query) |
            Q(serial_number__icontains=search_query) |
            Q(model_description__icontains=search_query) |
            Q(assigned_to__first_name__icontains=search_query) |
            Q(assigned_to__last_name__icontains=search_query) |
            Q(purchased_from__icontains=search_query)
        )

    # Filters
    category_filter = request.GET.get('category')
    if category_filter and category_filter.isdigit():
        assets = assets.filter(category_id=category_filter)

    status_filter = request.GET.get('status')
    if status_filter and status_filter.isdigit():
        assets = assets.filter(status_id=status_filter)

    assigned_filter = request.GET.get('assigned')
    if assigned_filter == 'assigned':
        assets = assets.exclude(assigned_to__isnull=True)
    elif assigned_filter == 'unassigned':
        assets = assets.filter(assigned_to__isnull=True)

    # Sorting
    SORT_MAP = {
        'asset_id': 'asset_id',
        'category': 'category__name',
        'model': 'model_description',
        'cost': 'purchase_cost',
        'date': 'purchase_date',
        'status': 'status__name',
        'vendor': 'purchased_from',
    }
    sort_by = request.GET.get('sort', '')
    sort_dir = request.GET.get('dir', 'asc')
    orm_field = SORT_MAP.get(sort_by, '-created_at')
    if sort_by and sort_dir == 'desc':
        orm_field = f'-{orm_field}'
    assets = assets.order_by(orm_field)

    # Pagination
    paginator = Paginator(assets, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()
    statuses = StatusOption.objects.filter(is_active=True)

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'statuses': statuses,
        'search_query': search_query,
        'category_filter': category_filter,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'sort_dir': sort_dir,
        'assigned_filter': assigned_filter,
    }
    
    return render(request, 'assets/list.html', context)


@login_required
def asset_detail(request, pk):
    """Asset detail view with full history"""
    asset = get_object_or_404(Asset, pk=pk, is_deleted=False)
    
    # Get assignment history
    assignment_history = asset.assignment_history.all().order_by('-start_date')
    
    # Get maintenance logs
    maintenance_logs = asset.maintenance_logs.all().order_by('-timestamp')
    
    # Get activity logs
    activity_logs = asset.activity_logs.all().order_by('-timestamp')[:20]

    # Get linked assets
    linked_assets = asset.get_linked_assets()
    all_assets_for_linking = Asset.objects.filter(is_deleted=False).exclude(pk=pk).order_by('asset_id')
    
    context = {
        'asset': asset,
        'assignment_history': assignment_history,
        'maintenance_logs': maintenance_logs,
        'activity_logs': activity_logs,
        'linked_assets': linked_assets,
        'all_assets_for_linking': all_assets_for_linking,
    }
    
    return render(request, 'assets/detail.html', context)


def _track_assignment_change(asset, old_person_id, old_department_id):
    """
    Helper to create/close AssignmentHistory records when assigned_to changes.
    Called from asset_create and asset_update.
    """
    now = timezone.now()
    new_person_id = asset.assigned_to_id
    new_department_id = asset.department_id

    # If person or department changed, close the old open record(s)
    if old_person_id != new_person_id or old_department_id != new_department_id:
        open_records = AssignmentHistory.objects.filter(
            asset=asset, end_date__isnull=True
        )
        open_records.update(end_date=now)

        # If old person existed, update last_known_person
        if old_person_id and old_person_id != new_person_id:
            from .models import Person
            try:
                old_person = Person.objects.get(pk=old_person_id)
                asset.last_known_person = old_person
                asset.save(update_fields=['last_known_person'])
            except Person.DoesNotExist:
                pass

        # Create new record if there's a new assignment
        if new_person_id or new_department_id:
            AssignmentHistory.objects.create(
                asset=asset,
                person_id=new_person_id,
                department_id=new_department_id,
                start_date=now,
            )


@login_required
@role_required(['super_admin', 'admin'])
def asset_create(request):
    """Create new asset"""
    from .forms import AssetForm
    
    if request.method == 'POST':
        form = AssetForm(request.POST, request.FILES)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.created_by = request.user
            asset.updated_by = request.user
            
            # If asset_id is blank, generate it dynamically here as a fallback
            if not asset.asset_id and asset.category.short_code:
                last_asset = Asset.objects.filter(
                    category=asset.category,
                    asset_id__startswith=f"{asset.category.short_code}-"
                ).order_by('-asset_id').first()
                if last_asset and '-' in last_asset.asset_id:
                    try:
                        last_num = int(last_asset.asset_id.split('-')[1])
                        next_num = last_num + 1
                    except ValueError:
                        next_num = 1
                else:
                    next_num = 1
                asset.asset_id = f"{asset.category.short_code}-{next_num:03d}"
            
            try:
                asset.save()
            except ValidationError as e:
                for field, errs in e.message_dict.items():
                    for err in errs:
                        messages.error(request, err)
                return render(request, 'assets/form.html', {'form': form, 'title': 'Create Asset'})
            
            # Track initial assignment
            _track_assignment_change(asset, None, None)

            messages.success(request, f'Asset {asset.asset_id} created successfully!')
            return redirect('assets:detail', pk=asset.pk)
        else:
            # Display form validation errors clearly
            for field, errors in form.errors.items():
                label = form.fields[field].label if field in form.fields else field
                for error in errors:
                    messages.error(request, f"{label}: {error}" if field != '__all__' else error)
    else:
        form = AssetForm()
    
    return render(request, 'assets/form.html', {'form': form, 'title': 'Create Asset'})


@login_required
@role_required(['super_admin', 'admin'])
def asset_update(request, pk):
    """Update existing asset"""
    from .forms import AssetForm
    asset = get_object_or_404(Asset, pk=pk, is_deleted=False)
    
    if request.method == 'POST':
        # Capture old assignment before saving
        old_person_id = asset.assigned_to_id
        old_department_id = asset.department_id

        form = AssetForm(request.POST, request.FILES, instance=asset)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.updated_by = request.user
            try:
                asset.save()
            except ValidationError as e:
                for field, errs in e.message_dict.items():
                    for err in errs:
                        messages.error(request, err)
                return render(request, 'assets/form.html', {'form': form, 'title': 'Update Asset', 'asset': asset})
            
            # Track assignment change (auto previous owner)
            _track_assignment_change(asset, old_person_id, old_department_id)

            messages.success(request, f'Asset {asset.asset_id} updated successfully!')
            return redirect('assets:detail', pk=asset.pk)
        else:
            # Display form validation errors clearly
            for field, errors in form.errors.items():
                label = form.fields[field].label if field in form.fields else field
                for error in errors:
                    messages.error(request, f"{label}: {error}" if field != '__all__' else error)
    else:
        form = AssetForm(instance=asset)
    
    # Pass assignment history for the "Previous Owners" section
    assignment_history = asset.assignment_history.select_related('person', 'department').order_by('-start_date')
    return render(request, 'assets/form.html', {
        'form': form,
        'title': 'Update Asset',
        'asset': asset,
        'assignment_history': assignment_history,
    })


@login_required
@role_required(['super_admin', 'admin'])
def asset_delete(request, pk):
    """Soft delete asset"""
    asset = get_object_or_404(Asset, pk=pk, is_deleted=False)
    
    if request.method == 'POST':
        asset.is_deleted = True
        asset.updated_by = request.user
        asset.save()
        messages.success(request, f'Asset {asset.asset_id} deleted successfully!')
        return redirect('assets:list')
    
    return render(request, 'assets/delete_confirm.html', {'asset': asset})


@login_required
@role_required(['super_admin', 'admin'])
@require_POST
def delete_assignment_history(request, pk):
    """AJAX endpoint to delete an assignment history record"""
    record = get_object_or_404(AssignmentHistory, pk=pk)
    record.delete()
    return JsonResponse({'success': True})


@login_required
def asset_export_excel(request):
    """Export assets to Excel"""
    assets = Asset.objects.filter(is_deleted=False).select_related('category', 'status', 'assigned_to')
    return export_assets_excel(assets)


@login_required
def get_next_asset_id(request):
    """API endpoint to get the next auto-incremented asset ID for a category"""
    category_id = request.GET.get('category_id')
    if not category_id:
        return JsonResponse({'error': 'No category ID provided'}, status=400)
        
    category = get_object_or_404(Category, id=category_id)
    if not category.short_code:
        return JsonResponse({'asset_id': ''})
        
    last_asset = Asset.objects.filter(
        category=category,
        asset_id__startswith=f"{category.short_code}-"
    ).order_by('-asset_id').first()
    
    if last_asset and '-' in last_asset.asset_id:
        try:
            last_num = int(last_asset.asset_id.split('-')[1])
            next_num = last_num + 1
        except ValueError:
            next_num = 1
    else:
        next_num = 1
        
    next_id = f"{category.short_code}-{next_num:03d}"
    
    return JsonResponse({'asset_id': next_id})


@login_required
@role_required(['super_admin', 'admin'])
@require_POST
def asset_link(request, pk):
    """Link two assets together"""
    from .models import AssetLink
    asset = get_object_or_404(Asset, pk=pk, is_deleted=False)
    linked_asset_id = request.POST.get('linked_asset_id')
    notes = request.POST.get('notes', '')

    if not linked_asset_id:
        messages.error(request, 'Please select an asset to link.')
        return redirect('assets:detail', pk=pk)

    linked_asset = get_object_or_404(Asset, pk=linked_asset_id, is_deleted=False)

    if asset.pk == linked_asset.pk:
        messages.error(request, 'Cannot link an asset to itself.')
        return redirect('assets:detail', pk=pk)

    # Create bidirectional links
    link1, created1 = AssetLink.objects.get_or_create(
        asset=asset, linked_asset=linked_asset,
        defaults={'notes': notes, 'created_by': request.user}
    )
    link2, created2 = AssetLink.objects.get_or_create(
        asset=linked_asset, linked_asset=asset,
        defaults={'notes': notes, 'created_by': request.user}
    )

    if created1 or created2:
        messages.success(request, f'Linked {asset.asset_id} ↔ {linked_asset.asset_id}')
    else:
        messages.info(request, 'These assets are already linked.')

    return redirect('assets:detail', pk=pk)


@login_required
@role_required(['super_admin', 'admin'])
@require_POST
def asset_unlink(request, pk, link_pk):
    """Remove a link between two assets"""
    from .models import AssetLink
    asset = get_object_or_404(Asset, pk=pk, is_deleted=False)
    link = get_object_or_404(AssetLink, pk=link_pk, asset=asset)

    # Remove both directions
    reverse_link = AssetLink.objects.filter(
        asset=link.linked_asset, linked_asset=asset
    )
    reverse_link.delete()
    linked_id = link.linked_asset.asset_id
    link.delete()

    messages.success(request, f'Unlinked {asset.asset_id} ↔ {linked_id}')
    return redirect('assets:detail', pk=pk)
