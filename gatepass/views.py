from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
import json

from .models import GatePass, GatePassPermission, GatePassLog
from .forms import GatePassForm, GatePassStatusUpdateForm, GatePassPermissionForm, GatePassSearchForm
from .permissions import (
    gatepass_create_required, gatepass_approve_required, gatepass_view_all_required,
    gatepass_manage_permissions_required, gatepass_owner_or_manager_required,
    can_create_gatepass, can_view_all_gatepasses
)

User = get_user_model()

@login_required
def dashboard(request):
    user_can_create = can_create_gatepass(request.user)
    user_can_view_all = can_view_all_gatepasses(request.user)
    
    if user_can_view_all:
        gatepasses = GatePass.objects.all()
    else:
        gatepasses = GatePass.objects.filter(created_by=request.user)
    
    stats = {
        'total': gatepasses.count(),
        'pending': gatepasses.filter(status='PENDING').count(),
        'approved': gatepasses.filter(status='APPROVED').count(),
        'rejected': gatepasses.filter(status='REJECTED').count(),
    }
    
    recent_gatepasses = gatepasses.order_by('-created_at')[:5]
    
    context = {
        'stats': stats,
        'recent_gatepasses': recent_gatepasses,
        'user_can_create': user_can_create,
        'user_can_view_all': user_can_view_all,
    }
    return render(request, 'gatepass/dashboard.html', context)

@gatepass_create_required
def create_gatepass(request):
    if request.method == 'POST':
        form = GatePassForm(request.POST)
        if form.is_valid():
            try:
                gatepass = form.save(commit=False)
                gatepass.created_by = request.user
                gatepass.save()
                
                GatePassLog.objects.create(
                    gatepass=gatepass,
                    action='CREATED',
                    details='Gate pass created',
                    performed_by=request.user
                )
                
                messages.success(request, f'✅ Gate pass {gatepass.pass_number} created successfully!')
                return redirect('gatepass:detail', pk=gatepass.pk)
                
            except Exception as e:
                messages.error(request, f'❌ Error creating gate pass: {str(e)}')
                print(f"Gate pass creation error: {e}")  # For debugging
        else:
            # Form validation errors
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            
            if error_messages:
                messages.error(request, f'❌ Please fix the following errors: {", ".join(error_messages)}')
            else:
                messages.error(request, '❌ Please check all required fields and try again.')
    else:
        form = GatePassForm()
    
    return render(request, 'gatepass/create.html', {'form': form})

@login_required
def list_gatepasses(request):
    user_can_view_all = can_view_all_gatepasses(request.user)
    
    if user_can_view_all:
        gatepasses = GatePass.objects.all()
    else:
        gatepasses = GatePass.objects.filter(created_by=request.user)
    
    form = GatePassSearchForm(request.GET)
    if form.is_valid():
        search = form.cleaned_data.get('search')
        status = form.cleaned_data.get('status')
        pass_type = form.cleaned_data.get('pass_type')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        
        if search:
            gatepasses = gatepasses.filter(
                Q(pass_number__icontains=search) |
                Q(visitor_name__icontains=search) |
                Q(visitor_phone__icontains=search)
            )
        
        if status:
            gatepasses = gatepasses.filter(status=status)
        
        if pass_type:
            gatepasses = gatepasses.filter(pass_type=pass_type)
        
        if date_from:
            gatepasses = gatepasses.filter(created_at__date__gte=date_from)
        
        if date_to:
            gatepasses = gatepasses.filter(created_at__date__lte=date_to)
    
    paginator = Paginator(gatepasses.order_by('-created_at'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'user_can_view_all': user_can_view_all,
    }
    return render(request, 'gatepass/list.html', context)

@gatepass_owner_or_manager_required
def gatepass_detail(request, pk):
    gatepass = get_object_or_404(GatePass, pk=pk)
    logs = gatepass.logs.all().order_by('-timestamp')
    
    context = {
        'gatepass': gatepass,
        'logs': logs,
    }
    return render(request, 'gatepass/detail.html', context)

@gatepass_approve_required
def approve_gatepass(request, pk):
    gatepass = get_object_or_404(GatePass, pk=pk)
    
    if request.method == 'POST':
        form = GatePassStatusUpdateForm(request.POST, instance=gatepass)
        if form.is_valid():
            gatepass = form.save(commit=False)
            if gatepass.status == 'APPROVED':
                gatepass.approved_by = request.user
                gatepass.approved_at = timezone.now()
            gatepass.save()
            
            GatePassLog.objects.create(
                gatepass=gatepass,
                action=f'STATUS_CHANGED_TO_{gatepass.status}',
                details=f'Status changed to {gatepass.get_status_display()}',
                performed_by=request.user
            )
            
            messages.success(request, f'Gate pass status updated to {gatepass.get_status_display()}')
            return redirect('gatepass:detail', pk=gatepass.pk)
    else:
        form = GatePassStatusUpdateForm(instance=gatepass)
    
    context = {
        'form': form,
        'gatepass': gatepass,
    }
    return render(request, 'gatepass/approve.html', context)

@gatepass_manage_permissions_required
def manage_permissions(request):
    permissions = GatePassPermission.objects.all().select_related('user', 'granted_by')
    users_with_permission = User.objects.filter(gatepass_permission__can_create_gatepass=True)
    
    if request.method == 'POST':
        form = GatePassPermissionForm(request.POST)
        if form.is_valid():
            permission, created = GatePassPermission.objects.get_or_create(
                user=form.cleaned_data['user'],
                defaults={
                    'can_create_gatepass': form.cleaned_data['can_create_gatepass'],
                    'granted_by': request.user
                }
            )
            
            if not created:
                permission.can_create_gatepass = form.cleaned_data['can_create_gatepass']
                permission.granted_by = request.user
                permission.save()
            
            action = 'granted' if form.cleaned_data['can_create_gatepass'] else 'revoked'
            messages.success(request, f'Gate pass creation permission {action} for {permission.user.full_name}')
            return redirect('gatepass:manage_permissions')
    else:
        form = GatePassPermissionForm()
    
    context = {
        'form': form,
        'permissions': permissions,
        'users_with_permission': users_with_permission,
    }
    return render(request, 'gatepass/manage_permissions.html', context)

@gatepass_manage_permissions_required
def toggle_permission(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, pk=user_id)
        permission, created = GatePassPermission.objects.get_or_create(
            user=user,
            defaults={'can_create_gatepass': True, 'granted_by': request.user}
        )
        
        if not created:
            permission.can_create_gatepass = not permission.can_create_gatepass
            permission.granted_by = request.user
            permission.save()
        
        status = 'granted' if permission.can_create_gatepass else 'revoked'
        return JsonResponse({
            'success': True,
            'status': status,
            'message': f'Permission {status} for {user.full_name}'
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@gatepass_owner_or_manager_required
def print_gatepass(request, pk):
    gatepass = get_object_or_404(GatePass, pk=pk)
    
    context = {
        'gatepass': gatepass,
    }
    return render(request, 'gatepass/print.html', context)
