from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.db import transaction
from django.utils import timezone
from assets.models import Department, Asset, Person
from .forms import PersonForm, DepartmentForm, UserCreateForm, UserEditForm, PasswordChangeRequiredForm
from .models import UserProfile


def login_view(request):
    """User login view with password change check"""
    if request.user.is_authenticated:
        # Check if user needs to change password
        if hasattr(request.user, 'profile') and request.user.profile.needs_password_change():
            return redirect('users:password_change_required')
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                
                # Check if user needs to change password
                if hasattr(user, 'profile') and user.profile.needs_password_change():
                    messages.warning(request, 'Please change your password before continuing.')
                    return redirect('users:password_change_required')
                
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


@login_required
def password_change_required_view(request):
    """Force password change on first login or when admin requires it"""
    if not hasattr(request.user, 'profile') or not request.user.profile.needs_password_change():
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        form = PasswordChangeRequiredForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Update profile
            profile = user.profile
            profile.password_changed_at = timezone.now()
            profile.is_first_login = False
            profile.must_change_password = False
            profile.save()
            
            # Keep user logged in after password change
            update_session_auth_hash(request, user)
            
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('dashboard:home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = PasswordChangeRequiredForm(request.user)
    
    return render(request, 'users/password_change_required.html', {
        'form': form,
        'is_first_login': request.user.profile.is_first_login
    })


@login_required
def password_change_view(request):
    """Regular password change view"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Update profile
            if hasattr(user, 'profile'):
                profile = user.profile
                profile.password_changed_at = timezone.now()
                profile.save()
            
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('users:profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'users/password_change.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.is_superuser or (hasattr(u, 'profile') and u.profile.is_admin()))
def user_list_view(request):
    """List all users for admin management"""
    users = User.objects.select_related('profile').order_by('username')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Filter by role
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(profile__role=role_filter)
    
    return render(request, 'users/user_list.html', {
        'users': users,
        'search_query': search_query,
        'role_filter': role_filter,
        'role_choices': UserProfile.ROLE_CHOICES,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser or (hasattr(u, 'profile') and u.profile.is_admin()))
def user_create_view(request):
    """Create new user (admin only)"""
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request, 
                f"User '{user.username}' created successfully. They will be required to change their password on first login."
            )
            return redirect('users:user_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields.get(field, field).label or field}: {error}")
    else:
        form = UserCreateForm()
    
    return render(request, 'users/user_form.html', {
        'form': form,
        'title': 'Create User',
        'is_create': True
    })


@login_required
@user_passes_test(lambda u: u.is_superuser or (hasattr(u, 'profile') and u.profile.is_admin()))
def user_edit_view(request, user_id):
    """Edit existing user (admin only)"""
    user = get_object_or_404(User, pk=user_id)
    
    # Prevent editing superusers unless you're a superuser
    if user.is_superuser and not request.user.is_superuser:
        messages.error(request, "You don't have permission to edit this user.")
        return redirect('users:user_list')
    
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User '{user.username}' updated successfully.")
            return redirect('users:user_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields.get(field, field).label or field}: {error}")
    else:
        form = UserEditForm(instance=user)
    
    return render(request, 'users/user_form.html', {
        'form': form,
        'title': f'Edit User: {user.username}',
        'is_create': False,
        'edit_user': user
    })


@login_required
@user_passes_test(lambda u: u.is_superuser or (hasattr(u, 'profile') and u.profile.is_admin()))
def user_reset_password_view(request, user_id):
    """Admin action to force password reset on next login"""
    user = get_object_or_404(User, pk=user_id)
    
    # Prevent resetting superuser passwords unless you're a superuser
    if user.is_superuser and not request.user.is_superuser:
        messages.error(request, "You don't have permission to reset this user's password.")
        return redirect('users:user_list')
    
    if request.method == 'POST':
        if hasattr(user, 'profile'):
            profile = user.profile
            profile.must_change_password = True
            profile.save()
            messages.success(
                request, 
                f"User '{user.username}' will be required to change their password on next login."
            )
        return redirect('users:user_list')
    
    return render(request, 'users/user_reset_password.html', {'reset_user': user})


@login_required
@user_passes_test(lambda u: u.is_superuser or (hasattr(u, 'profile') and u.profile.is_admin()))
def user_toggle_active_view(request, user_id):
    """Toggle user active status (disable/enable account)"""
    user = get_object_or_404(User, pk=user_id)
    
    # Prevent disabling superusers unless you're a superuser
    if user.is_superuser and not request.user.is_superuser:
        messages.error(request, "You don't have permission to modify this user.")
        return redirect('users:user_list')
    
    # Prevent self-deactivation
    if user == request.user:
        messages.error(request, "You cannot disable your own account.")
        return redirect('users:user_list')
    
    user.is_active = not user.is_active
    user.save()
    
    status = "enabled" if user.is_active else "disabled"
    messages.success(request, f"User '{user.username}' has been {status}.")
    return redirect('users:user_list')
