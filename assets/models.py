from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
import qrcode
from io import BytesIO
from django.core.files import File

ASSET_TYPE_CHOICES = [
    ('VEHICLE', 'Vehicle'),
    ('EQUIPMENT', 'Equipment'),
    ('ELECTRONICS', 'Electronics'),
    ('FURNITURE', 'Furniture'),
    ('BOAT', 'Boat'),
    ('SOUND_SYSTEM', 'Sound System'),
    ('TENT', 'Tent'),
    ('BANNER', 'Banner'),
    ('OTHER', 'Other'),
]

ASSET_STATUS_CHOICES = [
    ('AVAILABLE', 'Available'),
    ('IN_USE', 'In Use'),
    ('MAINTENANCE', 'Under Maintenance'),
    ('DAMAGED', 'Damaged'),
    ('RETIRED', 'Retired'),
    ('LOST', 'Lost'),
]

CONDITION_CHOICES = [
    ('EXCELLENT', 'Excellent'),
    ('GOOD', 'Good'),
    ('FAIR', 'Fair'),
    ('POOR', 'Poor'),
    ('DAMAGED', 'Damaged'),
]

ASSIGNMENT_STATUS_CHOICES = [
    ('PENDING', 'Pending Acceptance'),
    ('ACCEPTED', 'Accepted'),
    ('REJECTED', 'Rejected'),
    ('IN_USE', 'In Use'),
    ('RETURNED', 'Returned'),
    ('OVERDUE', 'Overdue'),
    ('LOST', 'Lost/Damaged'),
]

ACCESS_LEVEL_CHOICES = [
    ('VIP', 'VIP Access'),
    ('GENERAL', 'General Access'),
    ('VOLUNTEER', 'Volunteer Access'),
    ('STAFF', 'Staff Access'),
]

class Asset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    asset_code = models.CharField(max_length=20, unique=True, blank=True)
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPE_CHOICES)
    description = models.TextField()
    purchase_date = models.DateField()
    purchase_cost = models.DecimalField(max_digits=10, decimal_places=2)
    current_location = models.CharField(max_length=200)
    constituency = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=ASSET_STATUS_CHOICES, default='AVAILABLE')
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='GOOD')
    maintenance_schedule = models.JSONField(default=dict)
    last_maintenance_date = models.DateField(null=True, blank=True)
    next_maintenance_date = models.DateField(null=True, blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)
    insurance_details = models.JSONField(default=dict)
    serial_number = models.CharField(max_length=100, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    manufacturer = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to='asset_images/', blank=True, null=True)
    qr_code = models.ImageField(upload_to='asset_qr_codes/', blank=True, null=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_assets')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.asset_code:
            year = timezone.now().year
            count = Asset.objects.filter(created_at__year=year).count() + 1
            self.asset_code = f"ASSET{year}{count:05d}"
        
        # Generate QR code
        if not self.qr_code:
            qr_data = f"Asset: {self.name} | Code: {self.asset_code} | Location: {self.current_location}"
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_data)
            qr.make(fit=True)
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            buffer = BytesIO()
            qr_image.save(buffer, format='PNG')
            file_name = f"asset_qr_{self.asset_code}.png"
            self.qr_code.save(file_name, File(buffer), save=False)
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.asset_code})"
    
    class Meta:
        ordering = ['name']

class AssetCheckout(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='checkouts')
    checked_out_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='asset_checkouts')
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='assigned_asset_checkouts')
    
    # Assignment Details
    assignment_date = models.DateTimeField(default=timezone.now)
    checkout_date = models.DateTimeField(null=True, blank=True)
    expected_return_date = models.DateTimeField()
    actual_return_date = models.DateTimeField(null=True, blank=True)
    
    # Status and User Actions
    status = models.CharField(max_length=20, choices=ASSIGNMENT_STATUS_CHOICES, default='PENDING')
    acceptance_date = models.DateTimeField(null=True, blank=True)
    rejection_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Purpose and Location
    purpose = models.CharField(max_length=200)
    destination = models.CharField(max_length=200, blank=True)
    
    # Condition Tracking
    condition_checkout = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='GOOD')
    condition_return = models.CharField(max_length=20, choices=CONDITION_CHOICES, null=True, blank=True)
    
    # GPS Tracking
    gps_latitude_checkout = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    gps_longitude_checkout = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    gps_latitude_return = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    gps_longitude_return = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    
    # Notes
    checkout_notes = models.TextField(blank=True)
    return_notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    user_notes = models.TextField(blank=True)
    
    # Return Details
    damage_reported = models.BooleanField(default=False)
    damage_description = models.TextField(blank=True)
    damage_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Legacy fields for compatibility
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='approved_checkouts')
    is_returned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def accept_assignment(self):
        """User accepts the asset assignment"""
        self.status = 'ACCEPTED'
        self.acceptance_date = timezone.now()
        self.checkout_date = timezone.now()
        self.asset.status = 'IN_USE'
        self.asset.save()
        self.save()

    def reject_assignment(self, reason=""):
        """User rejects the asset assignment"""
        self.status = 'REJECTED'
        self.rejection_date = timezone.now()
        self.rejection_reason = reason
        self.asset.status = 'AVAILABLE'
        self.asset.save()
        self.save()

    def mark_in_use(self):
        """Mark asset as actively in use"""
        self.status = 'IN_USE'
        self.asset.status = 'IN_USE'
        self.asset.save()
        self.save()

    def return_asset(self, condition, notes="", damage=False, damage_desc="", damage_cost=None):
        """Return the asset"""
        self.status = 'RETURNED'
        self.actual_return_date = timezone.now()
        self.condition_return = condition
        self.return_notes = notes
        self.damage_reported = damage
        self.damage_description = damage_desc
        if damage_cost:
            self.damage_cost = damage_cost
        self.is_returned = True
        
        # Update asset status and condition
        self.asset.status = 'AVAILABLE' if not damage else 'DAMAGED'
        self.asset.condition = condition
        self.asset.save()
        self.save()

    @property
    def is_overdue(self):
        if self.expected_return_date and self.status in ['ACCEPTED', 'IN_USE']:
            return timezone.now() > self.expected_return_date
        return False

    @property
    def days_assigned(self):
        if self.actual_return_date:
            return (self.actual_return_date.date() - self.assignment_date.date()).days
        return (timezone.now().date() - self.assignment_date.date()).days

    @property
    def is_currently_overdue(self):
        if self.is_returned:
            return False
        return timezone.now() > self.expected_return_date
    
    def __str__(self):
        return f"{self.asset.name} checked out by {self.checked_out_by.full_name}"
    
    class Meta:
        ordering = ['-checkout_date']

class GatePass(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey('campaigns.Event', on_delete=models.CASCADE, related_name='gate_passes')
    attendee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    pass_code = models.CharField(max_length=20, unique=True, blank=True)
    qr_code = models.ImageField(upload_to='gate_passes/', blank=True, null=True)
    access_level = models.CharField(max_length=20, choices=ACCESS_LEVEL_CHOICES, default='GENERAL')
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    issued_at = models.DateTimeField(auto_now_add=True)
    issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='issued_gate_passes')
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    entry_gate = models.CharField(max_length=50, blank=True)
    special_instructions = models.TextField(blank=True)
    companion_count = models.IntegerField(default=0)
    
    def save(self, *args, **kwargs):
        if not self.pass_code:
            self.pass_code = f"GP{timezone.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
        
        # Generate QR code
        if not self.qr_code:
            qr_data = f"Gate Pass: {self.pass_code} | Event: {self.event.title} | Attendee: {self.attendee.full_name} | Access: {self.access_level}"
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_data)
            qr.make(fit=True)
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            buffer = BytesIO()
            qr_image.save(buffer, format='PNG')
            file_name = f"gate_pass_{self.pass_code}.png"
            self.qr_code.save(file_name, File(buffer), save=False)
        
        super().save(*args, **kwargs)
    
    @property
    def is_valid(self):
        now = timezone.now()
        return self.valid_from <= now <= self.valid_until and not self.is_used
    
    def __str__(self):
        return f"Gate Pass {self.pass_code} for {self.attendee.full_name}"
    
    class Meta:
        unique_together = ['event', 'attendee']
        ordering = ['-issued_at']

class AssetMaintenance(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='maintenance_records')
    maintenance_type = models.CharField(max_length=100)
    description = models.TextField()
    cost = models.DecimalField(max_digits=8, decimal_places=2)
    maintenance_date = models.DateField()
    performed_by = models.CharField(max_length=200)
    next_maintenance_date = models.DateField(null=True, blank=True)
    parts_replaced = models.JSONField(default=list)
    before_images = models.JSONField(default=list)
    after_images = models.JSONField(default=list)
    warranty_period = models.IntegerField(default=0, help_text="Warranty period in days")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.maintenance_type} for {self.asset.name}"
    
    class Meta:
        ordering = ['-maintenance_date']
