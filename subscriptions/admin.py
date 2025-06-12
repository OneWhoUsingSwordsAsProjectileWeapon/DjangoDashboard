
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Sum
from .models import (
    SubscriptionPlan, UserSubscription, SubscriptionUsage,
    SubscriptionLog, DefaultSubscriptionSettings
)

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'plan_type', 'price', 'currency', 'duration_days',
        'ads_limit', 'is_active', 'is_popular', 'subscription_count'
    )
    list_filter = ('plan_type', 'is_active', 'is_popular', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at', 'subscription_count')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'slug', 'plan_type', 'description')
        }),
        (_('Pricing'), {
            'fields': ('price', 'currency', 'duration_days')
        }),
        (_('Limits & Features'), {
            'fields': ('ads_limit', 'featured_ads_limit', 'premium_features')
        }),
        (_('Status'), {
            'fields': ('is_active', 'is_popular')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at', 'subscription_count'),
            'classes': ('collapse',)
        })
    )
    
    def subscription_count(self, obj):
        """Display subscription count for this plan"""
        count = obj.subscriptions.count()
        if count > 0:
            url = reverse('admin:subscriptions_usersubscription_changelist')
            return format_html(
                '<a href="{}?plan__id__exact={}">{}</a>',
                url, obj.id, count
            )
        return count
    subscription_count.short_description = _('Subscriptions')
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            subscription_count=Count('subscriptions')
        )

class SubscriptionUsageInline(admin.StackedInline):
    model = SubscriptionUsage
    readonly_fields = ('updated_at',)
    extra = 0

class SubscriptionLogInline(admin.TabularInline):
    model = SubscriptionLog
    readonly_fields = ('action', 'description', 'metadata', 'performed_by', 'created_at')
    extra = 0
    max_num = 10
    
    def has_add_permission(self, request, obj):
        return False

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user_link', 'plan', 'status', 'start_date', 'end_date',
        'days_remaining_display', 'auto_renew', 'amount_paid'
    )
    list_filter = (
        'status', 'auto_renew', 'plan', 'created_at', 'start_date', 'end_date'
    )
    search_fields = ('user__username', 'user__email', 'plan__name', 'payment_reference')
    readonly_fields = ('payment_reference', 'created_at', 'updated_at', 'days_remaining_display')
    inlines = [SubscriptionUsageInline, SubscriptionLogInline]
    
    fieldsets = (
        (_('Subscription Details'), {
            'fields': ('user', 'plan', 'status')
        }),
        (_('Duration'), {
            'fields': ('start_date', 'end_date', 'days_remaining_display')
        }),
        (_('Settings'), {
            'fields': ('auto_renew',)
        }),
        (_('Payment'), {
            'fields': ('amount_paid', 'payment_reference')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['activate_subscription', 'cancel_subscription', 'extend_subscription']
    
    def user_link(self, obj):
        """Link to user admin page"""
        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = _('User')
    
    def days_remaining_display(self, obj):
        """Display days remaining with color coding"""
        days = obj.days_remaining
        if not obj.is_active:
            return format_html('<span style="color: #dc3545;">Inactive</span>')
        elif days <= 3:
            return format_html('<span style="color: #fd7e14;">{} days</span>', days)
        else:
            return format_html('<span style="color: #28a745;">{} days</span>', days)
    days_remaining_display.short_description = _('Days Remaining')
    
    def activate_subscription(self, request, queryset):
        """Activate selected subscriptions"""
        count = queryset.update(status='active')
        self.message_user(request, f'{count} subscriptions activated.')
    activate_subscription.short_description = _('Activate selected subscriptions')
    
    def cancel_subscription(self, request, queryset):
        """Cancel selected subscriptions"""
        for subscription in queryset:
            subscription.cancel()
        self.message_user(request, f'{queryset.count()} subscriptions canceled.')
    cancel_subscription.short_description = _('Cancel selected subscriptions')
    
    def extend_subscription(self, request, queryset):
        """Extend selected subscriptions by 30 days"""
        for subscription in queryset:
            subscription.extend(30)
        self.message_user(request, f'{queryset.count()} subscriptions extended by 30 days.')
    extend_subscription.short_description = _('Extend selected subscriptions by 30 days')

@admin.register(SubscriptionUsage)
class SubscriptionUsageAdmin(admin.ModelAdmin):
    list_display = (
        'subscription_link', 'ads_count', 'ads_limit', 'usage_percentage',
        'featured_ads_count', 'total_ads_created', 'updated_at'
    )
    list_filter = ('updated_at', 'subscription__plan')
    search_fields = ('subscription__user__username', 'subscription__plan__name')
    readonly_fields = ('subscription', 'updated_at')
    
    def subscription_link(self, obj):
        """Link to subscription admin page"""
        url = reverse('admin:subscriptions_usersubscription_change', args=[obj.subscription.id])
        return format_html('<a href="{}">{}</a>', url, str(obj.subscription))
    subscription_link.short_description = _('Subscription')
    
    def ads_limit(self, obj):
        """Display ads limit from plan"""
        return obj.subscription.plan.ads_limit
    ads_limit.short_description = _('Ads Limit')
    
    def usage_percentage(self, obj):
        """Display usage percentage with color coding"""
        if obj.subscription.plan.ads_limit == 0:
            return "N/A"
        
        percentage = (obj.ads_count / obj.subscription.plan.ads_limit) * 100
        if percentage >= 90:
            color = '#dc3545'  # Red
        elif percentage >= 70:
            color = '#fd7e14'  # Orange
        else:
            color = '#28a745'  # Green
            
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, percentage
        )
    usage_percentage.short_description = _('Usage %')

@admin.register(SubscriptionLog)
class SubscriptionLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'subscription_link', 'action', 'short_description', 'performed_by', 'created_at')
    list_filter = ('action', 'created_at', 'subscription__plan')
    search_fields = ('subscription__user__username', 'description', 'performed_by__username')
    readonly_fields = ('subscription', 'action', 'description', 'metadata', 'performed_by', 'created_at')
    
    def subscription_link(self, obj):
        """Link to subscription admin page"""
        url = reverse('admin:subscriptions_usersubscription_change', args=[obj.subscription.id])
        return format_html('<a href="{}">{}</a>', url, str(obj.subscription))
    subscription_link.short_description = _('Subscription')
    
    def short_description(self, obj):
        """Truncated description"""
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    short_description.short_description = _('Description')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(DefaultSubscriptionSettings)
class DefaultSubscriptionSettingsAdmin(admin.ModelAdmin):
    list_display = ('name', 'value', 'description', 'updated_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return self.readonly_fields + ('name',)
        return self.readonly_fields
