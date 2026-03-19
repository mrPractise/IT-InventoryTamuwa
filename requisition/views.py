from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from .models import Requisition, RequisitionItem
from .forms import RequisitionForm, RequisitionItemFormSet
from users.decorators import role_required


@login_required
def requisition_list(request):
    qs = Requisition.objects.all().prefetch_related('items')
    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    sort_dir = request.GET.get('dir', 'desc')
    SORT_MAP = {
        'req_no': 'req_no',
        'title': 'title',
        'status': 'status',
        'total': 'total_amount',
        'created_by': 'created_by__username',
        'date': 'created_at',
    }
    orm_field = SORT_MAP.get(sort_by, '-created_at')
    if sort_by and sort_dir == 'desc':
        orm_field = f'-{orm_field}'
    qs = qs.order_by(orm_field)

    paginator = Paginator(qs, 20)
    page = request.GET.get('page')
    requisitions = paginator.get_page(page)

    return render(request, 'requisition/list.html', {
        'requisitions': requisitions,
        'status_filter': status_filter,
        'status_choices': Requisition.STATUS_CHOICES,
        'sort_by': sort_by,
        'sort_dir': sort_dir,
    })


@login_required
def requisition_detail(request, pk):
    req = get_object_or_404(Requisition, pk=pk)
    return render(request, 'requisition/detail.html', {'req': req})


@login_required
@role_required(['super_admin', 'admin'])
def requisition_create(request):
    if request.method == 'POST':
        form = RequisitionForm(request.POST)
        formset = RequisitionItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            req = form.save(commit=False)
            req.created_by = request.user
            req.save()
            formset.instance = req
            formset.save()
            messages.success(request, f'Requisition {req.req_no} created successfully!')
            return redirect('requisition:detail', pk=req.pk)
        else:
            # Display form validation errors
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{form.fields[field].label or field}: {error}")
            if formset.errors:
                messages.error(request, "Please check the items for errors.")
    else:
        form = RequisitionForm()
        formset = RequisitionItemFormSet()

    return render(request, 'requisition/form.html', {
        'form': form,
        'formset': formset,
        'title': 'New Requisition',
    })


@login_required
@role_required(['super_admin', 'admin'])
def requisition_update(request, pk):
    req = get_object_or_404(Requisition, pk=pk)

    # Bought: completely locked from frontend - Django admin only
    if req.status == 'Bought':
        messages.error(
            request,
            f'Requisition {req.req_no} has been marked as Bought and is locked. '
            'Changes can only be made from the Admin panel.'
        )
        return redirect('requisition:detail', pk=req.pk)

    if request.method == 'POST':
        form = RequisitionForm(request.POST, instance=req)
        formset = RequisitionItemFormSet(request.POST, instance=req)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f'Requisition {req.req_no} updated successfully!')
            return redirect('requisition:detail', pk=req.pk)
        else:
            # Display form validation errors
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{form.fields[field].label or field}: {error}")
            if formset.errors:
                messages.error(request, "Please check the items for errors.")
    else:
        form = RequisitionForm(instance=req)
        formset = RequisitionItemFormSet(instance=req)

    return render(request, 'requisition/form.html', {
        'form': form,
        'formset': formset,
        'req': req,
        'title': f'Edit {req.req_no}',
    })


@login_required
def unapproved_items(request):
    """List all requisition items that are not approved, with reasons."""
    items = (
        RequisitionItem.objects
        .filter(is_approved=False)
        .select_related('requisition')
        .order_by('-requisition__created_at', 'item_name')
    )
    return render(request, 'requisition/unapproved_items.html', {
        'items': items,
    })


@login_required
def bought_items_queue(request):
    """List all requisition ASSET items with Bought status that haven't been added to assets yet."""
    from assets.models import Asset
    
    # Get all bought ASSET items (not services) that are not yet processed
    bought_items = (
        RequisitionItem.objects
        .filter(
            requisition__status='Bought', 
            is_approved=True,
            item_type='Asset',  # Only Asset items, not Services
            is_processed=False  # Not yet added to assets
        )
        .select_related('requisition')
        .order_by('-requisition__created_at', 'item_name')
    )
    
    # Get all assets for the "Same as" dropdown
    from assets.models import Asset
    all_assets = Asset.objects.filter(is_deleted=False).select_related('category', 'status').order_by('asset_id')
    
    return render(request, 'requisition/bought_items_queue.html', {
        'items': bought_items,
        'total_count': bought_items.count(),
        'all_assets': all_assets,
    })


@login_required
@role_required(['super_admin', 'admin'])
@require_POST
def mark_item_processed(request, item_pk):
    """Mark a requisition item as processed (linked to existing asset)."""
    item = get_object_or_404(RequisitionItem, pk=item_pk)
    asset_id = request.POST.get('asset_id')
    
    if asset_id:
        from assets.models import Asset
        asset = get_object_or_404(Asset, pk=asset_id, is_deleted=False)
        item.is_processed = True
        item.save()
        messages.success(request, f"Item '{item.item_name}' linked to existing asset {asset.asset_id}.")
    else:
        messages.error(request, "Please select an asset to link.")
        return redirect('requisition:bought_items_queue')
    
    return redirect('requisition:bought_items_queue')
