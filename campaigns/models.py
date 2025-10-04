from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

CAMPAIGN_TYPE_CHOICES = [
    ('ELECTION', 'Election Campaign'),
    ('AWARENESS', 'Awareness Campaign'),
    ('MEMBERSHIP', 'Membership Drive'),
    ('FUNDRAISING', 'Fundraising'),
    ('COMMUNITY', 'Community Outreach'),
    ('POLICY', 'Policy Advocacy'),
]

CAMPAIGN_STATUS_CHOICES = [
    ('DRAFT', 'Draft'),
    ('ACTIVE', 'Active'),
    ('PAUSED', 'Paused'),
    ('COMPLETED', 'Completed'),
    ('CANCELLED', 'Cancelled'),
]

EVENT_TYPE_CHOICES = [
    ('RALLY', 'Rally'),
    ('MEETING', 'Public Meeting'),
    ('SEMINAR', 'Seminar'),
    ('WORKSHOP', 'Workshop'),
    ('CONFERENCE', 'Conference'),
    ('DOOR_TO_DOOR', 'Door to Door'),
    ('BOAT_CAMPAIGN', 'Boat Campaign'),
    ('FISHING_DEMO', 'Fishing Demonstration'),
    ('COMMUNITY_FEAST', 'Community Feast'),
]

class Campaign(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    constituency = models.CharField(max_length=100)
    district = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)
    campaign_type = models.CharField(max_length=20, choices=CAMPAIGN_TYPE_CHOICES)
    budget = models.DecimalField(max_digits=12, decimal_places=2)
    spent_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=CAMPAIGN_STATUS_CHOICES, default='DRAFT')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_campaigns')
    coordinators = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='coordinated_campaigns', blank=True)
    volunteers = models.ManyToManyField(settings.AUTH_USER_MODEL, through='CampaignVolunteer', related_name='volunteer_campaigns')
    image = models.ImageField(upload_to='campaign_images/', blank=True, null=True)
    goals = models.JSONField(default=list)
    target_demographics = models.JSONField(default=dict)
    expected_reach = models.IntegerField(default=0)
    actual_reach = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = self.title.lower().replace(' ', '-')
            self.slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)
    
    @property
    def budget_utilization_percentage(self):
        if self.budget > 0:
            return min((self.spent_amount / self.budget) * 100, 100)
        return 0
    
    @property
    def remaining_budget(self):
        return self.budget - self.spent_amount
    
    def __str__(self):
        return f"{self.title} ({self.constituency})"
    
    class Meta:
        ordering = ['-created_at']

class CampaignVolunteer(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    volunteer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=100, blank=True)
    assigned_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    performance_notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['campaign', 'volunteer']
    
    def __str__(self):
        return f"{self.volunteer.full_name} - {self.campaign.title}"

class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, null=True, blank=True, related_name='events')
    title = models.CharField(max_length=200)
    slug = models.SlugField(blank=True)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    date_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    venue = models.CharField(max_length=200)
    address = models.TextField()
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    max_attendees = models.IntegerField(default=0)  # 0 means unlimited
    registration_required = models.BooleanField(default=True)
    registration_deadline = models.DateTimeField(null=True, blank=True)
    is_public = models.BooleanField(default=True)
    contact_person = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    contact_phone = models.CharField(max_length=15, blank=True)
    image = models.ImageField(upload_to='event_images/', blank=True, null=True)
    requirements = models.TextField(blank=True)
    agenda = models.JSONField(default=list)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=[
        ('SCHEDULED', 'Scheduled'),
        ('ONGOING', 'Ongoing'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('POSTPONED', 'Postponed'),
    ], default='SCHEDULED')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_events')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = self.title.lower().replace(' ', '-')
            self.slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)
    
    @property
    def is_registration_open(self):
        if not self.registration_required:
            return False
        if self.registration_deadline:
            return timezone.now() < self.registration_deadline
        return self.date_time > timezone.now()
    
    @property
    def attendee_count(self):
        return self.attendees.filter(attended=True).count()
    
    def __str__(self):
        return f"{self.title} - {self.date_time.strftime('%Y-%m-%d')}"
    
    class Meta:
        ordering = ['date_time']

class EventAttendance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='attendees')
    attendee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    registered_at = models.DateTimeField(auto_now_add=True)
    attended = models.BooleanField(default=False)
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    gate_pass_used = models.CharField(max_length=50, blank=True)
    feedback_rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    feedback_comments = models.TextField(blank=True)
    special_requirements = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['event', 'attendee']
        ordering = ['registered_at']
    
    def __str__(self):
        return f"{self.attendee.full_name} - {self.event.title}"

class CampaignExpense(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='expenses')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    expense_date = models.DateField()
    category = models.CharField(max_length=100)
    vendor = models.CharField(max_length=200, blank=True)
    receipt_file = models.FileField(upload_to='expense_receipts/', blank=True, null=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='approved_expenses')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - ₹{self.amount}"
    
    class Meta:
        ordering = ['-expense_date']
