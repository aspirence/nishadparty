from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import MembershipTier, Membership, DocumentVerification, MembershipApplicationSteps

@admin.register(MembershipTier)
class MembershipTierAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'duration_months', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    ordering = ['price']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'price', 'duration_months', 'is_active')
        }),
        ('Benefits', {
            'fields': ('benefits',),
            'description': 'Add benefits as a JSON list, e.g. ["Benefit 1", "Benefit 2"]'
        }),
    )

class DocumentVerificationInline(admin.TabularInline):
    model = DocumentVerification
    extra = 0
    readonly_fields = ['created_at', 'updated_at']
    fields = ['document_type', 'document_number', 'verification_status', 'verified_by', 'rejection_reason']

class MembershipApplicationStepsInline(admin.StackedInline):
    model = MembershipApplicationSteps
    extra = 0
    fields = ['personal_info_completed', 'documents_uploaded', 'payment_completed', 'verification_submitted', 'current_step']

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ['membership_id', 'user_full_name', 'tier', 'verification_status', 'start_date', 'end_date', 'is_active', 'is_expired_status']
    list_filter = ['verification_status', 'is_active', 'tier', 'created_at', 'start_date']
    search_fields = ['membership_id', 'user__first_name', 'user__last_name', 'user__phone_number']
    ordering = ['-created_at']
    readonly_fields = ['membership_id', 'created_at', 'updated_at', 'is_expired_status']

    inlines = [DocumentVerificationInline, MembershipApplicationStepsInline]

    fieldsets = (
        ('Membership Information', {
            'fields': ('membership_id', 'user', 'tier', 'start_date', 'end_date', 'is_active')
        }),
        ('Verification', {
            'fields': ('verification_status', 'verified_by', 'verified_at', 'rejection_reason')
        }),
        ('Payment', {
            'fields': ('payment_id',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def user_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.phone_number
    user_full_name.short_description = 'Member Name'

    def is_expired_status(self, obj):
        if obj.is_expired:
            return format_html('<span style="color: red;">Expired</span>')
        else:
            return format_html('<span style="color: green;">Active</span>')
    is_expired_status.short_description = 'Expiry Status'

    actions = ['approve_memberships', 'reject_memberships', 'mark_active', 'mark_inactive']

    def approve_memberships(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            verification_status='APPROVED',
            verified_by=request.user,
            verified_at=timezone.now()
        )
        self.message_user(request, f'{updated} memberships approved successfully.')
    approve_memberships.short_description = "Approve selected memberships"

    def reject_memberships(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            verification_status='REJECTED',
            verified_by=request.user,
            verified_at=timezone.now()
        )
        self.message_user(request, f'{updated} memberships rejected.')
    reject_memberships.short_description = "Reject selected memberships"

    def mark_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} memberships marked as active.')
    mark_active.short_description = "Mark selected memberships as active"

    def mark_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} memberships marked as inactive.')
    mark_inactive.short_description = "Mark selected memberships as inactive"

@admin.register(DocumentVerification)
class DocumentVerificationAdmin(admin.ModelAdmin):
    list_display = ['membership_id', 'member_name', 'document_type', 'document_number', 'verification_status', 'verified_by', 'created_at']
    list_filter = ['document_type', 'verification_status', 'created_at']
    search_fields = ['membership__membership_id', 'membership__user__first_name', 'membership__user__last_name', 'document_number']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Document Information', {
            'fields': ('membership', 'document_type', 'document_file', 'document_number')
        }),
        ('Verification', {
            'fields': ('verification_status', 'verified_by', 'verified_at', 'rejection_reason', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def membership_id(self, obj):
        return obj.membership.membership_id
    membership_id.short_description = 'Membership ID'

    def member_name(self, obj):
        return obj.membership.user.get_full_name() or obj.membership.user.phone_number
    member_name.short_description = 'Member Name'

    actions = ['verify_documents', 'reject_documents']

    def verify_documents(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            verification_status='VERIFIED',
            verified_by=request.user,
            verified_at=timezone.now()
        )
        self.message_user(request, f'{updated} documents verified successfully.')
    verify_documents.short_description = "Verify selected documents"

    def reject_documents(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(
            verification_status='REJECTED',
            verified_by=request.user,
            verified_at=timezone.now()
        )
        self.message_user(request, f'{updated} documents rejected.')
    reject_documents.short_description = "Reject selected documents"

@admin.register(MembershipApplicationSteps)
class MembershipApplicationStepsAdmin(admin.ModelAdmin):
    list_display = ['membership_id', 'member_name', 'current_step', 'personal_info_completed', 'documents_uploaded', 'payment_completed', 'verification_submitted']
    list_filter = ['current_step', 'personal_info_completed', 'documents_uploaded', 'payment_completed', 'verification_submitted']
    search_fields = ['membership__membership_id', 'membership__user__first_name', 'membership__user__last_name']
    ordering = ['-membership__created_at']

    def membership_id(self, obj):
        return obj.membership.membership_id
    membership_id.short_description = 'Membership ID'

    def member_name(self, obj):
        return obj.membership.user.get_full_name() or obj.membership.user.phone_number
    member_name.short_description = 'Member Name'
