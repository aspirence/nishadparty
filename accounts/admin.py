from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, UserProfile, PhoneVerification

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'full_name', 'phone_number', 'user_type', 'is_phone_verified', 
                   'constituency', 'district', 'is_active', 'date_joined']
    list_filter = ['user_type', 'is_phone_verified', 'is_active', 'is_staff', 
                  'date_joined', 'district', 'state']
    search_fields = ['username', 'first_name', 'last_name', 'phone_number', 'email']
    readonly_fields = ['date_joined', 'last_login']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'is_phone_verified')}),
        ('Party Information', {'fields': ('user_type', 'constituency', 'district', 'state', 'preferred_language')}),
        ('Fishing Community', {'fields': ('fishing_license_number', 'boat_registration', 'family_primary_account')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'phone_number', 'first_name', 'last_name', 'user_type', 'password1', 'password2'),
        }),
    )
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Full Name'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'community_type', 'occupation', 'experience_years', 'date_of_birth']
    list_filter = ['community_type', 'experience_years']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'occupation']
    raw_id_fields = ['user']
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Profile', {'fields': ('avatar', 'bio', 'community_type', 'occupation', 'experience_years')}),
        ('Personal Info', {'fields': ('date_of_birth', 'address', 'pincode')}),
    )

@admin.register(PhoneVerification)
class PhoneVerificationAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'otp_code', 'is_verified', 'attempts', 'created_at', 'expires_at', 'is_expired_now']
    list_filter = ['is_verified', 'created_at', 'expires_at']
    search_fields = ['phone_number']
    readonly_fields = ['created_at', 'expires_at']
    
    def is_expired_now(self, obj):
        if obj.is_expired:
            return format_html('<span style="color: red;">✗ Expired</span>')
        else:
            return format_html('<span style="color: green;">✓ Valid</span>')
    is_expired_now.short_description = 'Status'
