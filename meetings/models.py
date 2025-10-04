from django.db import models
from django.conf import settings

MEETING_TYPE_CHOICES = [
    ('LEADERSHIP', 'Leadership Meeting'),
    ('COORDINATION', 'Coordination Meeting'),
    ('PLANNING', 'Planning Session'),
    ('REVIEW', 'Review Meeting'),
    ('STRATEGY', 'Strategy Discussion'),
    ('COMMUNITY', 'Community Meeting'),
]

PRIORITY_CHOICES = [
    ('LOW', 'Low'),
    ('MEDIUM', 'Medium'),
    ('HIGH', 'High'),
    ('URGENT', 'Urgent'),
]

MEETING_STATUS_CHOICES = [
    ('SCHEDULED', 'Scheduled'),
    ('ONGOING', 'Ongoing'),
    ('COMPLETED', 'Completed'),
    ('CANCELLED', 'Cancelled'),
    ('POSTPONED', 'Postponed'),
]

RESPONSE_CHOICES = [
    ('PENDING', 'Pending'),
    ('ACCEPTED', 'Accepted'),
    ('DECLINED', 'Declined'),
    ('TENTATIVE', 'Tentative'),
]

ATTENDEE_ROLE_CHOICES = [
    ('ORGANIZER', 'Organizer'),
    ('REQUIRED', 'Required Attendee'),
    ('OPTIONAL', 'Optional Attendee'),
    ('RESOURCE', 'Resource Person'),
]

class Meeting(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    meeting_type = models.CharField(max_length=20, choices=MEETING_TYPE_CHOICES)
    date_time = models.DateTimeField()
    duration_minutes = models.IntegerField()
    venue = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    is_virtual = models.BooleanField(default=False)
    meeting_link = models.URLField(blank=True)
    constituency = models.CharField(max_length=100, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=MEETING_STATUS_CHOICES, default='SCHEDULED')
    agenda = models.JSONField(default=list)
    materials = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.date_time.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        ordering = ['date_time']

class MeetingAttendee(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='attendees')
    attendee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ATTENDEE_ROLE_CHOICES, default='REQUIRED')
    invitation_sent = models.BooleanField(default=False)
    response_status = models.CharField(max_length=20, choices=RESPONSE_CHOICES, default='PENDING')
    attended = models.BooleanField(default=False)
    response_notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.attendee.full_name} - {self.meeting.title}"
    
    class Meta:
        unique_together = ['meeting', 'attendee']
