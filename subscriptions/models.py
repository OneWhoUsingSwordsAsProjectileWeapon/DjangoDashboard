
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
import uuid
from datetime import timedelta

class SubscriptionPlan(models.Model):
    """
    Subscription plan model with different tiers
    """
    PLAN_TYPES = [
        ('basic', _('Basic')),
        ('premium', _('Premium')),
        ('business', _('Business')),
        ('enterprise', _('Enterprise')),
    ]
    
    name = models.CharField(_("Plan name"), max_length=100)
    slug = models.SlugField(_("Slug"), unique=True)
    plan_type = models.CharField(_("Plan type"), max_length=20, choices=PLAN_TYPES)
    description = models.TextField(_("Description"), blank=True)
    
    # Pricing
    price = models.DecimalField(_("Price"), max_digits=10, decimal_places=2)
    currency = models.CharField(_("Currency"), max_length=3, default='USD')
    
    # Duration
    duration_days = models.PositiveIntegerField(_("Duration in days"))
    
    # Limits
    ads_limit = models.PositiveIntegerField(_("Ads limit"), help_text=_("Maximum number of active ads"))
    featured_ads_limit = models.PositiveIntegerField(_("Featured ads limit"), default=0)
    premium_features = models.JSONField(_("Premium features"), default=list, blank=True)
    
    # Status
    is_active = models.BooleanField(_("Is active"), default=True)
    is_popular = models.BooleanField(_("Is popular"), default=False)
    
    # Timestamps
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    
    class Meta:
        verbose_name = _("Subscription Plan")
        verbose_name_plural = _("Subscription Plans")
        ordering = ['price']
    
    def __str__(self):
        return f"{self.name} - ${self.price}/{self.duration_days} days"

class UserSubscription(models.Model):
    """
    User subscription model
    """
    STATUS_CHOICES = [
        ('active', _('Active')),
        ('expired', _('Expired')),
        ('canceled', _('Canceled')),
        ('pending', _('Pending')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    
    # Subscription details
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateTimeField(_("Start date"))
    end_date = models.DateTimeField(_("End date"))
    
    # Auto-renewal
    auto_renew = models.BooleanField(_("Auto renew"), default=False)
    
    # Payment
    payment_reference = models.UUIDField(_("Payment reference"), default=uuid.uuid4, editable=False)
    amount_paid = models.DecimalField(_("Amount paid"), max_digits=10, decimal_places=2)
    
    # Timestamps
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    
    class Meta:
        verbose_name = _("User Subscription")
        verbose_name_plural = _("User Subscriptions")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name} ({self.status})"
    
    @property
    def is_active(self):
        """Check if subscription is currently active"""
        now = timezone.now()
        return (
            self.status == 'active' and 
            self.start_date <= now <= self.end_date
        )
    
    @property
    def days_remaining(self):
        """Calculate days remaining in subscription"""
        if not self.is_active:
            return 0
        remaining = self.end_date - timezone.now()
        return max(0, remaining.days)
    
    @property
    def is_expiring_soon(self):
        """Check if subscription expires within 3 days"""
        return self.is_active and self.days_remaining <= 3
    
    def extend(self, days):
        """Extend subscription by given number of days"""
        self.end_date += timedelta(days=days)
        self.save(update_fields=['end_date'])
    
    def cancel(self):
        """Cancel subscription"""
        self.status = 'canceled'
        self.auto_renew = False
        self.save(update_fields=['status', 'auto_renew'])
    
    def renew(self):
        """Renew subscription for another period"""
        if self.auto_renew and self.plan.is_active:
            self.start_date = self.end_date
            self.end_date = self.start_date + timedelta(days=self.plan.duration_days)
            self.status = 'active'
            self.save(update_fields=['start_date', 'end_date', 'status'])
            return True
        return False

class SubscriptionUsage(models.Model):
    """
    Track subscription usage and limits
    """
    subscription = models.OneToOneField(
        UserSubscription,
        on_delete=models.CASCADE,
        related_name='usage'
    )
    
    # Current usage
    ads_count = models.PositiveIntegerField(_("Active ads count"), default=0)
    featured_ads_count = models.PositiveIntegerField(_("Featured ads count"), default=0)
    
    # Historical data
    total_ads_created = models.PositiveIntegerField(_("Total ads created"), default=0)
    last_ad_created = models.DateTimeField(_("Last ad created"), null=True, blank=True)
    
    # Timestamps
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    
    class Meta:
        verbose_name = _("Subscription Usage")
        verbose_name_plural = _("Subscription Usage")
    
    def __str__(self):
        return f"Usage for {self.subscription}"
    
    def can_create_ad(self):
        """Check if user can create a new ad"""
        if not self.subscription.is_active:
            return False, _("Subscription is not active")
        
        if self.ads_count >= self.subscription.plan.ads_limit:
            return False, _("Ad limit reached for current plan")
        
        return True, ""
    
    def increment_ads_count(self):
        """Increment ads count"""
        self.ads_count += 1
        self.total_ads_created += 1
        self.last_ad_created = timezone.now()
        self.save()
    
    def decrement_ads_count(self):
        """Decrement ads count"""
        if self.ads_count > 0:
            self.ads_count -= 1
            self.save()

class SubscriptionLog(models.Model):
    """
    Log subscription-related events
    """
    ACTION_TYPES = [
        ('created', _('Created')),
        ('activated', _('Activated')),
        ('renewed', _('Renewed')),
        ('canceled', _('Canceled')),
        ('expired', _('Expired')),
        ('limit_check', _('Limit Check')),
        ('payment', _('Payment')),
    ]
    
    subscription = models.ForeignKey(
        UserSubscription,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    action = models.CharField(_("Action"), max_length=20, choices=ACTION_TYPES)
    description = models.TextField(_("Description"))
    metadata = models.JSONField(_("Metadata"), default=dict, blank=True)
    
    # User who performed the action (for admin actions)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subscription_actions'
    )
    
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Subscription Log")
        verbose_name_plural = _("Subscription Logs")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.subscription} - {self.action}"

class DefaultSubscriptionSettings(models.Model):
    """
    Default subscription settings for new users
    """
    name = models.CharField(_("Setting name"), max_length=100, unique=True)
    value = models.TextField(_("Value"))
    description = models.TextField(_("Description"), blank=True)
    
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    
    class Meta:
        verbose_name = _("Default Subscription Setting")
        verbose_name_plural = _("Default Subscription Settings")
    
    def __str__(self):
        return self.name
    
    @classmethod
    def get_setting(cls, name, default=None):
        """Get a setting value"""
        try:
            return cls.objects.get(name=name).value
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_setting(cls, name, value, description=""):
        """Set a setting value"""
        setting, created = cls.objects.update_or_create(
            name=name,
            defaults={'value': value, 'description': description}
        )
        return setting
