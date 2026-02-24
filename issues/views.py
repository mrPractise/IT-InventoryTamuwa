from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Issue, IssueComment, Project, ProjectComment
from .forms import IssueForm, ProjectForm, CommentForm
from users.decorators import role_required


def _is_admin(user):
    return user.is_superuser or getattr(getattr(user, 'profile', None), 'role', '') in ('super_admin', 'admin')


# ─── Combined Home ───────────────────────────────────────────────────────────

@login_required
def issues_home(request):
    """Landing page with Issues and Projects as two tabs."""
    # Issue filters
    i_search = request.GET.get('i_search', '')
    i_priority = request.GET.get('i_priority', '')
    i_status = request.GET.get('i_status', '')

    issues_qs = Issue.objects.select_related('asset', 'department', 'requisition', 'reported_by')
    if i_search:
        issues_qs = issues_qs.filter(
            Q(title__icontains=i_search) | Q(description__icontains=i_search)
        )
    if i_priority:
        issues_qs = issues_qs.filter(priority=i_priority)
    if i_status:
        issues_qs = issues_qs.filter(status=i_status)

    # Project filters
    p_search = request.GET.get('p_search', '')
    p_priority = request.GET.get('p_priority', '')
    p_status = request.GET.get('p_status', '')

    projects_qs = Project.objects.prefetch_related('categories', 'requisitions').select_related('reported_by')
    if p_search:
        projects_qs = projects_qs.filter(
            Q(title__icontains=p_search) | Q(description__icontains=p_search)
        )
    if p_priority:
        projects_qs = projects_qs.filter(priority=p_priority)
    if p_status:
        projects_qs = projects_qs.filter(status=p_status)

    # Active tab
    active_tab = request.GET.get('tab', 'issues')

    issues_paginator = Paginator(issues_qs, 15)
    issues_page = issues_paginator.get_page(request.GET.get('i_page'))

    projects_paginator = Paginator(projects_qs, 15)
    projects_page = projects_paginator.get_page(request.GET.get('p_page'))

    return render(request, 'issues/list.html', {
        'active_tab': active_tab,
        # Issues
        'issues_page': issues_page,
        'issues_count': Issue.objects.exclude(status='Closed').count(),
        'i_search': i_search,
        'i_priority': i_priority,
        'i_status': i_status,
        # Projects
        'projects_page': projects_page,
        'projects_count': Project.objects.exclude(status='Done').count(),
        'p_search': p_search,
        'p_priority': p_priority,
        'p_status': p_status,
        # Choices
        'issue_priority_choices': Issue.PRIORITY_CHOICES,
        'issue_status_choices': Issue.STATUS_CHOICES,
        'project_priority_choices': Project.PRIORITY_CHOICES,
        'project_status_choices': Project.STATUS_CHOICES,
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
    form = IssueForm(request.POST or None)
    if form.is_valid():
        issue = form.save(commit=False)
        issue.reported_by = request.user
        issue.save()
        messages.success(request, f'Issue "{issue.title}" created.')
        return redirect('issues:issue_detail', pk=issue.pk)
    return render(request, 'issues/issue_form.html', {'form': form, 'title': 'New Issue'})


@login_required
@role_required(['super_admin', 'admin'])
def issue_update(request, pk):
    issue = get_object_or_404(Issue, pk=pk)
    if issue.status == 'Closed':
        messages.error(request, 'This issue is Closed and cannot be edited.')
        return redirect('issues:issue_detail', pk=pk)
    form = IssueForm(request.POST or None, instance=issue)
    if form.is_valid():
        form.save()
        messages.success(request, f'Issue "{issue.title}" updated.')
        return redirect('issues:issue_detail', pk=issue.pk)
    return render(request, 'issues/issue_form.html', {
        'form': form, 'issue': issue, 'title': f'Edit Issue: {issue.title}'
    })


# ─── Projects ─────────────────────────────────────────────────────────────────

@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    comments = project.comments.select_related('author')
    comment_form = CommentForm()

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

    return render(request, 'issues/project_detail.html', {
        'project': project,
        'comments': comments,
        'comment_form': comment_form,
        'category_counts': project.category_asset_counts(),
    })


@login_required
@role_required(['super_admin', 'admin'])
def project_create(request):
    form = ProjectForm(request.POST or None)
    if form.is_valid():
        project = form.save(commit=False)
        project.reported_by = request.user
        project.save()
        form.save_m2m()
        messages.success(request, f'Project "{project.title}" created.')
        return redirect('issues:project_detail', pk=project.pk)
    return render(request, 'issues/project_form.html', {'form': form, 'title': 'New Project'})


@login_required
@role_required(['super_admin', 'admin'])
def project_update(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if project.status == 'Done':
        messages.error(request, 'This project is Done and cannot be edited.')
        return redirect('issues:project_detail', pk=pk)
    form = ProjectForm(request.POST or None, instance=project)
    if form.is_valid():
        form.save()
        messages.success(request, f'Project "{project.title}" updated.')
        return redirect('issues:project_detail', pk=project.pk)
    return render(request, 'issues/project_form.html', {
        'form': form, 'project': project, 'title': f'Edit: {project.title}'
    })
