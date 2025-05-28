"""
Signal handlers for the notifications app.

This module contains signal handlers for notification-related events
and connections to other app signals that should generate notifications.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()

# Try to import models - they might not be loaded during startup
try:
    from .models import Notification
    from chat.models import Message
    from listings.models import Booking, Review
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False

# Only register signals if models are available
if MODELS_AVAILABLE:
    @receiver(post_save, sender=Message)
    def create_message_notification(sender, instance, created, **kwargs):
        """
        Create a notification when a new message is received.
        """
        if created and instance.sender != instance.conversation.participants.all():
            # Create notifications for all other participants
            for user in instance.conversation.participants.all():
                if user != instance.sender:
                    Notification.objects.create(
                        user=user,
                        notification_type='message_received',
                        title=f"New message",
                        message=f"New message from {instance.sender.username}",
                        conversation=instance.conversation,
                    )

    @receiver(pre_save, sender=Booking)
    def store_booking_original_status(sender, instance, **kwargs):
        """Store original booking status before save"""
        if instance.pk:
            try:
                instance._original_status = Booking.objects.get(pk=instance.pk).status
            except Booking.DoesNotExist:
                instance._original_status = None
        else:
            instance._original_status = None

    @receiver(post_save, sender=Booking)
    def create_booking_notification(sender, instance, created, **kwargs):
        """
        Create a notification when a booking status changes.
        """
        if not created and hasattr(instance, '_original_status'):
            # Check if status changed
            if instance._original_status and instance._original_status != instance.status:
                # Notify guest of booking status change
                if instance.status == 'confirmed':
                    notification_type = 'booking_confirmed'
                    title = "Booking Confirmed"
                    message = f"Your booking for {instance.listing.title} has been confirmed!"
                elif instance.status == 'canceled':
                    notification_type = 'booking_canceled'
                    title = "Booking Canceled"
                    message = f"Your booking for {instance.listing.title} has been canceled."
                else:
                    notification_type = 'system'
                    title = f"Booking {instance.status.capitalize()}"
                    message = f"Your booking for {instance.listing.title} status changed to {instance.status}"

            Notification.objects.create(
                user=instance.guest,
                notification_type=notification_type,
                title=title,
                message=message,
                booking=instance,
                listing=instance.listing,
            )

    @receiver(post_save, sender=Review)
    def create_review_notification(sender, instance, created, **kwargs):
        """
        Create a notification when a new review is posted.
        """
        if created:
            # Notify listing host
            Notification.objects.create(
                user=instance.listing.host,
                notification_type='review_received',
                title="New Review",
                message=f"New review for {instance.listing.title}",
                listing=instance.listing,
                review=instance,
            )