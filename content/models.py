from django.db import models
from django.conf import settings
from django.utils.text import slugify

ARTICLE_CATEGORY_CHOICES = [
    ('NEWS', 'News'),
    ('ANNOUNCEMENT', 'Announcement'),
    ('POLICY', 'Policy'),
    ('COMMUNITY', 'Community Stories'),
    ('FISHING', 'Fishing Related'),
    ('SCHEMES', 'Government Schemes'),
    ('EVENTS', 'Events'),
    ('PRESS_RELEASE', 'Press Release'),
]

LANGUAGE_CHOICES = [
    ('hi', 'Hindi'),
    ('en', 'English'),
    ('bho', 'Bhojpuri'),
    ('awa', 'Awadhi'),
    ('mag', 'Magahi'),
    ('mai', 'Maithili'),
    ('bn', 'Bengali'),
    ('as', 'Assamese'),
    ('or', 'Odia'),
    ('gu', 'Gujarati'),
]

MESSAGE_CATEGORY_CHOICES = [
    ('ANNOUNCEMENT', 'Announcement'),
    ('GREETINGS', 'Greetings'),
    ('TESTIMONIAL', 'Testimonial'),
    ('COMPLAINT', 'Complaint'),
    ('SUGGESTION', 'Suggestion'),
    ('SUPPORT', 'Support Request'),
]

class Article(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    content = models.TextField()
    excerpt = models.TextField()
    featured_image = models.ImageField(upload_to='articles/', blank=True, null=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.CharField(max_length=20, choices=ARTICLE_CATEGORY_CHOICES)
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='hi')
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    view_count = models.IntegerField(default=0)
    tags = models.JSONField(default=list)
    meta_description = models.CharField(max_length=160, blank=True)
    constituency = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']

class Translation(models.Model):
    content_type = models.CharField(max_length=50)
    object_id = models.PositiveIntegerField()
    field_name = models.CharField(max_length=50)
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES)
    translated_text = models.TextField()
    is_verified = models.BooleanField(default=False)
    translated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.content_type} {self.object_id} - {self.language}"
    
    class Meta:
        unique_together = ['content_type', 'object_id', 'field_name', 'language']

class VoiceMessage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    audio_file = models.FileField(upload_to='voice_messages/')
    transcript = models.TextField(blank=True)
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='hi')
    duration_seconds = models.IntegerField()
    category = models.CharField(max_length=20, choices=MESSAGE_CATEGORY_CHOICES)
    is_public = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    moderation_status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending Moderation'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ], default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Voice message from {self.user.full_name}"
    
    class Meta:
        ordering = ['-created_at']
