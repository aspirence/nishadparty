from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.db import models
from decimal import Decimal
import json

from .models import Donation, DonationCampaign, RecurringDonation
from accounts.models import User

def donation_home(request):
    """Display donation campaigns and options"""
    active_campaigns = DonationCampaign.objects.filter(is_active=True, end_date__gte=timezone.now().date())
    
    # Check if user is admin to determine what donations to show
    if request.user.is_authenticated and request.user.user_type == 'ADMINISTRATOR':
        # Admin can see all donations
        recent_donations = Donation.objects.filter(status='SUCCESS', anonymous=False).select_related('donor')[:5]
        total_raised = Donation.objects.filter(status='SUCCESS').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        is_admin_view = True
    elif request.user.is_authenticated:
        # Regular users can only see their own donations (including anonymous ones)
        recent_donations = Donation.objects.filter(
            donor=request.user
        ).select_related('donor').order_by('-created_at')[:5]
        total_raised = Donation.objects.filter(
            donor=request.user
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')
        is_admin_view = False
    else:
        # Non-authenticated users see no donations data
        recent_donations = Donation.objects.none()
        total_raised = Decimal('0.00')
        is_admin_view = False
    
    context = {
        'campaigns': active_campaigns,
        'recent_donations': recent_donations,
        'total_raised': total_raised,
        'is_admin_view': is_admin_view,
    }
    return render(request, 'donations/home.html', context)

def donate_form(request, campaign_id=None):
    """Display donation form"""
    campaign = None
    if campaign_id:
        campaign = get_object_or_404(DonationCampaign, id=campaign_id, is_active=True)
    
    if request.method == 'POST':
        # Get form data
        donor_name = request.POST.get('donor_name', '').strip()
        donor_email = request.POST.get('donor_email', '').strip()
        donor_phone = request.POST.get('donor_phone', '').strip()
        donor_address = request.POST.get('donor_address', '').strip()
        donor_pan = request.POST.get('donor_pan', '').strip().upper()
        amount = Decimal(request.POST.get('amount', '0'))
        payment_method = request.POST.get('payment_method', 'ONLINE')
        purpose = request.POST.get('purpose', '').strip()
        anonymous = request.POST.get('anonymous') == 'on'
        
        # Validation
        if not donor_name or not donor_email or not donor_phone or amount <= 0:
            messages.error(request, _('Please fill in all required information'))
            return render(request, 'donations/donate.html', {'campaign': campaign})
        
        # Check PAN requirement for amounts >= 2000
        if amount >= 2000 and not donor_pan:
            messages.error(request, _('PAN card number is required for donations of ₹2000 or more'))
            return render(request, 'donations/donate.html', {'campaign': campaign})
        
        # Create donation record
        donation = Donation.objects.create(
            donor=request.user if request.user.is_authenticated else None,
            donor_name=donor_name,
            donor_email=donor_email,
            donor_phone=donor_phone,
            donor_address=donor_address,
            donor_pan=donor_pan,
            amount=amount,
            payment_method=payment_method,
            purpose=purpose or (campaign.title if campaign else ''),
            anonymous=anonymous,
            constituency=request.POST.get('constituency', '')
        )
        
        if payment_method == 'ONLINE':
            # For now, mark as success (in real implementation, integrate with payment gateway)
            donation.status = 'SUCCESS'
            donation.save()
            
            # Update campaign amount if applicable
            if campaign:
                campaign.raised_amount += amount
                campaign.save()
            
            messages.success(request, _('Donation received successfully. Thank you!'))
            return redirect('donations:receipt', donation_id=donation.id)
        else:
            messages.info(request, _('Your donation has been registered. Please follow the instructions.'))
            return redirect('donations:payment_instructions', donation_id=donation.id)
    
    context = {
        'campaign': campaign,
    }
    return render(request, 'donations/donate.html', context)

def donation_receipt(request, donation_id):
    """Display donation receipt"""
    donation = get_object_or_404(Donation, id=donation_id, status='SUCCESS')
    
    context = {
        'donation': donation,
    }
    return render(request, 'donations/receipt.html', context)

def payment_instructions(request, donation_id):
    """Display payment instructions for offline payments"""
    donation = get_object_or_404(Donation, id=donation_id)
    
    context = {
        'donation': donation,
    }
    return render(request, 'donations/payment_instructions.html', context)

@login_required
def my_donations(request):
    """Display user's donation history"""
    donations = Donation.objects.filter(
        donor=request.user
    ).order_by('-created_at')
    
    total_donated = donations.filter(status='SUCCESS').aggregate(
        total=models.Sum('amount')
    )['total'] or Decimal('0.00')
    
    context = {
        'donations': donations,
        'total_donated': total_donated,
    }
    return render(request, 'donations/my_donations.html', context)
