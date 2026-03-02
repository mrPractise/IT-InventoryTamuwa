from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Requisition, RequisitionItem
from .forms import RequisitionForm, RequisitionItemFormSet
from users.decorators import role_required


@login_required
def requisition_list(request):
    qs = Requisition.objects.all().prefetch_related('items')
    status_filter = request.GET.get('status', '')
    if status_filter:
        qs = qs.filter(status=status_filter)

    paginator = Paginator(qs, 20)
    page = request.GET.get('page')
    requisitions = paginator.get_page(page)

    return render(request, 'requisition/list.html', {
        'requisitions': requisitions,
        'status_filter': status_filter,
        'status_choices': Requisition.STATUS_CHOICES,
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
