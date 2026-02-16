from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(allowed_roles):
    """Decorator to check user role"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Check if user has profile
            if hasattr(request.user, 'profile'):
                user_role = request.user.profile.role
                if user_role not in allowed_roles:
                    messages.error(request, 'You do not have permission to access this page.')
                    return redirect('dashboard:home')
            else:
                # If no profile, check if superuser
                if not request.user.is_superuser:
                    messages.error(request, 'You do not have permission to access this page.')
                    return redirect('dashboard:home')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
