from django.db import models
from django.conf import settings
from django.utils import timezone

SCHEME_TYPE_CHOICES = [
    ('FISHING', 'Fishing Related'),
    ('BOAT', 'Boat Subsidy'),
    ('EDUCATION', 'Education'),
    ('HEALTH', 'Health'),
    ('HOUSING', 'Housing'),
    ('EMPLOYMENT', 'Employment'),
    ('INSURANCE', 'Insurance'),
    ('PENSION', 'Pension'),
    ('FINANCIAL', 'Financial Assistance'),
]

APPLICATION_STATUS_CHOICES = [
    ('DRAFT', 'Draft'),
    ('SUBMITTED', 'Submitted'),
    ('UNDER_REVIEW', 'Under Review'),
    ('APPROVED', 'Approved'),
    ('REJECTED', 'Rejected'),
    ('PENDING_DOCUMENTS', 'Pending Documents'),
    ('COMPLETED', 'Completed'),
]

DEMAND_LEVEL_CHOICES = [
    ('HIGH', 'High Demand'),
    ('MEDIUM', 'Medium Demand'),
    ('LOW', 'Low Demand'),
]

WEATHER_ALERT_CHOICES = [
    ('STORM', 'Storm Warning'),
    ('CYCLONE', 'Cyclone Alert'),
    ('HEAVY_RAIN', 'Heavy Rain'),
    ('ROUGH_SEA', 'Rough Sea Conditions'),
    ('FISHING_BAN', 'Fishing Ban'),
    ('HIGH_TIDE', 'High Tide Alert'),
]

SEVERITY_CHOICES = [
    ('LOW', 'Low'),
    ('MEDIUM', 'Medium'),
    ('HIGH', 'High'),
    ('CRITICAL', 'Critical'),
]

class GovernmentScheme(models.Model):
    name = models.CharField(max_length=200)
    scheme_code = models.CharField(max_length=50, unique=True, blank=True)
    description = models.TextField()
    eligibility_criteria = models.TextField()
    application_process = models.TextField()
    required_documents = models.JSONField(default=list)
    deadline = models.DateField(null=True, blank=True)
    benefit_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    scheme_type = models.CharField(max_length=20, choices=SCHEME_TYPE_CHOICES)
    implementing_agency = models.CharField(max_length=200)
    contact_details = models.JSONField(default=dict)
    website_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    state = models.CharField(max_length=50, blank=True)
    district = models.CharField(max_length=100, blank=True)
    constituency = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.scheme_code:
            scheme_type_code = self.scheme_type[:3].upper()
            count = GovernmentScheme.objects.filter(scheme_type=self.scheme_type).count() + 1
            self.scheme_code = f"SCHEME_{scheme_type_code}_{count:05d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at']

class SchemeApplication(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    scheme = models.ForeignKey(GovernmentScheme, on_delete=models.CASCADE)
    application_id = models.CharField(max_length=50, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS_CHOICES, default='DRAFT')
    applied_date = models.DateField(null=True, blank=True)
    documents_submitted = models.JSONField(default=dict)
    additional_info = models.JSONField(default=dict)
    follow_up_date = models.DateField(null=True, blank=True)
    approval_date = models.DateField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    assisted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assisted_applications')
    reference_number = models.CharField(max_length=100, blank=True)
    benefit_received = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.application_id:
            year = timezone.now().year
            count = SchemeApplication.objects.filter(created_at__year=year).count() + 1
            self.application_id = f"APP{year}{count:06d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.full_name} - {self.scheme.name}"
    
    class Meta:
        unique_together = ['user', 'scheme']
        ordering = ['-created_at']

class MarketPrice(models.Model):
    fish_type = models.CharField(max_length=100)
    market_location = models.CharField(max_length=100)
    price_per_kg = models.DecimalField(max_digits=8, decimal_places=2)
    date_recorded = models.DateField()
    demand_level = models.CharField(max_length=10, choices=DEMAND_LEVEL_CHOICES)
    quality_grade = models.CharField(max_length=20, blank=True)
    supplier_count = models.IntegerField(default=0)
    quantity_available = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    seasonal_factor = models.CharField(max_length=100, blank=True)
    weather_impact = models.TextField(blank=True)
    transportation_cost = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.fish_type} at {self.market_location} - ₹{self.price_per_kg}/kg"
    
    class Meta:
        unique_together = ['fish_type', 'market_location', 'date_recorded']
        ordering = ['-date_recorded']

class WeatherAlert(models.Model):
    region = models.CharField(max_length=100)
    alert_type = models.CharField(max_length=20, choices=WEATHER_ALERT_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    issued_by = models.CharField(max_length=100)
    official_reference = models.CharField(max_length=100, blank=True)
    affected_areas = models.JSONField(default=list)
    safety_instructions = models.TextField()
    contact_numbers = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    auto_send_sms = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)
    recipients_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def is_current(self):
        now = timezone.now()
        return self.valid_from <= now <= self.valid_until
    
    def __str__(self):
        return f"{self.alert_type} Alert for {self.region}"
    
    class Meta:
        ordering = ['-valid_from']

class FishingLicense(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    license_number = models.CharField(max_length=50, unique=True)
    license_type = models.CharField(max_length=50)
    issued_date = models.DateField()
    expiry_date = models.DateField()
    issuing_authority = models.CharField(max_length=200)
    fishing_areas = models.JSONField(default=list)
    boat_details = models.JSONField(default=dict)
    restrictions = models.TextField(blank=True)
    renewal_fee = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True)
    renewal_reminder_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def is_expiring_soon(self):
        days_until_expiry = (self.expiry_date - timezone.now().date()).days
        return days_until_expiry <= 30
    
    def __str__(self):
        return f"License {self.license_number} for {self.user.full_name}"
    
    class Meta:
        ordering = ['-issued_date']

class CommunityEvent(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=100)
    date_time = models.DateTimeField()
    location = models.CharField(max_length=200)
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    target_community = models.CharField(max_length=100)
    expected_participants = models.IntegerField(default=0)
    actual_participants = models.IntegerField(default=0)
    budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sponsors = models.JSONField(default=list)
    agenda = models.JSONField(default=list)
    outcomes = models.TextField(blank=True)
    photos = models.JSONField(default=list)
    feedback_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-date_time']
