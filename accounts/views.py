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
        return redirect('complete_profile')
    
    return render(request, 'accounts/complete_profile.html', {
        'profile': profile
    })

@login_required
def dashboard_view(request):
    """
    Main single-page dashboard view - shows all information on one page
    """
    from django.utils import timezone
    from django.db.models import Sum
    from decimal import Decimal

    context = {
        'today': timezone.now(),
    }

    # Initialize stats
    stats = {
        'total_donations': 0,
        'donations_amount': Decimal('0.00'),
        'total_members': 0,
        'new_members': 0,
        'total_events': 0,
        'upcoming_events': 0,
        'total_assets': 0,
        'available_assets': 0,
    }

    # Get Donations stats
    try:
        from donations.models import Donation
        user_donations = Donation.objects.filter(donor=request.user, status='SUCCESS')
        stats['total_donations'] = user_donations.count()
        stats['donations_amount'] = user_donations.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        context['recent_donations'] = user_donations.order_by('-created_at')[:5]
    except:
        context['recent_donations'] = []

    # Get Membership stats
    try:
        from membership.models import Membership
        stats['total_members'] = Membership.objects.filter(is_active=True, verification_status='APPROVED').count()
        # New members this month
        stats['new_members'] = Membership.objects.filter(
            created_at__gte=timezone.now().replace(day=1)
        ).count()
        context['user_membership'] = Membership.objects.filter(user=request.user, is_active=True).first()
    except:
        context['user_membership'] = None

    # Get Events stats
    try:
        from campaigns.models import Event, EventAttendance
        stats['total_events'] = Event.objects.count()
        stats['upcoming_events'] = Event.objects.filter(date_time__gte=timezone.now()).count()
        context['upcoming_events'] = Event.objects.filter(
            date_time__gte=timezone.now(),
            is_public=True
        ).select_related('campaign').order_by('date_time')[:5]

        # User's registered events
        user_registrations = EventAttendance.objects.filter(
            attendee=request.user
        ).values_list('event_id', flat=True)
    except:
        context['upcoming_events'] = []

    # Get Assets stats
    try:
        from assets.models import Asset
        stats['total_assets'] = Asset.objects.count()
        stats['available_assets'] = Asset.objects.filter(status='AVAILABLE').count()
    except:
        pass

    # Recent activities (mock data - you can customize this)
    context['recent_activities'] = [
        {
            'title': 'Welcome to your dashboard!',
            'created_at': timezone.now(),
            'color': 'stat-icon blue',
            'icon': 'bi-star-fill'
        }
    ]

    context['stats'] = stats

    return render(request, 'core/main_dashboard.html', context)

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

    # Get active and inactive user counts
    total_users_count = User.objects.exclude(id=request.user.id).count()
    active_users_count = User.objects.exclude(id=request.user.id).filter(is_active=True).count()
    inactive_users_count = User.objects.exclude(id=request.user.id).filter(is_active=False).count()

    context = {
        'page_obj': page_obj,
        'users': page_obj,
        'user_types': user_types,
        'search_query': search_query,
        'user_type_filter': user_type_filter,
        'total_users': total_users_count,
        'active_users': active_users_count,
        'inactive_users': inactive_users_count,
        'paginator': paginator,
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

@login_required
def dashboard_user_management_content(request):
    """Return user management dashboard content for AJAX loading"""
    # Check if user is admin
    if request.user.user_type != 'ADMINISTRATOR':
        return render(request, 'accounts/dashboard_content_denied.html')

    # Get user statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = User.objects.filter(is_active=False).count()

    # Count by user types
    administrators = User.objects.filter(user_type='ADMINISTRATOR').count()
    members = User.objects.filter(user_type='MEMBER').count()
    volunteers = User.objects.filter(user_type='VOLUNTEER').count()
    supporters = User.objects.filter(user_type='SUPPORTER').count()

    # Recent users (last 10)
    recent_users = User.objects.select_related('userprofile').order_by('-date_joined')[:10]

    # Recently updated users
    recently_updated = User.objects.select_related('userprofile').order_by('-last_login')[:10]

    context = {
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'administrators': administrators,
        'members': members,
        'volunteers': volunteers,
        'supporters': supporters,
        'recent_users': recent_users,
        'recently_updated': recently_updated,
        'user_types': USER_TYPE_CHOICES,
    }
    return render(request, 'accounts/dashboard_content.html', context)
