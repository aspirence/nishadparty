from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.db import models
from django.core.paginator import Paginator
from datetime import timedelta

from .models import Asset, AssetCheckout, AssetMaintenance
from accounts.models import User
from accounts.decorators import admin_or_feature_required
from django.forms import ModelForm

def admin_required(user):
    """Check if user is an administrator"""
    return user.is_authenticated and user.user_type == 'ADMINISTRATOR'

@login_required
@admin_or_feature_required('ASSET_MANAGEMENT')
def asset_dashboard(request):
    """Asset dashboard showing overview for admins or user assignments for regular users"""
    if request.user.user_type == 'ADMINISTRATOR':
        # Admin dashboard
        total_assets = Asset.objects.count()
        available_assets = Asset.objects.filter(status='AVAILABLE').count()
        in_use_assets = Asset.objects.filter(status='IN_USE').count()
        maintenance_assets = Asset.objects.filter(status='MAINTENANCE').count()
        
        # Recent assignments
        recent_assignments = AssetCheckout.objects.select_related('asset', 'checked_out_by').order_by('-assignment_date')[:10]
        
        # Pending acceptances
        pending_assignments = AssetCheckout.objects.filter(status='PENDING').select_related('asset', 'checked_out_by')
        
        # Overdue returns
        overdue_assignments = AssetCheckout.objects.filter(
            status__in=['ACCEPTED', 'IN_USE'],
            expected_return_date__lt=timezone.now()
        ).select_related('asset', 'checked_out_by')
        
        context = {
            'is_admin': True,
            'total_assets': total_assets,
            'available_assets': available_assets,
            'in_use_assets': in_use_assets,
            'maintenance_assets': maintenance_assets,
            'recent_assignments': recent_assignments,
            'pending_assignments': pending_assignments,
            'overdue_assignments': overdue_assignments,
        }
        return render(request, 'assets/admin_dashboard.html', context)
    else:
        # User dashboard
        user_assignments = AssetCheckout.objects.filter(
            checked_out_by=request.user
        ).select_related('asset').order_by('-assignment_date')
        
        # Pending assignments that need user action
        pending_assignments = user_assignments.filter(status='PENDING')
        active_assignments = user_assignments.filter(status__in=['ACCEPTED', 'IN_USE'])
        
        context = {
            'is_admin': False,
            'user_assignments': user_assignments[:10],
            'pending_assignments': pending_assignments,
            'active_assignments': active_assignments,
        }
        return render(request, 'assets/user_dashboard.html', context)

@login_required
def asset_list(request):
    """List all assets for admin, or assigned assets for users"""
    if request.user.user_type == 'ADMINISTRATOR':
        assets = Asset.objects.all().order_by('-created_at')
        
        # Filter by status if requested
        status_filter = request.GET.get('status')
        if status_filter:
            assets = assets.filter(status=status_filter)
            
        # Search functionality
        search_query = request.GET.get('search')
        if search_query:
            assets = assets.filter(
                models.Q(name__icontains=search_query) |
                models.Q(asset_code__icontains=search_query) |
                models.Q(serial_number__icontains=search_query)
            )
        
        paginator = Paginator(assets, 20)
        page = request.GET.get('page')
        assets = paginator.get_page(page)
        
        context = {
            'assets': assets,
            'is_admin': True,
            'status_filter': status_filter,
            'search_query': search_query,
        }
        return render(request, 'assets/asset_list.html', context)
    else:
        # Regular users see only their assigned assets
        assignments = AssetCheckout.objects.filter(
            checked_out_by=request.user
        ).select_related('asset').order_by('-assignment_date')
        
        context = {
            'assignments': assignments,
            'is_admin': False,
        }
        return render(request, 'assets/user_asset_list.html', context)

@login_required
def assign_asset(request):
    """Admin function to assign asset to user"""
    if not admin_required(request.user):
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('assets:dashboard')
    
    if request.method == 'POST':
        asset_id = request.POST.get('asset_id')
        user_id = request.POST.get('user_id')
        purpose = request.POST.get('purpose', '')
        expected_return_date = request.POST.get('expected_return_date')
        admin_notes = request.POST.get('admin_notes', '')
        
        try:
            asset = get_object_or_404(Asset, id=asset_id)
            user = get_object_or_404(User, id=user_id)
            
            if asset.status != 'AVAILABLE':
                messages.error(request, _('This asset is currently not available.'))
                return redirect('assets:assign')
            
            # Create assignment
            assignment = AssetCheckout.objects.create(
                asset=asset,
                checked_out_by=user,
                assigned_by=request.user,
                expected_return_date=expected_return_date,
                purpose=purpose,
                admin_notes=admin_notes,
                condition_checkout=asset.condition,
                status='PENDING'
            )
            
            # Update asset status to show it's assigned (pending acceptance)
            asset.status = 'ASSIGNED'
            asset.save()
            
            messages.success(request, _('Asset assigned successfully. User needs to accept.'))
            return redirect('assets:dashboard')
            
        except Exception as e:
            messages.error(request, _('Error occurred while assigning asset.'))
            return redirect('assets:assign')
    
    # GET request - show assignment form
    available_assets = Asset.objects.filter(status='AVAILABLE')
    active_users = User.objects.filter(is_active=True).exclude(user_type='ADMINISTRATOR')
    
    # Check if specific asset is requested
    selected_asset_id = request.GET.get('asset')
    selected_asset = None
    if selected_asset_id:
        try:
            selected_asset = Asset.objects.get(id=selected_asset_id, status='AVAILABLE')
        except Asset.DoesNotExist:
            pass
    
    context = {
        'available_assets': available_assets,
        'active_users': active_users,
        'selected_asset': selected_asset,
    }
    return render(request, 'assets/assign_asset.html', context)

@login_required
def accept_assignment(request, assignment_id):
    """User accepts an asset assignment"""
    assignment = get_object_or_404(AssetCheckout, id=assignment_id, checked_out_by=request.user, status='PENDING')
    
    if request.method == 'POST':
        user_notes = request.POST.get('user_notes', '')
        assignment.user_notes = user_notes
        assignment.accept_assignment()
        
        messages.success(request, _('You have accepted the asset assignment.'))
        return redirect('assets:dashboard')
    
    context = {
        'assignment': assignment,
    }
    return render(request, 'assets/accept_assignment.html', context)

@login_required
def reject_assignment(request, assignment_id):
    """User rejects an asset assignment"""
    assignment = get_object_or_404(AssetCheckout, id=assignment_id, checked_out_by=request.user, status='PENDING')
    
    if request.method == 'POST':
        rejection_reason = request.POST.get('rejection_reason', '')
        assignment.reject_assignment(rejection_reason)
        
        messages.info(request, _('You have rejected the asset assignment.'))
        return redirect('assets:dashboard')
    
    context = {
        'assignment': assignment,
    }
    return render(request, 'assets/reject_assignment.html', context)

@login_required
def return_asset(request, assignment_id):
    """User returns an assigned asset"""
    assignment = get_object_or_404(
        AssetCheckout, 
        id=assignment_id, 
        checked_out_by=request.user, 
        status__in=['ACCEPTED', 'IN_USE']
    )
    
    if request.method == 'POST':
        condition = request.POST.get('condition')
        return_notes = request.POST.get('return_notes', '')
        damage_reported = request.POST.get('damage_reported') == 'on'
        damage_description = request.POST.get('damage_description', '')
        
        assignment.return_asset(
            condition=condition,
            notes=return_notes,
            damage=damage_reported,
            damage_desc=damage_description
        )
        
        messages.success(request, _('Asset returned successfully.'))
        return redirect('assets:dashboard')
    
    context = {
        'assignment': assignment,
    }
    return render(request, 'assets/return_asset.html', context)

@login_required
def asset_history(request, asset_id):
    """View asset history"""
    asset = get_object_or_404(Asset, id=asset_id)
    
    # Check permissions
    if request.user.user_type != 'ADMINISTRATOR':
        # Users can only see history of assets they've been assigned
        user_assignments = AssetCheckout.objects.filter(asset=asset, checked_out_by=request.user)
        if not user_assignments.exists():
            messages.error(request, _('You do not have permission to view this asset history.'))
            return redirect('assets:dashboard')
    
    assignments = AssetCheckout.objects.filter(asset=asset).select_related('checked_out_by', 'assigned_by').order_by('-assignment_date')
    maintenance_records = AssetMaintenance.objects.filter(asset=asset).order_by('-maintenance_date')
    
    context = {
        'asset': asset,
        'assignments': assignments,
        'maintenance_records': maintenance_records,
    }
    return render(request, 'assets/asset_history.html', context)

@login_required
def add_asset(request):
    """Admin function to add new asset"""
    if not admin_required(request.user):
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('assets:dashboard')
    
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name', '').strip()
            asset_type = request.POST.get('asset_type', '')
            description = request.POST.get('description', '').strip()
            purchase_date = request.POST.get('purchase_date', '')
            purchase_cost = request.POST.get('purchase_cost', '')
            current_location = request.POST.get('current_location', '').strip()
            constituency = request.POST.get('constituency', '').strip()
            condition = request.POST.get('condition', 'GOOD')
            serial_number = request.POST.get('serial_number', '').strip()
            model_number = request.POST.get('model_number', '').strip()
            manufacturer = request.POST.get('manufacturer', '').strip()
            
            # Validation
            if not name or not asset_type:
                messages.error(request, _('Please fill in all required information.'))
                return render(request, 'assets/add_asset.html')
            
            # Create asset
            asset = Asset.objects.create(
                name=name,
                asset_type=asset_type,
                description=description,
                purchase_date=purchase_date if purchase_date else None,
                purchase_cost=purchase_cost if purchase_cost else None,
                current_location=current_location,
                constituency=constituency,
                condition=condition,
                serial_number=serial_number,
                model_number=model_number,
                manufacturer=manufacturer,
                created_by=request.user,
                status='AVAILABLE'
            )
            
            # Handle image upload
            if 'image' in request.FILES:
                asset.image = request.FILES['image']
                asset.save()
            
            messages.success(request, _('Asset added successfully.'))
            return redirect('assets:dashboard')
            
        except Exception as e:
            messages.error(request, _('Error occurred while adding asset.'))
            return render(request, 'assets/add_asset.html')
    
    return render(request, 'assets/add_asset.html')

@login_required
def edit_asset(request, asset_id):
    """Admin function to edit existing asset"""
    if not admin_required(request.user):
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('assets:dashboard')
    
    asset = get_object_or_404(Asset, id=asset_id)
    
    if request.method == 'POST':
        try:
            # Update asset data
            asset.name = request.POST.get('name', '').strip()
            asset.asset_type = request.POST.get('asset_type', '')
            asset.description = request.POST.get('description', '').strip()
            
            purchase_date = request.POST.get('purchase_date', '')
            if purchase_date:
                asset.purchase_date = purchase_date
            
            purchase_cost = request.POST.get('purchase_cost', '')
            if purchase_cost:
                asset.purchase_cost = purchase_cost
            
            asset.current_location = request.POST.get('current_location', '').strip()
            asset.constituency = request.POST.get('constituency', '').strip()
            asset.condition = request.POST.get('condition', 'GOOD')
            asset.serial_number = request.POST.get('serial_number', '').strip()
            asset.model_number = request.POST.get('model_number', '').strip()
            asset.manufacturer = request.POST.get('manufacturer', '').strip()
            
            # Handle image upload
            if 'image' in request.FILES:
                asset.image = request.FILES['image']
            
            asset.save()
            
            messages.success(request, _('Asset updated successfully.'))
            return redirect('assets:list')
            
        except Exception as e:
            messages.error(request, _('Error occurred while updating asset.'))
    
    context = {
        'asset': asset,
    }
    return render(request, 'assets/edit_asset.html', context)

@login_required
def delete_asset(request, asset_id):
    """Admin function to delete asset"""
    if not admin_required(request.user):
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('assets:dashboard')

    asset = get_object_or_404(Asset, id=asset_id)

    # Check if asset has active assignments
    active_assignments = AssetCheckout.objects.filter(
        asset=asset,
        status__in=['PENDING', 'ACCEPTED', 'IN_USE']
    ).exists()

    if active_assignments:
        messages.error(request, _('This asset cannot be deleted because it is currently assigned.'))
        return redirect('assets:list')

    if request.method == 'POST':
        asset_name = asset.name
        asset.delete()
        messages.success(request, _('Asset "{}" deleted successfully.'.format(asset_name)))
        return redirect('assets:list')

    context = {
        'asset': asset,
    }
    return render(request, 'assets/delete_asset.html', context)

@login_required
def dashboard_assets_content(request):
    """Return assets dashboard content for AJAX loading"""
    if request.user.user_type == 'ADMINISTRATOR':
        # Admin statistics
        total_assets = Asset.objects.count()
        available_assets = Asset.objects.filter(status='AVAILABLE').count()
        in_use_assets = Asset.objects.filter(status='IN_USE').count()
        maintenance_assets = Asset.objects.filter(status='MAINTENANCE').count()

        # Recent assets
        recent_assets = Asset.objects.all().order_by('-created_at')[:5]

        # Recent assignments
        recent_assignments = AssetCheckout.objects.select_related('asset', 'checked_out_by').order_by('-assignment_date')[:5]

        # Pending assignments
        pending_assignments = AssetCheckout.objects.filter(status='PENDING').select_related('asset', 'checked_out_by').count()

        # Overdue assignments
        overdue_assignments = AssetCheckout.objects.filter(
            status__in=['ACCEPTED', 'IN_USE'],
            expected_return_date__lt=timezone.now()
        ).count()

        context = {
            'is_admin': True,
            'total_assets': total_assets,
            'available_assets': available_assets,
            'in_use_assets': in_use_assets,
            'maintenance_assets': maintenance_assets,
            'recent_assets': recent_assets,
            'recent_assignments': recent_assignments,
            'pending_assignments': pending_assignments,
            'overdue_assignments': overdue_assignments,
        }
    else:
        # User statistics
        user_assignments = AssetCheckout.objects.filter(
            checked_out_by=request.user
        ).select_related('asset').order_by('-assignment_date')[:5]

        # Count of active assignments
        active_assignments_count = AssetCheckout.objects.filter(
            checked_out_by=request.user,
            status__in=['ACCEPTED', 'IN_USE']
        ).count()

        # Count of pending assignments
        pending_assignments_count = AssetCheckout.objects.filter(
            checked_out_by=request.user,
            status='PENDING'
        ).count()

        # Count of returned assignments
        returned_assignments_count = AssetCheckout.objects.filter(
            checked_out_by=request.user,
            status='RETURNED'
        ).count()

        context = {
            'is_admin': False,
            'user_assignments': user_assignments,
            'active_assignments_count': active_assignments_count,
            'pending_assignments_count': pending_assignments_count,
            'returned_assignments_count': returned_assignments_count,
        }

    return render(request, 'assets/dashboard_content.html', context)
