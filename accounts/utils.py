import random
import requests
from django.conf import settings
from django.utils import timezone
from .models import PhoneVerification

def generate_otp():
    return str(random.randint(100000, 999999))

def generate_default_otp():
    """
    Generate default OTP for testing purposes
    """
    return "123456"

def send_otp_sms(phone_number, otp_code):
    """
    Send OTP via SMS using MSG91 or Twilio
    Returns True if successful, False otherwise
    """
    try:
        # Using MSG91 for SMS
        if hasattr(settings, 'MSG91_AUTH_KEY') and settings.MSG91_AUTH_KEY:
            url = "https://api.msg91.com/api/v5/flow/"
            
            # Template message for OTP
            message = f"Your NISHAD Party verification code is: {otp_code}. This code will expire in 10 minutes. Do not share this with anyone."
            
            payload = {
                "template_id": settings.MSG91_DEFAULT_TEMPLATE if hasattr(settings, 'MSG91_DEFAULT_TEMPLATE') else None,
                "short_url": "0",
                "realTimeResponse": "1",
                "recipients": [
                    {
                        "mobiles": phone_number.replace('+91', ''),  # Remove country code for MSG91
                        "message": message,
                        "otp": otp_code
                    }
                ]
            }
            
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "authkey": settings.MSG91_AUTH_KEY
            }
            
            response = requests.post(url, json=payload, headers=headers)
            return response.status_code == 200
        
        # Fallback to Twilio
        elif hasattr(settings, 'TWILIO_ACCOUNT_SID') and settings.TWILIO_ACCOUNT_SID:
            from twilio.rest import Client
            
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            message = f"Your NISHAD Party verification code is: {otp_code}. This code will expire in 10 minutes."
            
            message = client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone_number if phone_number.startswith('+') else f'+91{phone_number}'
            )
            
            return message.sid is not None
        
        else:
            # For development, just print the OTP
            print(f"OTP for {phone_number}: {otp_code}")
            return True
            
    except Exception as e:
        print(f"Error sending OTP: {str(e)}")
        return False

def create_or_update_otp(phone_number):
    """
    Create or update OTP for phone number
    Returns the OTP code
    """
    otp_code = generate_otp()
    
    # Clean up expired OTPs
    PhoneVerification.objects.filter(
        phone_number=phone_number,
        expires_at__lt=timezone.now()
    ).delete()
    
    # Create or update OTP
    verification, created = PhoneVerification.objects.get_or_create(
        phone_number=phone_number,
        is_verified=False,
        defaults={
            'otp_code': otp_code,
            'expires_at': timezone.now() + timezone.timedelta(minutes=10)
        }
    )
    
    if not created:
        verification.otp_code = otp_code
        verification.expires_at = timezone.now() + timezone.timedelta(minutes=10)
        verification.attempts = 0
        verification.save()
    
    return otp_code

def create_or_update_otp_with_default(phone_number):
    """
    Create or update OTP for phone number with default OTP for testing
    Returns the OTP code (always 123456 for testing)
    """
    otp_code = generate_default_otp()  # Always use 123456 for testing
    
    # Clean up expired OTPs
    PhoneVerification.objects.filter(
        phone_number=phone_number,
        expires_at__lt=timezone.now()
    ).delete()
    
    # Create or update OTP
    verification, created = PhoneVerification.objects.get_or_create(
        phone_number=phone_number,
        is_verified=False,
        defaults={
            'otp_code': otp_code,
            'expires_at': timezone.now() + timezone.timedelta(minutes=10)
        }
    )
    
    if not created:
        verification.otp_code = otp_code
        verification.expires_at = timezone.now() + timezone.timedelta(minutes=10)
        verification.attempts = 0
        verification.save()
    
    print(f"[TESTING] OTP for {phone_number}: {otp_code}")
    return otp_code

def verify_otp(phone_number, otp_code):
    """
    Verify OTP for phone number
    Returns tuple (success: bool, message: str, verification: PhoneVerification or None)
    """
    try:
        verification = PhoneVerification.objects.get(
            phone_number=phone_number,
            otp_code=otp_code,
            is_verified=False
        )
        
        if verification.is_expired:
            return False, "OTP has expired. Please request a new one.", None
        
        if verification.attempts >= 5:
            return False, "Too many failed attempts. Please request a new OTP.", None
        
        verification.is_verified = True
        verification.save()
        
        return True, "OTP verified successfully.", verification
        
    except PhoneVerification.DoesNotExist:
        # Increment attempts for existing non-verified OTPs
        from django.db import models
        PhoneVerification.objects.filter(
            phone_number=phone_number,
            is_verified=False
        ).update(attempts=models.F('attempts') + 1)
        
        return False, "Invalid OTP. Please try again.", None

def format_phone_number(phone_number):
    """
    Format phone number to standard format (Legacy - for India only)
    """
    # Remove any non-numeric characters
    phone = ''.join(filter(str.isdigit, str(phone_number)))
    
    # Add country code if not present
    if len(phone) == 10:
        phone = '91' + phone
    elif len(phone) == 12 and phone.startswith('91'):
        pass  # Already has country code
    else:
        raise ValueError("Invalid phone number format")
    
    return phone

def format_phone_number_with_country(phone_number_with_code, country_code):
    """
    Format phone number with country code for international support
    """
    # Remove any non-numeric characters except + sign
    phone = ''.join(filter(lambda x: x.isdigit() or x == '+', str(phone_number_with_code)))
    
    # Remove + from phone if present
    if phone.startswith('+'):
        phone = phone[1:]
    
    # Country code validation rules
    country_rules = {
        '+91': {'min_digits': 10, 'max_digits': 10, 'country_code': '91'},  # India
        '+1': {'min_digits': 10, 'max_digits': 10, 'country_code': '1'},    # US/Canada
        '+44': {'min_digits': 10, 'max_digits': 11, 'country_code': '44'},  # UK
        '+971': {'min_digits': 9, 'max_digits': 9, 'country_code': '971'},  # UAE
        '+966': {'min_digits': 9, 'max_digits': 9, 'country_code': '966'},  # Saudi Arabia
        '+974': {'min_digits': 8, 'max_digits': 8, 'country_code': '974'},  # Qatar
        '+965': {'min_digits': 8, 'max_digits': 8, 'country_code': '965'},  # Kuwait
        '+968': {'min_digits': 8, 'max_digits': 8, 'country_code': '968'},  # Oman
        '+973': {'min_digits': 8, 'max_digits': 8, 'country_code': '973'},  # Bahrain
        '+60': {'min_digits': 9, 'max_digits': 10, 'country_code': '60'},   # Malaysia
        '+65': {'min_digits': 8, 'max_digits': 8, 'country_code': '65'},    # Singapore
        '+86': {'min_digits': 11, 'max_digits': 11, 'country_code': '86'},  # China
    }
    
    if country_code not in country_rules:
        raise ValueError(f"Unsupported country code: {country_code}")
    
    rules = country_rules[country_code]
    country_code_digits = rules['country_code']
    
    # Check if phone already has country code
    if phone.startswith(country_code_digits):
        # Phone already has country code
        phone_without_country = phone[len(country_code_digits):]
    else:
        # Phone doesn't have country code, use as-is
        phone_without_country = phone
    
    # Validate phone number length
    if len(phone_without_country) < rules['min_digits'] or len(phone_without_country) > rules['max_digits']:
        raise ValueError(f"Invalid phone number length for {country_code}. Expected {rules['min_digits']}-{rules['max_digits']} digits.")
    
    # Return formatted phone with country code
    formatted_phone = country_code_digits + phone_without_country
    return formatted_phone

def is_phone_number_valid(phone_number):
    """
    Validate phone number format
    """
    try:
        formatted = format_phone_number(phone_number)
        return len(formatted) == 12 and formatted.startswith('91')
    except ValueError:
        return False