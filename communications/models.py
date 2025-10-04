from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

CAMPAIGN_STATUS_CHOICES = [
    ('DRAFT', 'Draft'),
    ('SCHEDULED', 'Scheduled'),
    ('SENDING', 'Sending'),
    ('SENT', 'Sent'),
    ('FAILED', 'Failed'),
    ('CANCELLED', 'Cancelled'),
]

TEMPLATE_CHOICES = [
    ('BASIC', 'Basic Template'),
    ('NEWSLETTER', 'Newsletter Template'),
    ('ANNOUNCEMENT', 'Announcement Template'),
    ('INVITATION', 'Event Invitation'),
    ('REMINDER', 'Reminder Template'),
]

NOTIFICATION_TYPE_CHOICES = [
    ('INFO', 'Information'),
    ('WARNING', 'Warning'),
    ('SUCCESS', 'Success'),
    ('ERROR', 'Error'),
    ('REMINDER', 'Reminder'),
    ('ANNOUNCEMENT', 'Announcement'),
]

MESSAGE_STATUS_CHOICES = [
    ('PENDING', 'Pending'),
    ('SENT', 'Sent'),
    ('DELIVERED', 'Delivered'),
    ('FAILED', 'Failed'),
    ('BOUNCED', 'Bounced'),
]

class SMSCampaign(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    message = models.TextField(max_length=160)
    target_audience = models.JSONField(default=dict)  # filters for user selection
    scheduled_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=CAMPAIGN_STATUS_CHOICES, default='DRAFT')
    sent_count = models.IntegerField(default=0)
    delivered_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)
    total_recipients = models.IntegerField(default=0)
    cost_per_sms = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sender_id = models.CharField(max_length=20, default='NISHAD')
    priority = models.CharField(max_length=10, choices=[('LOW', 'Low'), ('NORMAL', 'Normal'), ('HIGH', 'High')], default='NORMAL')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def delivery_rate(self):
        if self.sent_count > 0:
            return (self.delivered_count / self.sent_count) * 100
        return 0
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at']

class SMSMessage(models.Model):
    campaign = models.ForeignKey(SMSCampaign, on_delete=models.CASCADE, related_name='messages')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)
    message_content = models.TextField()
    status = models.CharField(max_length=20, choices=MESSAGE_STATUS_CHOICES, default='PENDING')
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    provider_message_id = models.CharField(max_length=100, blank=True)
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    cost = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    
    def __str__(self):
        return f"SMS to {self.phone_number} from {self.campaign.name}"
    
    class Meta:
        ordering = ['-sent_at']

class EmailNewsletter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.CharField(max_length=200)
    content = models.TextField()
    html_content = models.TextField(blank=True)
    template = models.CharField(max_length=20, choices=TEMPLATE_CHOICES, default='BASIC')
    target_segments = models.JSONField(default=dict)
    scheduled_time = models.DateTimeField()
    sent_at = models.DateTimeField(null=True, blank=True)
    total_recipients = models.IntegerField(default=0)
    sent_count = models.IntegerField(default=0)
    delivered_count = models.IntegerField(default=0)
    opened_count = models.IntegerField(default=0)
    clicked_count = models.IntegerField(default=0)
    bounced_count = models.IntegerField(default=0)
    unsubscribed_count = models.IntegerField(default=0)
    open_rate = models.FloatField(default=0.0)
    click_rate = models.FloatField(default=0.0)
    bounce_rate = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, choices=CAMPAIGN_STATUS_CHOICES, default='DRAFT')
    from_email = models.EmailField(default='noreply@nishadparty.org')
    reply_to = models.EmailField(blank=True)
    attachments = models.JSONField(default=list)
    tags = models.JSONField(default=list)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def calculate_rates(self):
        if self.delivered_count > 0:
            self.open_rate = (self.opened_count / self.delivered_count) * 100
            self.click_rate = (self.clicked_count / self.delivered_count) * 100
        if self.sent_count > 0:
            self.bounce_rate = (self.bounced_count / self.sent_count) * 100
        self.save()
    
    def __str__(self):
        return self.subject
    
    class Meta:
        ordering = ['-created_at']

class EmailRecipient(models.Model):
    newsletter = models.ForeignKey(EmailNewsletter, on_delete=models.CASCADE, related_name='recipients')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    email_address = models.EmailField()
    status = models.CharField(max_length=20, choices=MESSAGE_STATUS_CHOICES, default='PENDING')
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    bounced_at = models.DateTimeField(null=True, blank=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    provider_message_id = models.CharField(max_length=100, blank=True)
    error_message = models.TextField(blank=True)
    
    def __str__(self):
        return f"Email to {self.email_address}"
    
    class Meta:
        unique_together = ['newsletter', 'recipient']
        ordering = ['-sent_at']

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES, default='INFO')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    action_url = models.URLField(blank=True)
    action_label = models.CharField(max_length=50, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    priority = models.CharField(max_length=10, choices=[('LOW', 'Low'), ('NORMAL', 'Normal'), ('HIGH', 'High')], default='NORMAL')
    icon = models.CharField(max_length=50, blank=True)
    data = models.JSONField(default=dict)  # Additional data for the notification
    
    @property
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    def __str__(self):
        return f"{self.title} for {self.user.full_name}"
    
    class Meta:
        ordering = ['-created_at']

class WhatsAppMessage(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)
    message_content = models.TextField()
    template_name = models.CharField(max_length=100, blank=True)
    template_params = models.JSONField(default=dict)
    media_url = models.URLField(blank=True)
    media_type = models.CharField(max_length=20, blank=True)  # image, video, document, audio
    status = models.CharField(max_length=20, choices=MESSAGE_STATUS_CHOICES, default='PENDING')
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    provider_message_id = models.CharField(max_length=100, blank=True)
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    cost = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_whatsapp_messages')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"WhatsApp to {self.phone_number}"
    
    class Meta:
        ordering = ['-created_at']

class CommunicationTemplate(models.Model):
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=20, choices=[
        ('SMS', 'SMS'),
        ('EMAIL', 'Email'),
        ('WHATSAPP', 'WhatsApp'),
        ('NOTIFICATION', 'Notification'),
    ])
    subject = models.CharField(max_length=200, blank=True)  # For email templates
    content = models.TextField()
    html_content = models.TextField(blank=True)  # For email templates
    variables = models.JSONField(default=list)  # List of available variables
    category = models.CharField(max_length=50, blank=True)
    language = models.CharField(max_length=10, default='hi')
    is_active = models.BooleanField(default=True)
    usage_count = models.IntegerField(default=0)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"
    
    class Meta:
        unique_together = ['name', 'template_type', 'language']
        ordering = ['name']
