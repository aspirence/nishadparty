from django.shortcuts import render
from django.http import JsonResponse
from django.utils.translation import get_language, activate
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from .models import YouTubeVideo
import json

# Import content models
try:
    from content.models import Photo, Video, Article
except ImportError:
    Photo = Video = Article = None

def home_view(request):
    """
    Home page view - shows home page for all users (authenticated and non-authenticated)
    """
    # Get active YouTube videos for homepage
    youtube_videos = YouTubeVideo.objects.filter(is_active=True)[:6]  # Limit to 6 videos

    context = {
        'youtube_videos': youtube_videos
    }

    return render(request, 'core/home.html', context)

def change_language_view(request):
    """
    AJAX view to change language
    """
    if request.method == 'POST':
        try:
            # Handle both JSON and form data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                language = data.get('language', 'hi')
            else:
                language = request.POST.get('language', 'hi')
            
            # Validate language
            from django.conf import settings
            if language in [lang[0] for lang in settings.LANGUAGES]:
                # Set language in session
                request.session['django_language'] = language
                # Activate for current request
                activate(language)
                
                return JsonResponse({
                    'status': 'success',
                    'message': f'Language changed to {language}',
                    'language': language,
                    'reload': True
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid language selected'
                })
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': 'Error changing language'
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'Only POST requests allowed'
    })

def about_view(request):
    return render(request, 'core/about.html')

def leadership_view(request):
    return render(request, 'core/leadership.html')

def vision_view(request):
    return render(request, 'core/vision.html')

def photo_gallery_view(request):
    context = {}
    if Photo:
        # Get filter category from query parameter
        category = request.GET.get('category', 'all')

        # Base queryset
        photos = Photo.objects.filter(is_published=True)

        # Apply category filter
        if category != 'all':
            photos = photos.filter(category=category.upper())

        # Get photos and featured photo
        featured_photo = photos.filter(is_featured=True).first()
        photos_list = photos.order_by('-created_at')[:12]

        # Get statistics
        stats = {
            'total_photos': Photo.objects.filter(is_published=True).count(),
            'events_covered': Photo.objects.filter(is_published=True, category='EVENTS').count(),
            'campaigns': Photo.objects.filter(is_published=True, category='CAMPAIGNS').count(),
            'community_visits': Photo.objects.filter(is_published=True, category='COMMUNITY').count(),
        }

        context = {
            'photos': photos_list,
            'featured_photo': featured_photo,
            'stats': stats,
            'current_category': category,
        }

    return render(request, 'core/photo_gallery.html', context)

def video_gallery_view(request):
    context = {}
    if Video:
        # Get filter category from query parameter
        category = request.GET.get('category', 'all')

        # Base queryset
        videos = Video.objects.filter(is_published=True)

        # Apply category filter
        if category != 'all':
            videos = videos.filter(category=category.upper())

        # Get videos and featured video
        featured_video = videos.filter(is_featured=True).first()
        videos_list = videos.order_by('-created_at')[:12]

        # Get statistics
        stats = {
            'total_videos': Video.objects.filter(is_published=True).count(),
            'hours_content': Video.objects.filter(is_published=True).count() * 10,  # Estimate
            'speeches': Video.objects.filter(is_published=True, category='SPEECHES').count(),
            'documentaries': Video.objects.filter(is_published=True, category='DOCUMENTARIES').count(),
        }

        context = {
            'videos': videos_list,
            'featured_video': featured_video,
            'stats': stats,
            'current_category': category,
        }

    return render(request, 'core/video_gallery.html', context)

def news_view(request):
    context = {}
    if Article:
        # Get filter category from query parameter
        category = request.GET.get('category', 'all')

        # Base queryset
        articles = Article.objects.filter(is_published=True)

        # Apply category filter
        if category != 'all':
            if category == 'politics':
                articles = articles.filter(category__in=['POLICY', 'ANNOUNCEMENT'])
            elif category == 'community':
                articles = articles.filter(category__in=['COMMUNITY', 'FISHING'])
            elif category == 'achievements':
                articles = articles.filter(category='EVENTS')
            elif category == 'press':
                articles = articles.filter(category='PRESS_RELEASE')

        # Get articles and featured article
        featured_article = articles.filter(is_featured=True).first()
        articles_list = articles.order_by('-created_at')[:12]

        context = {
            'articles': articles_list,
            'featured_article': featured_article,
            'current_category': category,
        }

    return render(request, 'core/news.html', context)

def policies_view(request):
    return render(request, 'core/policies.html')

def contact_view(request):
    return render(request, 'core/contact.html')

def manifesto_view(request):
    return render(request, 'core/manifesto.html')

def privacy_policy_view(request):
    return render(request, 'core/privacy_policy.html')

def terms_view(request):
    return render(request, 'core/terms.html')

def sitemap_view(request):
    return render(request, 'core/sitemap.html')

def kejriwal_videos_api(request):
    """
    API endpoint to serve Kejriwal speaks videos data
    """
    try:
        # Get active YouTube videos for Kejriwal widget
        videos = YouTubeVideo.objects.filter(is_active=True).order_by('display_order', '-created_at')

        video_data = []
        for video in videos:
            video_data.append({
                'id': video.id,
                'title': video.title,
                'description': video.description,
                'youtube_url': video.youtube_url,
                'thumbnail': video.get_thumbnail_url(),
                'embed_url': video.get_embed_url(),
                'video_id': video.get_video_id(),
                'created_at': video.created_at.isoformat(),
                'is_featured': video.is_featured
            })

        return JsonResponse({
            'status': 'success',
            'videos': video_data,
            'total': len(video_data)
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'Unable to load videos',
            'error': str(e)
        }, status=500)

@login_required
def dashboard_view(request):
    """
    Unified dashboard view with all sections and statistics
    """
    # Ensure UserProfile exists for the user
    try:
        from accounts.models import UserProfile
        UserProfile.objects.get_or_create(user=request.user)
    except Exception as e:
        pass  # UserProfile might not exist in the app

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
                date__gte=timezone.now().date(),
                status='ACTIVE'
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

@login_required
def main_dashboard_view(request):
    """
    Main single-page dashboard view - shows all information on one page
    """
    from django.utils import timezone
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

    # Recent activities - different for admin and regular users
    recent_activities = []

    if request.user.user_type == 'ADMINISTRATOR':
        # Admin sees all activities across the platform
        try:
            from donations.models import Donation
            # Recent donations (all users)
            recent_donations = Donation.objects.select_related('donor').order_by('-created_at')[:5]
            for donation in recent_donations:
                donor_name = donation.donor.get_full_name() if donation.donor else "Anonymous"
                recent_activities.append({
                    'title': f'{donor_name} made a donation of ₹{donation.amount}',
                    'created_at': donation.created_at,
                    'color': 'red',
                    'icon': 'bi-heart-fill',
                    'type': 'donation'
                })
        except:
            pass

        try:
            from membership.models import Membership
            # Recent memberships (all users)
            recent_memberships = Membership.objects.select_related('user').order_by('-created_at')[:5]
            for membership in recent_memberships:
                user_name = membership.user.get_full_name()
                recent_activities.append({
                    'title': f'{user_name} joined as a member',
                    'created_at': membership.created_at,
                    'color': 'blue',
                    'icon': 'bi-person-plus-fill',
                    'type': 'membership'
                })
        except:
            pass

        try:
            from campaigns.models import EventAttendance
            # Recent event registrations (all users)
            recent_registrations = EventAttendance.objects.select_related('attendee', 'event').order_by('-registered_at')[:5]
            for reg in recent_registrations:
                user_name = reg.attendee.get_full_name()
                recent_activities.append({
                    'title': f'{user_name} registered for {reg.event.title}',
                    'created_at': reg.registered_at,
                    'color': 'green',
                    'icon': 'bi-calendar-check-fill',
                    'type': 'event'
                })
        except:
            pass

        try:
            from assets.models import AssetAssignment
            # Recent asset assignments (all users)
            recent_assignments = AssetAssignment.objects.select_related('asset', 'checked_out_by').order_by('-assignment_date')[:5]
            for assignment in recent_assignments:
                user_name = assignment.checked_out_by.get_full_name()
                recent_activities.append({
                    'title': f'{user_name} was assigned {assignment.asset.name}',
                    'created_at': assignment.assignment_date,
                    'color': 'orange',
                    'icon': 'bi-box-seam-fill',
                    'type': 'asset'
                })
        except:
            pass

    else:
        # Regular users see only their own activities
        try:
            from donations.models import Donation
            # User's recent donations
            user_donations = Donation.objects.filter(donor=request.user).order_by('-created_at')[:3]
            for donation in user_donations:
                recent_activities.append({
                    'title': f'You made a donation of ₹{donation.amount}',
                    'created_at': donation.created_at,
                    'color': 'red',
                    'icon': 'bi-heart-fill',
                    'type': 'donation'
                })
        except:
            pass

        try:
            from membership.models import Membership
            # User's membership
            user_membership = Membership.objects.filter(user=request.user).order_by('-created_at').first()
            if user_membership:
                recent_activities.append({
                    'title': f'You joined as a member',
                    'created_at': user_membership.created_at,
                    'color': 'blue',
                    'icon': 'bi-person-plus-fill',
                    'type': 'membership'
                })
        except:
            pass

        try:
            from campaigns.models import EventAttendance
            # User's recent event registrations
            user_registrations = EventAttendance.objects.filter(attendee=request.user).select_related('event').order_by('-registered_at')[:3]
            for reg in user_registrations:
                recent_activities.append({
                    'title': f'You registered for {reg.event.title}',
                    'created_at': reg.registered_at,
                    'color': 'green',
                    'icon': 'bi-calendar-check-fill',
                    'type': 'event'
                })
        except:
            pass

        try:
            from assets.models import AssetAssignment
            # User's recent asset assignments
            user_assignments = AssetAssignment.objects.filter(checked_out_by=request.user).select_related('asset').order_by('-assignment_date')[:3]
            for assignment in user_assignments:
                recent_activities.append({
                    'title': f'You were assigned {assignment.asset.name}',
                    'created_at': assignment.assignment_date,
                    'color': 'orange',
                    'icon': 'bi-box-seam-fill',
                    'type': 'asset'
                })
        except:
            pass

    # Sort all activities by date and limit to 10 most recent
    if recent_activities:
        recent_activities.sort(key=lambda x: x['created_at'], reverse=True)
        context['recent_activities'] = recent_activities[:10]
    else:
        # Show welcome message if no activities yet
        context['recent_activities'] = [
            {
                'title': 'Welcome to your dashboard! Start exploring the features.',
                'created_at': timezone.now(),
                'color': 'blue',
                'icon': 'bi-star-fill',
                'type': 'welcome'
            }
        ]

    context['stats'] = stats

    return render(request, 'core/main_dashboard.html', context)
