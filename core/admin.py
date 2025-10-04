from django.contrib import admin
from .models import SiteConfiguration, AuditLog, YouTubeVideo

@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ['key', 'value_preview', 'is_active', 'updated_at']
    list_filter = ['is_active', 'updated_at']
    search_fields = ['key', 'value', 'description']
    readonly_fields = ['updated_at']

    def value_preview(self, obj):
        return obj.value[:50] + "..." if len(obj.value) > 50 else obj.value
    value_preview.short_description = "Value"

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model_name', 'object_id', 'timestamp']
    list_filter = ['action', 'model_name', 'timestamp']
    search_fields = ['user__username', 'action', 'model_name', 'object_id']
    readonly_fields = ['user', 'action', 'model_name', 'object_id', 'changes', 'ip_address', 'user_agent', 'timestamp']

@admin.register(YouTubeVideo)
class YouTubeVideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'is_featured', 'display_order', 'created_at']
    list_filter = ['is_active', 'is_featured', 'created_at']
    search_fields = ['title', 'description']
    list_editable = ['is_active', 'is_featured', 'display_order']
    readonly_fields = ['created_at', 'updated_at', 'get_video_id', 'get_embed_url', 'get_thumbnail_url']

    fieldsets = (
        ('Video Information', {
            'fields': ('title', 'youtube_url', 'description')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'is_featured', 'display_order')
        }),
        ('Optional', {
            'fields': ('thumbnail_url',),
            'classes': ('collapse',)
        }),
        ('Auto-Generated URLs', {
            'fields': ('get_video_id', 'get_embed_url', 'get_thumbnail_url'),
            'classes': ('collapse',),
            'description': 'These fields are automatically generated from the YouTube URL'
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
