from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from .models import Asset, Category, StatusOption, Department
from .utils import export_assets_excel, export_assets_pdf
from users.decorators import role_required


@login_required
def asset_list(request):
    """List all assets with search and filter"""
    assets = Asset.objects.filter(is_deleted=False).select_related(
        'category', 'status', 'assigned_to', 'department'
    )
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        assets = assets.filter(
            Q(asset_id__icontains=search_query) |
            Q(serial_number__icontains=search_query) |
            Q(model_description__icontains=search_query) |
            Q(assigned_to__username__icontains=search_query)
        )
    
    # Filters
    category_filter = request.GET.get('category')
    if category_filter:
        assets = assets.filter(category_id=category_filter)
    
    status_filter = request.GET.get('status')
    if status_filter:
        assets = assets.filter(status_id=status_filter)
    
    assigned_filter = request.GET.get('assigned')
    if assigned_filter == 'assigned':
        assets = assets.exclude(assigned_to__isnull=True)
    elif assigned_filter == 'unassigned':
        assets = assets.filter(assigned_to__isnull=True)
    
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
    
    context = {
        'asset': asset,
        'assignment_history': assignment_history,
        'maintenance_logs': maintenance_logs,
        'activity_logs': activity_logs,
    }
    
    return render(request, 'assets/detail.html', context)


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
            
            asset.save()
            
            messages.success(request, f'Asset {asset.asset_id} created successfully!')
            return redirect('assets:detail', pk=asset.pk)
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
        form = AssetForm(request.POST, request.FILES, instance=asset)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.updated_by = request.user
            asset.save()
            
            messages.success(request, f'Asset {asset.asset_id} updated successfully!')
            return redirect('assets:detail', pk=asset.pk)
    else:
        form = AssetForm(instance=asset)
    
    return render(request, 'assets/form.html', {'form': form, 'title': 'Update Asset', 'asset': asset})


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
def asset_export_excel(request):
    """Export assets to Excel"""
    assets = Asset.objects.filter(is_deleted=False).select_related('category', 'status', 'assigned_to')
    return export_assets_excel(assets)


@login_required
def asset_export_pdf(request):
    """Export assets to PDF"""
    assets = Asset.objects.filter(is_deleted=False).select_related('category', 'status', 'assigned_to')
    return export_assets_pdf(assets)

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
