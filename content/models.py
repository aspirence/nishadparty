from django.db import models
from django.conf import settings
from django.utils.text import slugify
import uuid

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

PHOTO_CATEGORY_CHOICES = [
    ('CAMPAIGNS', 'Campaigns'),
    ('EVENTS', 'Events'),
    ('COMMUNITY', 'Community'),
    ('MEETINGS', 'Meetings'),
    ('LEADERSHIP', 'Leadership'),
    ('RALLIES', 'Rallies'),
]

VIDEO_CATEGORY_CHOICES = [
    ('SPEECHES', 'Speeches'),
    ('CAMPAIGNS', 'Campaigns'),
    ('EVENTS', 'Events'),
    ('DOCUMENTARIES', 'Documentaries'),
    ('INTERVIEWS', 'Interviews'),
    ('NEWS', 'News Coverage'),
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

class Photo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    image = models.ImageField(upload_to='photos/')
    thumbnail = models.ImageField(upload_to='photos/thumbnails/', blank=True, null=True)
    category = models.CharField(max_length=20, choices=PHOTO_CATEGORY_CHOICES)
    location = models.CharField(max_length=200, blank=True)
    event_date = models.DateField(null=True, blank=True)
    photographer = models.CharField(max_length=100, blank=True)
    tags = models.JSONField(default=list)
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    view_count = models.IntegerField(default=0)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
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

class Video(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    youtube_url = models.URLField(blank=True, null=True)
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='videos/thumbnails/', blank=True, null=True)
    duration_minutes = models.IntegerField(default=0)
    duration_seconds = models.IntegerField(default=0)
    category = models.CharField(max_length=20, choices=VIDEO_CATEGORY_CHOICES)
    location = models.CharField(max_length=200, blank=True)
    event_date = models.DateField(null=True, blank=True)
    speaker = models.CharField(max_length=100, blank=True)
    tags = models.JSONField(default=list)
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    view_count = models.IntegerField(default=0)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_youtube_embed_url(self):
        if self.youtube_url:
            if 'youtube.com/watch?v=' in self.youtube_url:
                video_id = self.youtube_url.split('v=')[1].split('&')[0]
                return f"https://www.youtube.com/embed/{video_id}"
            elif 'youtu.be/' in self.youtube_url:
                video_id = self.youtube_url.split('youtu.be/')[1].split('?')[0]
                return f"https://www.youtube.com/embed/{video_id}"
        return None

    def get_youtube_thumbnail(self):
        if self.youtube_url:
            if 'youtube.com/watch?v=' in self.youtube_url:
                video_id = self.youtube_url.split('v=')[1].split('&')[0]
                return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            elif 'youtu.be/' in self.youtube_url:
                video_id = self.youtube_url.split('youtu.be/')[1].split('?')[0]
                return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        return None

    def get_duration_display(self):
        if self.duration_minutes > 0:
            return f"{self.duration_minutes}:{self.duration_seconds:02d}"
        return f"0:{self.duration_seconds:02d}"

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']
