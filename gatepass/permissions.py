from functools import wraps
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .models import GatePass, GatePassPermission

def can_create_gatepass(user):
    if not user.is_authenticated:
        return False
    
    if user.user_type in ['ADMINISTRATOR']:
        return True
    
    if user.user_type in ['COORDINATOR']:
        return True
    
    try:
        permission = user.gatepass_permission
        return permission.can_create_gatepass
    except GatePassPermission.DoesNotExist:
        return False

def can_approve_gatepass(user):
    if not user.is_authenticated:
        return False
    
    return user.user_type in ['ADMINISTRATOR', 'COORDINATOR']

def can_view_all_gatepasses(user):
    if not user.is_authenticated:
        return False
    
    return user.user_type in ['ADMINISTRATOR', 'COORDINATOR']

def can_manage_permissions(user):
    if not user.is_authenticated:
        return False
    
    return user.user_type == 'ADMINISTRATOR'

def gatepass_create_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not can_create_gatepass(request.user):
            return HttpResponseForbidden("You don't have permission to create gate passes.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def gatepass_approve_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not can_approve_gatepass(request.user):
            return HttpResponseForbidden("You don't have permission to approve gate passes.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def gatepass_view_all_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not can_view_all_gatepasses(request.user):
            return HttpResponseForbidden("You don't have permission to view all gate passes.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def gatepass_manage_permissions_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not can_manage_permissions(request.user):
            return HttpResponseForbidden("You don't have permission to manage gate pass permissions.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def gatepass_owner_or_manager_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        gatepass_id = kwargs.get('pk') or kwargs.get('gatepass_id')
        if gatepass_id:
            gatepass = get_object_or_404(GatePass, pk=gatepass_id)
            if (request.user == gatepass.created_by or 
                can_view_all_gatepasses(request.user)):
                return view_func(request, *args, **kwargs)
        return HttpResponseForbidden("You don't have permission to access this gate pass.")
    return _wrapped_view