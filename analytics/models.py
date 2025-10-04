from django.db import models
from django.conf import settings
from django.utils import timezone

METRIC_CATEGORY_CHOICES = [
    ('USER', 'User Metrics'),
    ('DONATION', 'Donation Metrics'),
    ('CAMPAIGN', 'Campaign Metrics'),
    ('ENGAGEMENT', 'Engagement Metrics'),
    ('FINANCIAL', 'Financial Metrics'),
    ('GEOGRAPHIC', 'Geographic Metrics'),
]

WIDGET_TYPE_CHOICES = [
    ('CHART', 'Chart Widget'),
    ('COUNTER', 'Counter Widget'),
    ('TABLE', 'Table Widget'),
    ('MAP', 'Map Widget'),
    ('PROGRESS', 'Progress Bar Widget'),
    ('LIST', 'List Widget'),
]

class AnalyticsMetric(models.Model):
    metric_name = models.CharField(max_length=100)
    metric_value = models.JSONField()
    constituency = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)
    date_recorded = models.DateField()
    category = models.CharField(max_length=20, choices=METRIC_CATEGORY_CHOICES)
    additional_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.metric_name} - {self.date_recorded}"
    
    class Meta:
        unique_together = ['metric_name', 'date_recorded', 'constituency']
        ordering = ['-date_recorded']

class DashboardWidget(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPE_CHOICES)
    title = models.CharField(max_length=100)
    configuration = models.JSONField()
    position = models.IntegerField()
    is_active = models.BooleanField(default=True)
    size = models.CharField(max_length=20, default='medium')
    refresh_interval = models.IntegerField(default=300)  # seconds
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} for {self.user.full_name}"
    
    class Meta:
        ordering = ['position']
