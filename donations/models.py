from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

PAYMENT_METHOD_CHOICES = [
    ('ONLINE', 'Online Payment'),
    ('CASH', 'Cash'),
    ('CHEQUE', 'Cheque'),
    ('DD', 'Demand Draft'),
    ('UPI', 'UPI'),
    ('BANK_TRANSFER', 'Bank Transfer'),
]

PAYMENT_STATUS_CHOICES = [
    ('PENDING', 'Pending'),
    ('SUCCESS', 'Success'),
    ('FAILED', 'Failed'),
    ('CANCELLED', 'Cancelled'),
    ('REFUNDED', 'Refunded'),
]

FREQUENCY_CHOICES = [
    ('MONTHLY', 'Monthly'),
    ('QUARTERLY', 'Quarterly'),
    ('HALF_YEARLY', 'Half Yearly'),
    ('YEARLY', 'Yearly'),
]

class Donation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    donor_name = models.CharField(max_length=100)
    donor_email = models.EmailField()
    donor_phone = models.CharField(max_length=15)
    donor_address = models.TextField(blank=True)
    donor_pan = models.CharField(max_length=10, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    razorpay_order_id = models.CharField(max_length=100, blank=True)
    razorpay_signature = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    is_recurring = models.BooleanField(default=False)
    constituency = models.CharField(max_length=100, blank=True)
    purpose = models.CharField(max_length=200, blank=True)
    anonymous = models.BooleanField(default=False)
    receipt_number = models.CharField(max_length=50, unique=True, blank=True)
    receipt_generated = models.BooleanField(default=False)
    receipt_file = models.FileField(upload_to='receipts/', blank=True, null=True)
    tax_exemption_claimed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            year = timezone.now().year
            month = timezone.now().month
            count = Donation.objects.filter(created_at__year=year, created_at__month=month).count() + 1
            self.receipt_number = f"NISHAD{year}{month:02d}{count:05d}"
        super().save(*args, **kwargs)
    
    @property
    def requires_pan_verification(self):
        return self.amount >= 2000
    
    def __str__(self):
        return f"₹{self.amount} from {self.donor_name} ({self.receipt_number})"
    
    class Meta:
        ordering = ['-created_at']

class RecurringDonation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    next_payment_date = models.DateField()
    is_active = models.BooleanField(default=True)
    failed_attempts = models.IntegerField(default=0)
    max_failures = models.IntegerField(default=3)
    constituency = models.CharField(max_length=100, blank=True)
    purpose = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.donor.full_name} - ₹{self.amount} {self.frequency}"
    
    class Meta:
        ordering = ['-created_at']

class DonationCompliance(models.Model):
    donation = models.OneToOneField(Donation, on_delete=models.CASCADE)
    pan_verified = models.BooleanField(default=False)
    pan_verification_date = models.DateTimeField(null=True, blank=True)
    election_commission_reported = models.BooleanField(default=False)
    ec_report_date = models.DateTimeField(null=True, blank=True)
    ec_reference_number = models.CharField(max_length=50, blank=True)
    compliance_notes = models.TextField(blank=True)
    verification_documents = models.FileField(upload_to='compliance_docs/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Compliance for {self.donation.receipt_number}"

class DonationCampaign(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    raised_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='campaign_images/', blank=True, null=True)
    constituency = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def progress_percentage(self):
        if self.target_amount > 0:
            return min((self.raised_amount / self.target_amount) * 100, 100)
        return 0
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']
