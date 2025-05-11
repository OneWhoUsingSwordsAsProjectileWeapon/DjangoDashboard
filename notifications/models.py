from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Notification(models.Model):
    """
    Model for storing user notifications
    """
    NOTIFICATION_TYPES = [
        ('booking_request', _('Booking Request')),
        ('booking_confirmed', _('Booking Confirmed')),
        ('booking_canceled', _('Booking Canceled')),
        ('message_received', _('Message Received')),
        ('review_received', _('Review Received')),
        ('listing_approved', _('Listing Approved')),
        ('payment_received', _('Payment Received')),
        ('system', _('System Notification')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_("User")
    )
    notification_type = models.CharField(
        _("Notification Type"),
        max_length=30,
        choices=NOTIFICATION_TYPES
    )
    title = models.CharField(_("Title"), max_length=255)
    message = models.TextField(_("Message"))
    is_read = models.BooleanField(_("Is Read"), default=False)
    # Allow linking to related objects
    booking = models.ForeignKey(
        'listings.Booking',
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True,
        verbose_name=_("Related Booking")
    )
    listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True,
        verbose_name=_("Related Listing")
    )
    conversation = models.ForeignKey(
        'chat.Conversation',
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True,
        verbose_name=_("Related Conversation")
    )
    review = models.ForeignKey(
        'listings.Review',
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True,
        verbose_name=_("Related Review")
    )
    # Timestamps
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} - {self.title} - {self.user.username}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])

class EmailTemplate(models.Model):
    """
    Model for storing email templates
    """
    name = models.CharField(_("Template Name"), max_length=50, unique=True)
    subject = models.CharField(_("Subject"), max_length=255)
    content = models.TextField(_("Content"))
    
    class Meta:
        verbose_name = _("Email Template")
        verbose_name_plural = _("Email Templates")
    
    def __str__(self):
        return self.name
