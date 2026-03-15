from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Task
from .forms import TaskForm


@login_required
def task_list(request):
    """List all tasks with filters"""
    tasks = Task.objects.select_related('assigned_to', 'created_by')

    # Filters
    status_filter = request.GET.get('status', '')
    if status_filter:
        tasks = tasks.filter(status=status_filter)

    priority_filter = request.GET.get('priority', '')
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)

    search_query = request.GET.get('search', '')
    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    if sort_by in ['due_date', '-due_date', 'priority', '-priority', 'status', '-status', 'created_at', '-created_at']:
        tasks = tasks.order_by(sort_by)

    # Pagination
    paginator = Paginator(tasks, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'search_query': search_query,
    }
    return render(request, 'tasks/list.html', context)


@login_required
def task_detail(request, pk):
    """Task detail view"""
    task = get_object_or_404(Task, pk=pk)
    return render(request, 'tasks/detail.html', {'task': task})


@login_required
def task_create(request):
    """Create new task"""
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            messages.success(request, f'Task "{task.title}" created!')
            return redirect('tasks:detail', pk=task.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label or field}: {error}")
    else:
        form = TaskForm()
    return render(request, 'tasks/form.html', {'form': form, 'title': 'Create Task'})


@login_required
def task_update(request, pk):
    """Update task"""
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, f'Task "{task.title}" updated!')
            return redirect('tasks:detail', pk=task.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label or field}: {error}")
    else:
        form = TaskForm(instance=task)
    return render(request, 'tasks/form.html', {'form': form, 'title': 'Edit Task', 'task': task})


@login_required
def task_delete(request, pk):
    """Delete task"""
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        task.delete()
        messages.success(request, f'Task "{task.title}" deleted.')
        return redirect('tasks:list')
    return render(request, 'tasks/delete_confirm.html', {'task': task})
