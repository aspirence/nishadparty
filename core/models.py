from django.db import models
from django.conf import settings
import re

class SiteConfiguration(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}..."
    
    class Meta:
        ordering = ['key']

class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=50)
    changes = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user} {self.action} {self.model_name} {self.object_id}"
    
    class Meta:
        ordering = ['-timestamp']

class YouTubeVideo(models.Model):
    title = models.CharField(max_length=200, help_text="Video title")
    youtube_url = models.URLField(help_text="Full YouTube video URL (e.g., https://www.youtube.com/watch?v=VIDEO_ID)")
    description = models.TextField(blank=True, help_text="Optional description of the video")
    thumbnail_url = models.URLField(blank=True, help_text="Optional custom thumbnail URL (if empty, YouTube thumbnail will be used)")
    is_featured = models.BooleanField(default=False, help_text="Display prominently on homepage")
    is_active = models.BooleanField(default=True, help_text="Show video on website")
    display_order = models.PositiveIntegerField(default=0, help_text="Order of display (lower numbers appear first)")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_video_id(self):
        """Extract YouTube video ID from URL"""
        youtube_url_patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
        ]

        for pattern in youtube_url_patterns:
            match = re.search(pattern, self.youtube_url)
            if match:
                return match.group(1)
        return None

    def get_embed_url(self):
        """Get YouTube embed URL"""
        video_id = self.get_video_id()
        if video_id:
            return f"https://www.youtube.com/embed/{video_id}"
        return None

    def get_thumbnail_url(self):
        """Get video thumbnail URL"""
        if self.thumbnail_url:
            return self.thumbnail_url

        video_id = self.get_video_id()
        if video_id:
            return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        return None

    class Meta:
        ordering = ['display_order', '-created_at']
        verbose_name = "YouTube Video"
        verbose_name_plural = "YouTube Videos"
