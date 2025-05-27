from django.contrib import admin
from django.utils import timezone
from .models import ReportCategory, Report, BannedUser, ForbiddenKeyword, ListingApproval, ModerationLog

@admin.register(ReportCategory)
class ReportCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    search_fields = ('name', 'description')
    list_filter = ('is_active',)

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'content_type', 'reporter', 'status', 'created_at')
    list_filter = ('status', 'content_type', 'category', 'created_at')
    search_fields = ('description', 'reporter__username', 'reported_user__username')
    readonly_fields = ('created_at', 'updated_at', 'reporter')
    
    fieldsets = (
        ('Report Information', {
            'fields': ('reporter', 'content_type', 'category', 'description', 'status')
        }),
        ('Reported Content', {
            'fields': ('listing', 'review', 'reported_user', 'message')
        }),
        ('Moderation', {
            'fields': ('moderator', 'moderator_notes', 'action_taken', 'resolved_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_resolved', 'mark_as_in_progress', 'mark_as_rejected']
    
    def mark_as_resolved(self, request, queryset):
        queryset.update(status='resolved', moderator=request.user, resolved_at=timezone.now())
        self.message_user(request, f"{queryset.count()} reports have been marked as resolved.")
    mark_as_resolved.short_description = "Mark selected reports as resolved"
    
    def mark_as_in_progress(self, request, queryset):
        queryset.update(status='in_progress', moderator=request.user)
        self.message_user(request, f"{queryset.count()} reports have been marked as in progress.")
    mark_as_in_progress.short_description = "Mark selected reports as in progress"
    
    def mark_as_rejected(self, request, queryset):
        queryset.update(status='rejected', moderator=request.user, resolved_at=timezone.now())
        self.message_user(request, f"{queryset.count()} reports have been marked as rejected.")
    mark_as_rejected.short_description = "Mark selected reports as rejected"

@admin.register(BannedUser)
class BannedUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_permanent', 'banned_until', 'banned_by', 'created_at')
    list_filter = ('is_permanent', 'created_at')
    search_fields = ('user__username', 'user__email', 'reason')
    readonly_fields = ('created_at', 'updated_at')
    
    actions = ['remove_ban']
    
    def remove_ban(self, request, queryset):
        queryset.delete()
        self.message_user(request, f"Bans have been removed for {queryset.count()} users.")
    remove_ban.short_description = "Remove ban for selected users"

@admin.register(ForbiddenKeyword)
class ForbiddenKeywordAdmin(admin.ModelAdmin):
    list_display = ('keyword', 'replacement', 'severity', 'is_regex', 'is_active')
    list_filter = ('severity', 'is_regex', 'is_active')
    search_fields = ('keyword', 'replacement', 'notes')
    readonly_fields = ('created_at', 'updated_at')
    
    actions = ['activate_keywords', 'deactivate_keywords']
    
    def activate_keywords(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} keywords have been activated.")
    activate_keywords.short_description = "Activate selected keywords"
    
    def deactivate_keywords(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} keywords have been deactivated.")
    deactivate_keywords.short_description = "Deactivate selected keywords"

@admin.register(ListingApproval)
class ListingApprovalAdmin(admin.ModelAdmin):
    list_display = ('listing', 'status', 'moderator', 'approval_score', 'created_at', 'reviewed_at')
    list_filter = ('status', 'created_at', 'reviewed_at')
    search_fields = ('listing__title', 'listing__host__username', 'moderator__username')
    readonly_fields = ('created_at', 'updated_at', 'approval_score')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('listing', 'status', 'moderator')
        }),
        ('Критерии оценки', {
            'fields': (
                'has_valid_title', 'has_valid_description', 'has_valid_images',
                'has_valid_address', 'has_appropriate_pricing', 'follows_content_policy'
            )
        }),
        ('Заметки и причины', {
            'fields': ('moderator_notes', 'rejection_reason', 'required_changes')
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at', 'reviewed_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(ModerationLog)
class ModerationLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'moderator', 'action_type', 'target_user', 'target_listing')
    list_filter = ('action_type', 'created_at')
    search_fields = ('moderator__username', 'target_user__username', 'target_listing__title', 'description')
    readonly_fields = ('created_at',)
    
    def has_add_permission(self, request):
        return False  # Logs should only be created programmatically
