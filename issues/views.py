from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from .models import Issue, IssueComment, Project, ProjectComment, ProjectItem
from .forms import IssueForm, ProjectForm, CommentForm
from users.decorators import role_required
from assets.models import Category, Asset


def _is_admin(user):
    return user.is_superuser or getattr(getattr(user, 'profile', None), 'role', '') in ('super_admin', 'admin')


@login_required
def issue_list(request):
    """View to list all Issues with filtering and pagination."""
    search = request.GET.get('i_search', '')
    priority = request.GET.get('i_priority', '')
    status = request.GET.get('i_status', '')

    issues_qs = Issue.objects.select_related('asset', 'department', 'reported_by')
    if search:
        issues_qs = issues_qs.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )
    if priority:
        issues_qs = issues_qs.filter(priority=priority)
    if status:
        issues_qs = issues_qs.filter(status=status)

    paginator = Paginator(issues_qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    issue_priority_choices = [(val, label, val == priority) for val, label in Issue.PRIORITY_CHOICES]
    issue_status_choices = [(val, label, val == status) for val, label in Issue.STATUS_CHOICES]

    return render(request, 'issues/issue_list.html', {
        'issues_page': page_obj,
        'issues_count': Issue.objects.exclude(status='Closed').count(),
        'i_search': search,
        'i_priority': priority,
        'i_status': status,
        'issue_priority_choices': issue_priority_choices,
        'issue_status_choices': issue_status_choices,
    })


@login_required
def project_list(request):
    """View to list all Projects with filtering and pagination."""
    search = request.GET.get('p_search', '')
    priority = request.GET.get('p_priority', '')
    status = request.GET.get('p_status', '')

    projects_qs = Project.objects.prefetch_related('categories', 'requisitions').select_related('reported_by')
    if search:
        projects_qs = projects_qs.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )
    if priority:
        projects_qs = projects_qs.filter(priority=priority)
    if status:
        projects_qs = projects_qs.filter(status=status)

    paginator = Paginator(projects_qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    project_priority_choices = [(val, label, val == priority) for val, label in Project.PRIORITY_CHOICES]
    project_status_choices = [(val, label, val == status) for val, label in Project.STATUS_CHOICES]

    return render(request, 'issues/project_list.html', {
        'projects_page': page_obj,
        'projects_count': Project.objects.exclude(status='Done').count(),
        'p_search': search,
        'p_priority': priority,
        'p_status': status,
        'project_priority_choices': project_priority_choices,
        'project_status_choices': project_status_choices,
    })


# ─── Issues ──────────────────────────────────────────────────────────────────

@login_required
def issue_detail(request, pk):
    issue = get_object_or_404(Issue, pk=pk)
    comments = issue.comments.select_related('author')
    comment_form = CommentForm()

    if request.method == 'POST':
        if not _is_admin(request.user):
            messages.error(request, 'Only admins can post comments.')
            return redirect('issues:issue_detail', pk=pk)
        form = CommentForm(request.POST)
        if form.is_valid():
            IssueComment.objects.create(
                issue=issue, author=request.user, body=form.cleaned_data['body']
            )
            messages.success(request, 'Comment added.')
            return redirect('issues:issue_detail', pk=pk)

    return render(request, 'issues/issue_detail.html', {
        'issue': issue,
        'comments': comments,
        'comment_form': comment_form,
    })


@login_required
@role_required(['super_admin', 'admin'])
def issue_create(request):
    if request.method == 'POST':
        form = IssueForm(request.POST)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.reported_by = request.user
            issue.save()
            messages.success(request, f'Issue "{issue.title}" created.')
            return redirect('issues:issue_detail', pk=issue.pk)
        else:
            # Display form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label or field}: {error}")
    else:
        form = IssueForm()
    return render(request, 'issues/issue_form.html', {'form': form, 'title': 'New Issue'})


@login_required
@role_required(['super_admin', 'admin'])
def issue_update(request, pk):
    issue = get_object_or_404(Issue, pk=pk)
    if issue.status == 'Closed':
        messages.error(request, 'This issue is Closed and cannot be edited.')
        return redirect('issues:issue_detail', pk=pk)
    
    if request.method == 'POST':
        form = IssueForm(request.POST, instance=issue)
        if form.is_valid():
            form.save()
            messages.success(request, f'Issue "{issue.title}" updated.')
            return redirect('issues:issue_detail', pk=issue.pk)
        else:
            # Display form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label or field}: {error}")
    else:
        form = IssueForm(instance=issue)
    return render(request, 'issues/issue_form.html', {
        'form': form, 'issue': issue, 'title': f'Edit Issue: {issue.title}'
    })


# ─── Projects ─────────────────────────────────────────────────────────────────

@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    comments = project.comments.select_related('author')
    comment_form = CommentForm()
    cost_items = project.cost_items.all()
    total_cost = sum(item.total_price for item in cost_items)

    if request.method == 'POST':
        if not _is_admin(request.user):
            messages.error(request, 'Only admins can post comments.')
            return redirect('issues:project_detail', pk=pk)
        form = CommentForm(request.POST)
        if form.is_valid():
            ProjectComment.objects.create(
                project=project, author=request.user, body=form.cleaned_data['body']
            )
            messages.success(request, 'Comment added.')
            return redirect('issues:project_detail', pk=pk)

    # Build category availability data
    category_counts = []
    for cat in project.categories.all():
        assets = Asset.objects.filter(category=cat, is_deleted=False).order_by('status__name', 'asset_id')
        available_count = assets.filter(status__name='Available').count()
        category_counts.append({
            'category': cat,
            'available_count': available_count,
            'assets': assets,
        })

    return render(request, 'issues/project_detail.html', {
        'project': project,
        'comments': comments,
        'comment_form': comment_form,
        'category_counts': category_counts,
        'cost_items': cost_items,
        'total_cost': total_cost,
    })


@login_required
def category_assets_api(request, category_id):
    """Return assets in a category as JSON for the project form"""
    cat = get_object_or_404(Category, pk=category_id)
    assets = Asset.objects.filter(
        category=cat, is_deleted=False
    ).order_by('status__name', 'asset_id').select_related('status', 'assigned_to', 'department')
    data = [{
        'id': a.pk,
        'asset_id': a.asset_id,
        'name': a.name or a.asset_id,
        'status': a.status.name if a.status else 'Unknown',
        'assigned_to': str(a.assigned_to) if a.assigned_to else None,
        'department': str(a.department) if a.department else None,
    } for a in assets]
    return JsonResponse({'category': cat.name, 'assets': data})


def _save_project_items(project, post_data):
    """Save/replace project cost items from POST data."""
    item_names = post_data.getlist('item_name[]')
    item_types = post_data.getlist('item_type[]')
    unit_prices = post_data.getlist('unit_price[]')
    quantities = post_data.getlist('quantity[]')

    project.cost_items.all().delete()
    for i in range(len(item_names)):
        name = item_names[i].strip()
        if not name:
            continue
        try:
            price = float(unit_prices[i] or 0)
            qty = int(quantities[i] or 1)
        except (ValueError, IndexError):
            price, qty = 0, 1
        itype = item_types[i] if i < len(item_types) else 'Asset'
        ProjectItem.objects.create(
            project=project,
            item_name=name,
            item_type=itype,
            unit_price=price,
            quantity=qty,
        )


@login_required
@role_required(['super_admin', 'admin'])
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.reported_by = request.user
            project.save()
            form.save_m2m()
            _save_project_items(project, request.POST)
            messages.success(request, f'Project "{project.title}" created.')
            return redirect('issues:project_detail', pk=project.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label or field}: {error}")
    else:
        form = ProjectForm()
    return render(request, 'issues/project_form.html', {'form': form, 'title': 'New Project'})


@login_required
@role_required(['super_admin', 'admin'])
def project_update(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.status == 'Done':
        messages.error(request, 'This project is Done and cannot be edited.')
        return redirect('issues:project_detail', pk=pk)
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            _save_project_items(project, request.POST)
            messages.success(request, f'Project "{project.title}" updated.')
            return redirect('issues:project_detail', pk=project.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label or field}: {error}")
    else:
        form = ProjectForm(instance=project)
    return render(request, 'issues/project_form.html', {
        'form': form, 'project': project, 'title': f'Edit: {project.title}',
        'cost_items': project.cost_items.all(),
    })
