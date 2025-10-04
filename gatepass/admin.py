from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import GatePass, GatePassPermission, GatePassLog

@admin.register(GatePass)
class GatePassAdmin(admin.ModelAdmin):
    list_display = ['pass_number', 'visitor_name', 'visitor_phone', 'pass_type', 'status', 
                   'valid_from', 'valid_until', 'created_by', 'is_valid_now']
    list_filter = ['status', 'pass_type', 'created_at', 'valid_from', 'valid_until']
    search_fields = ['pass_number', 'visitor_name', 'visitor_phone', 'visitor_email']
    readonly_fields = ['pass_number', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Visitor Information', {
            'fields': ('visitor_name', 'visitor_phone', 'visitor_email', 'visitor_id_proof', 'company_organization')
        }),
        ('Pass Details', {
            'fields': ('pass_number', 'pass_type', 'purpose', 'valid_from', 'valid_until', 'authorized_areas')
        }),
        ('Escort Information', {
            'fields': ('escort_required', 'escort_name', 'escort_phone'),
            'classes': ('collapse',)
        }),
        ('Status & Approval', {
            'fields': ('status', 'created_by', 'approved_by', 'approved_at')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_valid_now(self, obj):
        if obj.is_valid:
            return format_html('<span style="color: green;">✓ Valid</span>')
        elif obj.is_expired:
            return format_html('<span style="color: red;">✗ Expired</span>')
        else:
            return format_html('<span style="color: orange;">⏳ Pending</span>')
    is_valid_now.short_description = 'Current Status'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by', 'approved_by')

@admin.register(GatePassPermission)
class GatePassPermissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'user_type', 'can_create_gatepass', 'granted_by', 'granted_at']
    list_filter = ['can_create_gatepass', 'granted_at', 'user__user_type']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__phone_number']
    readonly_fields = ['granted_at']
    
    def user_type(self, obj):
        return obj.user.get_user_type_display()
    user_type.short_description = 'User Type'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'granted_by')

@admin.register(GatePassLog)
class GatePassLogAdmin(admin.ModelAdmin):
    list_display = ['gatepass_number', 'action', 'performed_by', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['gatepass__pass_number', 'gatepass__visitor_name', 'details']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    def gatepass_number(self, obj):
        url = reverse('admin:gatepass_gatepass_change', args=[obj.gatepass.pk])
        return format_html('<a href="{}">{}</a>', url, obj.gatepass.pass_number)
    gatepass_number.short_description = 'Gate Pass'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('gatepass', 'performed_by')

# Inline for GatePassLog in GatePass admin
class GatePassLogInline(admin.TabularInline):
    model = GatePassLog
    extra = 0
    readonly_fields = ['action', 'details', 'performed_by', 'timestamp']
    can_delete = False

# Update GatePassAdmin to include logs
GatePassAdmin.inlines = [GatePassLogInline]
