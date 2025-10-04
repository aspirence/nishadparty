from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

VERIFICATION_STATUS_CHOICES = [
    ('PENDING', 'Pending'),
    ('APPROVED', 'Approved'),
    ('REJECTED', 'Rejected'),
    ('EXPIRED', 'Expired'),
]

DOCUMENT_TYPE_CHOICES = [
    ('AADHAR', 'Aadhar Card'),
    ('VOTER_ID', 'Voter ID'),
    ('PAN', 'PAN Card'),
    ('FISHING_LICENSE', 'Fishing License'),
    ('BOAT_REGISTRATION', 'Boat Registration'),
    ('INCOME_CERTIFICATE', 'Income Certificate'),
    ('CASTE_CERTIFICATE', 'Caste Certificate'),
]

STATUS_CHOICES = [
    ('PENDING', 'Pending Verification'),
    ('VERIFIED', 'Verified'),
    ('REJECTED', 'Rejected'),
]

class MembershipTier(models.Model):
    name = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_months = models.IntegerField()
    benefits = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - ₹{self.price} for {self.duration_months} months"
    
    class Meta:
        ordering = ['price']

class Membership(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tier = models.ForeignKey(MembershipTier, on_delete=models.CASCADE, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    payment_id = models.CharField(max_length=100, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='PENDING')
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='verified_memberships')
    verified_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    membership_id = models.CharField(max_length=20, unique=True, blank=True)

    # Additional user information
    full_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.membership_id:
            year = timezone.now().year
            count = Membership.objects.filter(created_at__year=year).count() + 1
            self.membership_id = f"NISHAD{year}{count:06d}"
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now().date() > self.end_date
    
    def __str__(self):
        return f"{self.user.full_name} - {self.tier.name} ({self.membership_id})"
    
    class Meta:
        ordering = ['-created_at']

class DocumentVerification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    membership = models.ForeignKey(Membership, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPE_CHOICES)
    document_file = models.FileField(upload_to='membership_documents/')
    document_number = models.CharField(max_length=50, blank=True)
    verification_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='verified_documents')
    rejection_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.document_type} for {self.membership.user.full_name}"
    
    class Meta:
        unique_together = ['membership', 'document_type']
        ordering = ['-created_at']

class MembershipApplicationSteps(models.Model):
    membership = models.OneToOneField(Membership, on_delete=models.CASCADE)
    personal_info_completed = models.BooleanField(default=False)
    documents_uploaded = models.BooleanField(default=False)
    payment_completed = models.BooleanField(default=False)
    verification_submitted = models.BooleanField(default=False)
    current_step = models.IntegerField(default=1)  # 1-4 representing the steps
    
    def __str__(self):
        return f"Application steps for {self.membership.user.full_name}"
