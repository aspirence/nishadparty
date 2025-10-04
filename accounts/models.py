from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

USER_TYPE_CHOICES = [
    ('SUPPORTER', 'Supporter'),
    ('MEMBER', 'Member'),
    ('VOLUNTEER', 'Volunteer'),
    ('COORDINATOR', 'Coordinator'),
    ('ADMINISTRATOR', 'Administrator'),
]

LANGUAGE_CHOICES = [
    ('hi', 'Hindi'),
    ('en', 'English'),
]

COMMUNITY_CHOICES = [
    ('FISHING', 'Fishing Community'),
    ('BOATING', 'Boating Community'),
    ('ALLIED', 'Allied Fishing Services'),
    ('OTHER', 'Other'),
]

class User(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True)
    is_phone_verified = models.BooleanField(default=False)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='SUPPORTER')
    constituency = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)
    preferred_language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='hi')
    fishing_license_number = models.CharField(max_length=50, blank=True)
    boat_registration = models.CharField(max_length=50, blank=True)
    family_primary_account = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='family_members')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.phone_number})"
    
    @property
    def full_name(self):
        return self.get_full_name() or self.username
    
    @classmethod
    def get_user_type_choices(cls):
        return USER_TYPE_CHOICES

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    community_type = models.CharField(max_length=20, choices=COMMUNITY_CHOICES, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    experience_years = models.IntegerField(default=0)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    pincode = models.CharField(max_length=6, blank=True)
    
    def __str__(self):
        return f"Profile of {self.user.full_name}"

class PhoneVerification(models.Model):
    phone_number = models.CharField(max_length=15)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    expires_at = models.DateTimeField()
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(minutes=10)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f"OTP for {self.phone_number}"
    
    class Meta:
        ordering = ['-created_at']
