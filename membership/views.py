from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.utils.translation import gettext as _
import qrcode
import io
import base64
import uuid as uuid_lib

from .models import MembershipTier, Membership, DocumentVerification, MembershipApplicationSteps
from accounts.models import User

@login_required
def membership_home(request):
    """Display membership options and current membership status"""
    user_membership = Membership.objects.filter(user=request.user, is_active=True).first()
    membership_tiers = MembershipTier.objects.filter(is_active=True)
    
    context = {
        'user_membership': user_membership,
        'membership_tiers': membership_tiers,
    }
    return render(request, 'membership/home.html', context)

@login_required
def apply_membership(request, tier_id):
    """Apply for membership with selected tier"""
    tier = get_object_or_404(MembershipTier, id=tier_id, is_active=True)
    
    # Check if user already has active membership
    existing_membership = Membership.objects.filter(user=request.user, is_active=True).first()
    if existing_membership and not existing_membership.is_expired:
        messages.warning(request, _('You already have an active membership.'))
        return redirect('membership:home')
    
    if request.method == 'POST':
        # Create membership application
        end_date = timezone.now().date() + timedelta(days=tier.duration_months * 30)
        
        membership = Membership.objects.create(
            user=request.user,
            tier=tier,
            start_date=timezone.now().date(),
            end_date=end_date,
            verification_status='PENDING'
        )
        
        # Create application steps tracker
        MembershipApplicationSteps.objects.create(membership=membership)
        
        messages.success(request, _('Membership application submitted successfully. You can now upload documents.'))
        return redirect('membership:application_status', membership_id=membership.id)
    
    context = {
        'tier': tier,
    }
    return render(request, 'membership/apply.html', context)

@login_required
def application_status(request, membership_id):
    """View membership application status and upload documents"""
    membership = get_object_or_404(Membership, id=membership_id, user=request.user)
    app_steps, created = MembershipApplicationSteps.objects.get_or_create(membership=membership)
    documents = DocumentVerification.objects.filter(membership=membership)
    
    if request.method == 'POST':
        # Handle document upload
        document_type = request.POST.get('document_type')
        document_number = request.POST.get('document_number', '')
        
        if 'document_file' in request.FILES and document_type:
            # Remove existing document of same type
            DocumentVerification.objects.filter(
                membership=membership, 
                document_type=document_type
            ).delete()
            
            # Create new document
            DocumentVerification.objects.create(
                membership=membership,
                document_type=document_type,
                document_file=request.FILES['document_file'],
                document_number=document_number
            )
            
            messages.success(request, _('Document uploaded successfully.'))
            return redirect('membership:application_status', membership_id=membership.id)
    
    context = {
        'membership': membership,
        'app_steps': app_steps,
        'documents': documents,
        'document_choices': DocumentVerification._meta.get_field('document_type').choices,
    }
    return render(request, 'membership/application_status.html', context)

@login_required
def apply_membership_with_payment(request):
    """Handle new membership application with custom payment amount"""
    # Check if user already has active membership
    existing_membership = Membership.objects.filter(user=request.user, is_active=True).first()
    if existing_membership and not existing_membership.is_expired:
        messages.warning(request, _('You already have an active membership.'))
        return redirect('membership:home')

    if request.method == 'POST':
        # Get form data
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        occupation = request.POST.get('occupation', '').strip()
        address = request.POST.get('address', '').strip()
        amount = request.POST.get('amount', '')

        # Validate required fields
        if not all([full_name, phone, email, occupation, address, amount]):
            messages.error(request, _('All fields are required.'))
            return redirect('membership:home')

        try:
            amount = float(amount)
            if amount < 50:
                messages.error(request, _('Minimum membership amount is ₹50.'))
                return redirect('membership:home')
        except (ValueError, TypeError):
            messages.error(request, _('Invalid amount entered.'))
            return redirect('membership:home')

        # Create membership application
        end_date = timezone.now().date() + timedelta(days=365)  # 12 months

        membership = Membership.objects.create(
            user=request.user,
            start_date=timezone.now().date(),
            end_date=end_date,
            amount_paid=amount,
            verification_status='PENDING',
            full_name=full_name,
            phone=phone,
            email=email,
            occupation=occupation,
            address=address
        )

        # Create application steps tracker
        MembershipApplicationSteps.objects.create(membership=membership)

        messages.success(request, _('Membership application created. Please proceed with payment.'))
        return redirect('membership:payment', membership_id=membership.id)

    return redirect('membership:home')

@login_required
def payment_page(request, membership_id):
    """Display QR code payment page"""
    membership = get_object_or_404(Membership, id=membership_id, user=request.user)

    # Generate dummy QR code for payment
    payment_id = str(uuid_lib.uuid4())[:8].upper()
    membership.payment_id = payment_id
    membership.save()

    # Create QR code data
    qr_data = f"UPI://pay?pa=nishadparty@upi&pn=Nishad%20Party&mc=0000&tid={payment_id}&tr={membership.membership_id}&tn=Membership%20Payment&am={membership.amount_paid}&cu=INR"

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    # Create QR code image
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64 for template
    buffer = io.BytesIO()
    qr_img.save(buffer, format='PNG')
    buffer.seek(0)
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()

    context = {
        'membership': membership,
        'payment_id': payment_id,
        'qr_code_base64': qr_code_base64,
    }
    return render(request, 'membership/payment.html', context)

@login_required
def payment_complete(request, membership_id):
    """Handle payment completion (dummy implementation)"""
    membership = get_object_or_404(Membership, id=membership_id, user=request.user)

    if request.method == 'POST':
        # In a real implementation, you would verify payment here
        # For demo purposes, we'll just mark as completed

        # Update application steps
        app_steps, created = MembershipApplicationSteps.objects.get_or_create(membership=membership)
        app_steps.payment_completed = True
        app_steps.current_step = 2  # Move to document upload step
        app_steps.save()

        messages.success(request, _('Payment completed successfully! Please upload your documents to complete the application.'))
        return redirect('membership:application_status', membership_id=membership.id)

    return redirect('membership:payment', membership_id=membership_id)

@login_required
def membership_card(request):
    """Display digital membership card"""
    try:
        membership = Membership.objects.get(
            user=request.user,
            is_active=True,
            verification_status='APPROVED'
        )
        context = {
            'membership': membership,
            'has_membership': True,
        }
    except Membership.DoesNotExist:
        # Check if user has any membership (pending/rejected)
        pending_membership = Membership.objects.filter(
            user=request.user
        ).order_by('-created_at').first()

        context = {
            'membership': None,
            'has_membership': False,
            'pending_membership': pending_membership,
        }

    return render(request, 'membership/card.html', context)
