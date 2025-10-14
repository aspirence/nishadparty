from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import FeaturePermission


def feature_required(feature):
    """
    Decorator to check if user has permission for a specific feature.
    Usage: @feature_required('USER_MANAGEMENT')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            # Check if user has permission
            if FeaturePermission.user_has_permission(request.user, feature):
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'You do not have permission to access this feature.')
                return redirect('dashboard')
        return wrapped_view
    return decorator


def admin_or_feature_required(feature):
    """
    Decorator that allows access if user is admin OR has specific feature permission.
    Usage: @admin_or_feature_required('ASSET_MANAGEMENT')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            if request.user.user_type == 'ADMINISTRATOR' or \
               FeaturePermission.user_has_permission(request.user, feature):
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'You do not have permission to access this feature.')
                return redirect('dashboard')
        return wrapped_view
    return decorator


def admin_required(view_func):
    """
    Decorator to check if user is an administrator.
    """
    @wraps(view_func)
    @login_required
    def wrapped_view(request, *args, **kwargs):
        if request.user.user_type == 'ADMINISTRATOR':
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'You must be an administrator to access this page.')
            return redirect('dashboard')
    return wrapped_view
