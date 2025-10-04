from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

User = get_user_model()

GATE_PASS_STATUS_CHOICES = [
    ('PENDING', _('Pending')),
    ('APPROVED', _('Approved')),
    ('REJECTED', _('Rejected')),
    ('EXPIRED', _('Expired')),
]

GATE_PASS_TYPE_CHOICES = [
    ('VISITOR', _('Visitor Pass')),
    ('VENDOR', _('Vendor Pass')),
    ('VIP', _('VIP Pass')),
    ('STAFF', _('Staff Pass')),
    ('EMERGENCY', _('Emergency Pass')),
]

class GatePassPermission(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='gatepass_permission')
    can_create_gatepass = models.BooleanField(default=False)
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='granted_permissions')
    granted_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Gate Pass Permission for {self.user.full_name}"
    
    class Meta:
        verbose_name = _("Gate Pass Permission")
        verbose_name_plural = _("Gate Pass Permissions")

class GatePass(models.Model):
    pass_number = models.CharField(max_length=20, unique=True, blank=True)
    visitor_name = models.CharField(max_length=100)
    visitor_phone = models.CharField(max_length=15)
    visitor_email = models.EmailField(blank=True)
    visitor_id_proof = models.CharField(max_length=50, help_text="ID proof number")
    company_organization = models.CharField(max_length=200, blank=True, help_text="Company/Organization name")
    
    pass_type = models.CharField(max_length=20, choices=GATE_PASS_TYPE_CHOICES, default='VISITOR')
    purpose = models.TextField(help_text="Purpose of visit")
    
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    
    authorized_areas = models.TextField(blank=True, help_text="Areas visitor is authorized to access")
    escort_required = models.BooleanField(default=False)
    escort_name = models.CharField(max_length=100, blank=True)
    escort_phone = models.CharField(max_length=15, blank=True)
    
    status = models.CharField(max_length=20, choices=GATE_PASS_STATUS_CHOICES, default='PENDING')
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_gatepasses')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_gatepasses')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True, help_text="Additional notes")
    
    def save(self, *args, **kwargs):
        if not self.pass_number:
            self.pass_number = self.generate_pass_number()
        super().save(*args, **kwargs)
    
    def generate_pass_number(self):
        from datetime import datetime
        prefix = "GP"
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{prefix}{timestamp}"
    
    def clean(self):
        if self.valid_from and self.valid_until:
            if self.valid_from >= self.valid_until:
                raise ValidationError("Valid from date must be before valid until date")
        
        if self.escort_required and not self.escort_name:
            raise ValidationError("Escort name is required when escort is needed")
    
    @property
    def is_valid(self):
        now = timezone.now()
        return (self.status == 'APPROVED' and 
                self.valid_from <= now <= self.valid_until)
    
    @property
    def is_expired(self):
        return timezone.now() > self.valid_until
    
    def __str__(self):
        return f"{self.pass_number} - {self.visitor_name}"
    
    class Meta:
        verbose_name = _("Gate Pass")
        verbose_name_plural = _("Gate Passes")
        ordering = ['-created_at']

class GatePassLog(models.Model):
    gatepass = models.ForeignKey(GatePass, on_delete=models.CASCADE, related_name='logs')
    action = models.CharField(max_length=50)
    details = models.TextField(blank=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.gatepass.pass_number} - {self.action}"
    
    class Meta:
        verbose_name = _("Gate Pass Log")
        verbose_name_plural = _("Gate Pass Logs")
        ordering = ['-timestamp']
