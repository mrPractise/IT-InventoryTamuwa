from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.db import transaction
from assets.models import Department, Asset, Person
from .forms import PersonForm, DepartmentForm


def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('dashboard:home')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()

    return render(request, 'users/login.html', {'form': form})


@login_required
def profile_view(request):
    """User profile view"""
    profile = getattr(request.user, 'profile', None)
    return render(request, 'users/profile.html', {'profile': profile})


@login_required
def directory_view(request):
    """Main directory view for people and departments."""
    # Annotate people with their asset counts
    people = Person.objects.all().annotate(
        assigned_count=Count(
            'assigned_assets',
            filter=Q(assigned_assets__is_deleted=False)
        )
    ).select_related('department')

    # Annotate departments with their asset counts
    departments = Department.objects.all().annotate(
        asset_count=Count(
            'assets',
            filter=Q(assets__is_deleted=False)
        )
    )

    context = {
        'people': people,
        'departments': departments,
    }
    return render(request, 'users/directory.html', context)


@login_required
def person_assets_view(request, person_id):
    """View to show assets assigned to a specific person."""
    person = get_object_or_404(Person, id=person_id)
    assets = Asset.objects.filter(assigned_to=person, is_deleted=False).select_related('category', 'status')
    
    context = {
        'person': person,
        'assets': assets,
        'view_type': 'person',
    }
    return render(request, 'users/assigned_assets.html', context)


@login_required
def department_assets_view(request, dept_id):
    """Show all assets belonging to a specific department."""
    department = get_object_or_404(Department, pk=dept_id)
    assets = Asset.objects.filter(
        department=department, is_deleted=False
    ).select_related('category', 'status', 'assigned_to').order_by('asset_id')

    # Also get people in this department
    dept_people = Person.objects.filter(
        department=department
    ).annotate(
        assigned_count=Count(
            'assigned_assets',
            filter=Q(assigned_assets__is_deleted=False)
        )
    )

    context = {
        'department': department,
        'assets': assets,
        'dept_people': dept_people,
        'view_type': 'department',
    }
    return render(request, 'users/department_assets.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser or (hasattr(u, 'profile') and u.profile.is_admin()))
def add_person_view(request):
    """View to add a new person."""
    if request.method == 'POST':
        form = PersonForm(request.POST)
        if form.is_valid():
            person = form.save()
            messages.success(request, f"Person {person.full_name} added successfully.")
            return redirect('users:directory')
        else:
            # Display form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label or field}: {error}")
    else:
        form = PersonForm()
    
    return render(request, 'users/add_person.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.is_superuser or (hasattr(u, 'profile') and u.profile.is_admin()))
def add_department_view(request):
    """View to add a new department."""
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            dept = form.save()
            messages.success(request, f"Department '{dept.name}' created successfully.")
            return redirect('users:directory')
        else:
            # Display form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label or field}: {error}")
    else:
        form = DepartmentForm()
    
    return render(request, 'users/add_department.html', {'form': form})
