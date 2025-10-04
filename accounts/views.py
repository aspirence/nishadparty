from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.translation import gettext as _
import json

from .models import User, UserProfile, PhoneVerification, USER_TYPE_CHOICES
from .utils import create_or_update_otp, create_or_update_otp_with_default, send_otp_sms, verify_otp, format_phone_number, format_phone_number_with_country, is_phone_number_valid

class PhoneLoginView(View):
    template_name = 'accounts/phone_login.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        return render(request, self.template_name)
    
    def post(self, request):
        phone_number = request.POST.get('phone_number', '').strip()
        country_code = request.POST.get('country_code', '+91').strip()
        
        if not phone_number:
            return JsonResponse({
                'status': 'error',
                'message': 'Phone number is required'
            }, status=400)
        
        try:
            # Format phone number with country code
            full_phone_number = country_code + phone_number
            formatted_phone = format_phone_number_with_country(full_phone_number, country_code)
            
            # For testing purposes, always use default OTP
            otp_code = create_or_update_otp_with_default(formatted_phone)
            
            # Send OTP via SMS (for testing, this will just print the OTP)
            if send_otp_sms(formatted_phone, otp_code):
                request.session['phone_number'] = formatted_phone
                request.session['country_code'] = country_code
                return JsonResponse({
                    'status': 'success',
                    'message': f'OTP sent successfully! For testing, use: 123456',
                    'redirect_url': reverse('verify_otp')
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Failed to send OTP. Please try again.'
                }, status=500)
        
        except ValueError as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': 'An error occurred. Please try again.'
            }, status=500)

class VerifyOTPView(View):
    template_name = 'accounts/verify_otp.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        
        phone_number = request.session.get('phone_number')
        if not phone_number:
            return redirect('phone_login')
        
        # Mask phone number for display
        masked_phone = phone_number[:2] + 'X' * (len(phone_number) - 6) + phone_number[-4:]
        
        return render(request, self.template_name, {
            'masked_phone': masked_phone,
            'phone_number': phone_number
        })
    
    def post(self, request):
        phone_number = request.session.get('phone_number')
        otp_code = request.POST.get('otp_code', '').strip()
        
        if not phone_number:
            return JsonResponse({
                'status': 'error',
                'message': 'Session expired. Please start over.'
            }, status=400)
        
        if not otp_code:
            return JsonResponse({
                'status': 'error',
                'message': 'OTP is required'
            }, status=400)
        
        success, message, verification = verify_otp(phone_number, otp_code)
        
        if success:
            # Get or create user
            user, created = User.objects.get_or_create(
                phone_number=phone_number,
                defaults={
                    'username': phone_number,
                    'is_phone_verified': True
                }
            )
            
            if not created and not user.is_phone_verified:
                user.is_phone_verified = True
                user.save()
            
            # Create user profile if it doesn't exist
            UserProfile.objects.get_or_create(user=user)
            
            # Login user
            login(request, user)
            
            # Clear session
            if 'phone_number' in request.session:
                del request.session['phone_number']
            
            # Redirect based on profile completion
            if created or not user.first_name:
                redirect_url = reverse('complete_profile')
            else:
                redirect_url = reverse('home')
            
            return JsonResponse({
                'status': 'success',
                'message': 'Login successful',
                'redirect_url': redirect_url
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': message
            }, status=400)

class ResendOTPView(View):
    def post(self, request):
        phone_number = request.session.get('phone_number')
        
        if not phone_number:
            return JsonResponse({
                'status': 'error',
                'message': 'Session expired. Please start over.'
            }, status=400)
        
        try:
            # Check if we can send another OTP (rate limiting)
            recent_otp = PhoneVerification.objects.filter(
                phone_number=phone_number,
                created_at__gte=timezone.now() - timezone.timedelta(minutes=1)
            ).first()
            
            if recent_otp:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Please wait 1 minute before requesting another OTP.'
                }, status=429)
            
            otp_code = create_or_update_otp(phone_number)
            
            if send_otp_sms(phone_number, otp_code):
                return JsonResponse({
                    'status': 'success',
                    'message': 'OTP resent successfully'
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Failed to resend OTP. Please try again.'
                }, status=500)
        
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': 'An error occurred. Please try again.'
            }, status=500)

@login_required
def complete_profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update user basic info
        request.user.first_name = request.POST.get('first_name', '').strip()
        request.user.last_name = request.POST.get('last_name', '').strip()
        request.user.email = request.POST.get('email', '').strip()
        request.user.constituency = request.POST.get('constituency', '').strip()
        request.user.district = request.POST.get('district', '').strip()
        request.user.state = request.POST.get('state', '').strip()
        request.user.preferred_language = request.POST.get('preferred_language', 'hi')
        request.user.fishing_license_number = request.POST.get('fishing_license_number', '').strip()
        request.user.boat_registration = request.POST.get('boat_registration', '').strip()
        request.user.save()
        
        # Update profile
        profile.community_type = request.POST.get('community_type', '').strip()
        profile.occupation = request.POST.get('occupation', '').strip()
        profile.experience_years = int(request.POST.get('experience_years', 0) or 0)
        profile.address = request.POST.get('address', '').strip()
        profile.pincode = request.POST.get('pincode', '').strip()
        profile.bio = request.POST.get('bio', '').strip()
        
        # Handle date of birth
        dob = request.POST.get('date_of_birth')
        if dob:
            profile.date_of_birth = dob
        
        # Handle avatar upload
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']
        
        profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('home')
    
    return render(request, 'accounts/complete_profile.html', {
        'profile': profile
    })

@login_required
def dashboard_view(request):
    """
    Unified dashboard view with all sections and statistics
    """
    context = {
        'donation_count': 0,
        'membership_count': 0,
        'upcoming_events': 0,
        'pending_gatepasses': 0,
    }

    try:
        # Import models dynamically to avoid import errors if apps don't exist

        # Donations statistics
        try:
            from donations.models import Donation
            if request.user.is_authenticated:
                context['donation_count'] = Donation.objects.filter(user=request.user).count()
            else:
                context['donation_count'] = 0
        except ImportError:
            context['donation_count'] = 0

        # Membership statistics
        try:
            from membership.models import Membership
            if request.user.is_authenticated:
                context['membership_count'] = Membership.objects.filter(user=request.user, status='ACTIVE').count()
            else:
                context['membership_count'] = 0
        except ImportError:
            context['membership_count'] = 0

        # Campaigns/Events statistics
        try:
            from campaigns.models import Event, EventRegistration
            from django.utils import timezone

            # Count upcoming events
            context['upcoming_events'] = Event.objects.filter(
                date_time__gte=timezone.now()
            ).count()

            # User's event registrations
            if request.user.is_authenticated:
                context['my_registrations'] = EventRegistration.objects.filter(
                    user=request.user
                ).count()
            else:
                context['my_registrations'] = 0

        except ImportError:
            context['upcoming_events'] = 0
            context['my_registrations'] = 0

        # Gate pass statistics
        try:
            from gatepass.models import GatePass
            if request.user.is_authenticated:
                context['pending_gatepasses'] = GatePass.objects.filter(
                    user=request.user,
                    status='PENDING'
                ).count()
            else:
                context['pending_gatepasses'] = 0
        except ImportError:
            context['pending_gatepasses'] = 0

        # Assets statistics (for admin users)
        try:
            from assets.models import Asset, AssetRequest
            if request.user.is_authenticated and hasattr(request.user, 'user_type'):
                if request.user.user_type == 'ADMINISTRATOR':
                    context['total_assets'] = Asset.objects.count()
                    context['pending_asset_requests'] = AssetRequest.objects.filter(status='PENDING').count()
                else:
                    context['my_asset_requests'] = AssetRequest.objects.filter(user=request.user).count()
        except ImportError:
            pass

    except Exception as e:
        # Log error but don't break the page
        print(f"Error fetching dashboard statistics: {e}")

    return render(request, 'core/dashboard.html', context)

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('phone_login')

# Admin User Management Views
@login_required
def admin_user_list(request):
    """Admin view to manage all users"""
    if request.user.user_type != 'ADMINISTRATOR':
        messages.error(request, _('You do not have permission to view this page.'))
        return redirect('home')
    
    # Get search and filter parameters
    search_query = request.GET.get('search', '')
    user_type_filter = request.GET.get('user_type', '')
    
    # Base queryset
    users = User.objects.select_related('userprofile').exclude(id=request.user.id)
    
    # Apply filters
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    if user_type_filter:
        users = users.filter(user_type=user_type_filter)
    
    # Order by creation date
    users = users.order_by('-date_joined')
    
    # Paginate
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get user type choices for filter dropdown
    user_types = USER_TYPE_CHOICES
    
    context = {
        'page_obj': page_obj,
        'users': page_obj,
        'user_types': user_types,
        'search_query': search_query,
        'user_type_filter': user_type_filter,
        'total_users': users.count(),
    }
    return render(request, 'accounts/admin_user_list.html', context)

@login_required
def admin_change_user_type(request, user_id):
    """Admin function to change user type"""
    if request.user.user_type != 'ADMINISTRATOR':
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    
    user = get_object_or_404(User, id=user_id)
    
    # Prevent admin from changing their own type
    if user == request.user:
        return JsonResponse({'status': 'error', 'message': 'You cannot change your own user type'}, status=400)
    
    if request.method == 'POST':
        new_user_type = request.POST.get('user_type')
        
        # Validate user type
        valid_types = [choice[0] for choice in USER_TYPE_CHOICES]
        if new_user_type not in valid_types:
            return JsonResponse({'status': 'error', 'message': 'Invalid user type'}, status=400)
        
        # Update user type
        old_type = user.get_user_type_display()
        user.user_type = new_user_type
        user.save()
        
        new_type = user.get_user_type_display()
        
        messages.success(request, f'{user.get_full_name()}\'s user type changed from {old_type} to {new_type}.')
        
        return JsonResponse({
            'status': 'success', 
            'message': 'User type updated successfully',
            'new_type': new_type,
            'new_type_code': new_user_type
        })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@login_required 
def admin_user_detail(request, user_id):
    """Admin view to see detailed user information"""
    if request.user.user_type != 'ADMINISTRATOR':
        messages.error(request, _('You do not have permission to view this page.'))
        return redirect('home')
    
    user = get_object_or_404(User, id=user_id)
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Get user's activity data
    from membership.models import Membership
    from donations.models import Donation
    from campaigns.models import EventAttendance
    
    memberships = Membership.objects.filter(user=user).order_by('-created_at')[:5]
    donations = Donation.objects.filter(donor=user).order_by('-created_at')[:5]
    events = EventAttendance.objects.filter(attendee=user).select_related('event').order_by('-registered_at')[:5]
    
    context = {
        'profile_user': user,  # Renamed to avoid confusion with request.user
        'profile': profile,
        'memberships': memberships,
        'donations': donations,
        'events': events,
        'user_types': USER_TYPE_CHOICES,
    }
    return render(request, 'accounts/admin_user_detail.html', context)

@login_required
def admin_toggle_user_status(request, user_id):
    """Admin function to activate/deactivate user"""
    if request.user.user_type != 'ADMINISTRATOR':
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    
    user = get_object_or_404(User, id=user_id)
    
    # Prevent admin from deactivating themselves
    if user == request.user:
        return JsonResponse({'status': 'error', 'message': 'You cannot deactivate your own account'}, status=400)
    
    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save()
        
        status = 'active' if user.is_active else 'inactive'
        messages.success(request, f'{user.get_full_name()}\'s account has been {status}.')
        
        return JsonResponse({
            'status': 'success',
            'message': f'User successfully {"activated" if user.is_active else "deactivated"}',
            'is_active': user.is_active
        })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
