from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(*roles):
    """Restrict a view to users whose role is in `roles`."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            if request.user.role not in roles:
                messages.error(request, "You don't have permission to access that page.")
                return redirect('reports:dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def staff_required(view_func):
    """Allow Admin, Manager, Receptionist, Housekeeping — block Guests."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_staff_member:
            messages.error(request, "You don't have permission to access that page.")
            return redirect('reports:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
