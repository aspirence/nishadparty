from django.contrib.auth.models import AbstractUser, BaseUserManager
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

class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('The phone number must be set')

        # Generate username from phone number if not provided
        if 'username' not in extra_fields:
            extra_fields['username'] = f"user_{phone_number}"

        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_phone_verified', True)
        extra_fields.setdefault('user_type', 'ADMINISTRATOR')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone_number, password, **extra_fields)

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

    objects = UserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []  # Remove required fields for easier superuser creation
    
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


# Feature Permission System
FEATURE_CHOICES = [
    ('USER_MANAGEMENT', 'User Management'),
    ('ASSET_MANAGEMENT', 'Asset Management'),
    ('GATE_PASS', 'Gate Pass Management'),
    ('DONATION_MANAGEMENT', 'Donation Management'),
    ('EVENT_MANAGEMENT', 'Event Management'),
    ('MEMBERSHIP_MANAGEMENT', 'Membership Management'),
]

class FeaturePermission(models.Model):
    """
    Model to manage feature-level permissions for users.
    Allows admins to grant specific users access to manage certain features.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feature_permissions')
    feature = models.CharField(max_length=50, choices=FEATURE_CHOICES)
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='permissions_granted')
    granted_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, help_text="Optional notes about this permission")

    class Meta:
        unique_together = ('user', 'feature')
        ordering = ['-granted_at']
        verbose_name = 'Feature Permission'
        verbose_name_plural = 'Feature Permissions'

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_feature_display()}"

    @classmethod
    def user_has_permission(cls, user, feature):
        """Check if a user has permission for a specific feature"""
        # Admins have all permissions
        if user.user_type == 'ADMINISTRATOR':
            return True

        # Check if user has active permission for this feature
        return cls.objects.filter(
            user=user,
            feature=feature,
            is_active=True
        ).exists()

    @classmethod
    def get_user_features(cls, user):
        """Get all features a user has access to"""
        if user.user_type == 'ADMINISTRATOR':
            return [choice[0] for choice in FEATURE_CHOICES]

        return list(cls.objects.filter(
            user=user,
            is_active=True
        ).values_list('feature', flat=True))
