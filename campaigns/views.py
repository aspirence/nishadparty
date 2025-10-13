from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.utils.translation import gettext as _
from datetime import datetime, timedelta
import calendar
from collections import defaultdict

from .models import Event, EventAttendance, Campaign
from accounts.models import User

def admin_required(user):
    """Check if user is an administrator"""
    return user.is_authenticated and user.user_type == 'ADMINISTRATOR'

def events_calendar(request):
    """Display events calendar view"""
    # Get current month/year or from request
    current_date = timezone.now().date()
    year = int(request.GET.get('year', current_date.year))
    month = int(request.GET.get('month', current_date.month))
    
    # Get events for the month
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
    
    events = Event.objects.filter(
        date_time__date__gte=start_date,
        date_time__date__lte=end_date,
        is_public=True
    ).select_related('campaign', 'contact_person').order_by('date_time')
    
    # Group events by date
    events_by_date = defaultdict(list)
    for event in events:
        events_by_date[event.date_time.date()].append(event)
    
    # Generate calendar data
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    
    # Navigation dates
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    context = {
        'calendar_weeks': cal,
        'events_by_date': dict(events_by_date),
        'year': year,
        'month': month,
        'month_name': month_name,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'current_date': current_date,
        'upcoming_events': events.filter(date_time__gte=timezone.now())[:5],
    }
    return render(request, 'campaigns/calendar.html', context)

def events_list(request):
    """Display events list view"""
    # Filter options
    event_type = request.GET.get('type')
    constituency = request.GET.get('constituency')
    search = request.GET.get('search')
    
    events = Event.objects.filter(
        is_public=True,
        date_time__gte=timezone.now()
    ).select_related('campaign', 'contact_person')
    
    if event_type:
        events = events.filter(event_type=event_type)
    
    if constituency:
        events = events.filter(campaign__constituency__icontains=constituency)
    
    if search:
        events = events.filter(
            title__icontains=search
        )
    
    events = events.order_by('date_time')
    
    # Get filter options
    event_types = Event._meta.get_field('event_type').choices
    constituencies = Event.objects.filter(is_public=True).values_list(
        'campaign__constituency', flat=True
    ).distinct().exclude(campaign__constituency__isnull=True)
    
    context = {
        'events': events,
        'event_types': event_types,
        'constituencies': constituencies,
        'selected_type': event_type,
        'selected_constituency': constituency,
        'search_query': search,
    }
    return render(request, 'campaigns/events_list.html', context)

def event_detail(request, event_slug):
    """Display event details"""
    event = get_object_or_404(Event, slug=event_slug, is_public=True)
    
    # Check if user is registered
    user_registered = False
    user_attendance = None
    if request.user.is_authenticated:
        try:
            user_attendance = EventAttendance.objects.get(
                event=event, 
                attendee=request.user
            )
            user_registered = True
        except EventAttendance.DoesNotExist:
            pass
    
    # Get attendee count
    registered_count = event.attendees.count()

    # Calculate available seats
    if event.max_attendees > 0:
        available_seats = event.max_attendees - registered_count
    else:
        available_seats = None  # Unlimited

    context = {
        'event': event,
        'user_registered': user_registered,
        'user_attendance': user_attendance,
        'registered_count': registered_count,
        'available_seats': available_seats,
        'can_register': (
            request.user.is_authenticated and
            not user_registered and
            event.is_registration_open and
            (event.max_attendees == 0 or registered_count < event.max_attendees)
        ),
    }
    return render(request, 'campaigns/event_detail.html', context)

@login_required
def event_register(request, event_slug):
    """Register for an event"""
    event = get_object_or_404(Event, slug=event_slug, is_public=True)
    
    # Check if registration is open
    if not event.is_registration_open:
        messages.error(request, _('Registration for this event is closed.'))
        return redirect('campaigns:event_detail', event_slug=event_slug)
    
    # Check if already registered
    if EventAttendance.objects.filter(event=event, attendee=request.user).exists():
        messages.warning(request, _('You are already registered for this event.'))
        return redirect('campaigns:event_detail', event_slug=event_slug)
    
    # Check capacity
    if event.max_attendees > 0 and event.attendees.count() >= event.max_attendees:
        messages.error(request, _('This event is fully booked.'))
        return redirect('campaigns:event_detail', event_slug=event_slug)
    
    if request.method == 'POST':
        special_requirements = request.POST.get('special_requirements', '').strip()
        
        EventAttendance.objects.create(
            event=event,
            attendee=request.user,
            special_requirements=special_requirements
        )
        
        messages.success(request, _('You have successfully registered for the event.'))
        return redirect('campaigns:event_detail', event_slug=event_slug)
    
    context = {
        'event': event,
    }
    return render(request, 'campaigns/event_register.html', context)

@login_required
def my_events(request):
    """Display user's registered events"""
    attendances = EventAttendance.objects.filter(
        attendee=request.user
    ).select_related('event', 'event__campaign').order_by('-event__date_time')
    
    upcoming = attendances.filter(event__date_time__gte=timezone.now())
    past = attendances.filter(event__date_time__lt=timezone.now())
    
    context = {
        'upcoming_events': upcoming,
        'past_events': past,
    }
    return render(request, 'campaigns/my_events.html', context)

@login_required
def admin_events_dashboard(request):
    """Admin dashboard for event management"""
    if not admin_required(request.user):
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('campaigns:events_list')
    
    # Get event statistics
    total_events = Event.objects.count()
    upcoming_events = Event.objects.filter(date_time__gte=timezone.now()).count()
    ongoing_events = Event.objects.filter(status='ONGOING').count()
    completed_events = Event.objects.filter(status='COMPLETED').count()
    
    # Recent events
    recent_events = Event.objects.select_related('campaign', 'contact_person').order_by('-created_at')[:10]
    
    # Upcoming events that need attention
    upcoming_events_list = Event.objects.filter(
        date_time__gte=timezone.now(),
        status='SCHEDULED'
    ).select_related('campaign', 'contact_person').order_by('date_time')[:5]
    
    context = {
        'total_events': total_events,
        'upcoming_events': upcoming_events,
        'ongoing_events': ongoing_events,
        'completed_events': completed_events,
        'recent_events': recent_events,
        'upcoming_events_list': upcoming_events_list,
    }
    return render(request, 'campaigns/admin_events_dashboard.html', context)

@login_required
def admin_add_event(request):
    """Admin function to add new event"""
    if not admin_required(request.user):
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('campaigns:events_list')
    
    if request.method == 'POST':
        try:
            # Get form data
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            event_type = request.POST.get('event_type', '')
            date_time = request.POST.get('date_time', '')
            end_time = request.POST.get('end_time', '')
            venue = request.POST.get('venue', '').strip()
            address = request.POST.get('address', '').strip()
            max_attendees = request.POST.get('max_attendees', '0')
            registration_required = request.POST.get('registration_required') == 'on'
            registration_deadline = request.POST.get('registration_deadline', '')
            is_public = request.POST.get('is_public') == 'on'
            contact_phone = request.POST.get('contact_phone', '').strip()
            requirements = request.POST.get('requirements', '').strip()
            estimated_cost = request.POST.get('estimated_cost', '0')
            campaign_id = request.POST.get('campaign_id', '')
            
            # Validation
            if not title or not event_type or not date_time or not venue:
                messages.error(request, _('Please fill in all required information.'))
                return render(request, 'campaigns/admin_add_event.html', {'campaigns': Campaign.objects.all()})
            
            # Get campaign if specified
            campaign = None
            if campaign_id:
                try:
                    campaign = Campaign.objects.get(id=campaign_id)
                except Campaign.DoesNotExist:
                    pass
            
            # Create event
            event = Event.objects.create(
                title=title,
                description=description,
                event_type=event_type,
                date_time=date_time,
                end_time=end_time if end_time else None,
                venue=venue,
                address=address,
                max_attendees=int(max_attendees) if max_attendees else 0,
                registration_required=registration_required,
                registration_deadline=registration_deadline if registration_deadline else None,
                is_public=is_public,
                contact_person=request.user,
                contact_phone=contact_phone,
                requirements=requirements,
                estimated_cost=estimated_cost if estimated_cost else 0,
                campaign=campaign,
                created_by=request.user,
                status='SCHEDULED'
            )
            
            # Handle image upload
            if 'image' in request.FILES:
                event.image = request.FILES['image']
                event.save()
            
            messages.success(request, _('Event added successfully.'))
            return redirect('campaigns:admin_events_dashboard')
            
        except Exception as e:
            messages.error(request, _('Error occurred while adding event.'))
            return render(request, 'campaigns/admin_add_event.html', {'campaigns': Campaign.objects.all()})
    
    campaigns = Campaign.objects.all()
    return render(request, 'campaigns/admin_add_event.html', {'campaigns': campaigns})

@login_required
def admin_edit_event(request, event_id):
    """Admin function to edit existing event"""
    if not admin_required(request.user):
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('campaigns:events_list')
    
    event = get_object_or_404(Event, id=event_id)
    
    if request.method == 'POST':
        try:
            # Update event data
            event.title = request.POST.get('title', '').strip()
            event.description = request.POST.get('description', '').strip()
            event.event_type = request.POST.get('event_type', '')
            event.date_time = request.POST.get('date_time', '')
            
            end_time = request.POST.get('end_time', '')
            event.end_time = end_time if end_time else None
            
            event.venue = request.POST.get('venue', '').strip()
            event.address = request.POST.get('address', '').strip()
            
            max_attendees = request.POST.get('max_attendees', '0')
            event.max_attendees = int(max_attendees) if max_attendees else 0
            
            event.registration_required = request.POST.get('registration_required') == 'on'
            
            registration_deadline = request.POST.get('registration_deadline', '')
            event.registration_deadline = registration_deadline if registration_deadline else None
            
            event.is_public = request.POST.get('is_public') == 'on'
            event.contact_phone = request.POST.get('contact_phone', '').strip()
            event.requirements = request.POST.get('requirements', '').strip()
            
            estimated_cost = request.POST.get('estimated_cost', '0')
            event.estimated_cost = estimated_cost if estimated_cost else 0
            
            event.status = request.POST.get('status', 'SCHEDULED')
            
            campaign_id = request.POST.get('campaign_id', '')
            if campaign_id:
                try:
                    event.campaign = Campaign.objects.get(id=campaign_id)
                except Campaign.DoesNotExist:
                    event.campaign = None
            else:
                event.campaign = None
            
            # Handle image upload
            if 'image' in request.FILES:
                event.image = request.FILES['image']
            
            event.save()
            
            messages.success(request, _('Event updated successfully.'))
            return redirect('campaigns:admin_events_dashboard')
            
        except Exception as e:
            messages.error(request, _('Error occurred while updating event.'))
    
    campaigns = Campaign.objects.all()
    context = {
        'event': event,
        'campaigns': campaigns,
    }
    return render(request, 'campaigns/admin_edit_event.html', context)

@login_required
def admin_delete_event(request, event_id):
    """Admin function to delete event"""
    if not admin_required(request.user):
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('campaigns:events_list')

    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        event_title = event.title
        event.delete()
        messages.success(request, _('Event "{}" deleted successfully.'.format(event_title)))
        return redirect('campaigns:admin_events_dashboard')

    context = {
        'event': event,
    }
    return render(request, 'campaigns/admin_delete_event.html', context)

@login_required
def dashboard_campaigns_content(request):
    """Dashboard content view for campaigns section"""
    # Get event statistics
    total_events = Event.objects.filter(is_public=True).count()
    upcoming_events_count = Event.objects.filter(
        is_public=True,
        date_time__gte=timezone.now()
    ).count()

    # Get user's registered events
    user_registered_events = EventAttendance.objects.filter(
        attendee=request.user
    ).select_related('event', 'event__campaign')

    registered_events_count = user_registered_events.count()

    # Get upcoming registered events
    upcoming_registered = user_registered_events.filter(
        event__date_time__gte=timezone.now()
    ).order_by('event__date_time')[:5]

    # Get past registered events
    past_registered = user_registered_events.filter(
        event__date_time__lt=timezone.now()
    ).order_by('-event__date_time')[:5]

    # Get upcoming public events (not registered yet)
    upcoming_public_events = Event.objects.filter(
        is_public=True,
        date_time__gte=timezone.now()
    ).exclude(
        id__in=user_registered_events.values_list('event_id', flat=True)
    ).select_related('campaign', 'contact_person').order_by('date_time')[:5]

    context = {
        'total_events': total_events,
        'upcoming_events_count': upcoming_events_count,
        'registered_events_count': registered_events_count,
        'upcoming_registered': upcoming_registered,
        'past_registered': past_registered,
        'upcoming_public_events': upcoming_public_events,
    }
    return render(request, 'campaigns/dashboard_content.html', context)

@login_required
def dashboard_event_management_content(request):
    """Return event management dashboard content for AJAX loading (Admin only)"""
    # Check if user is admin
    if not admin_required(request.user):
        return render(request, 'campaigns/dashboard_content_denied.html')

    # Get event statistics
    total_events = Event.objects.count()
    upcoming_events = Event.objects.filter(date_time__gte=timezone.now()).count()
    ongoing_events = Event.objects.filter(status='ONGOING').count()
    completed_events = Event.objects.filter(status='COMPLETED').count()
    cancelled_events = Event.objects.filter(status='CANCELLED').count()

    # Get total registrations
    total_registrations = EventAttendance.objects.filter(status='CONFIRMED').count()
    pending_registrations = EventAttendance.objects.filter(status='REGISTERED').count()

    # Recent events
    recent_events = Event.objects.select_related('campaign', 'contact_person').order_by('-created_at')[:5]

    # Upcoming events that need attention
    upcoming_events_list = Event.objects.filter(
        date_time__gte=timezone.now(),
        status='SCHEDULED'
    ).select_related('campaign', 'contact_person').order_by('date_time')[:5]

    # Events with most registrations
    popular_events = Event.objects.filter(
        date_time__gte=timezone.now()
    ).select_related('campaign', 'contact_person').order_by('-eventattendance__id')[:5]

    context = {
        'total_events': total_events,
        'upcoming_events': upcoming_events,
        'ongoing_events': ongoing_events,
        'completed_events': completed_events,
        'cancelled_events': cancelled_events,
        'total_registrations': total_registrations,
        'pending_registrations': pending_registrations,
        'recent_events': recent_events,
        'upcoming_events_list': upcoming_events_list,
        'popular_events': popular_events,
    }
    return render(request, 'campaigns/event_management_dashboard_content.html', context)
