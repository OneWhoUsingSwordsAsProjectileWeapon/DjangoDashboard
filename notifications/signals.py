"""
Signal handlers for the notifications app.

This module contains signal handlers for notification-related events
and connections to other app signals that should generate notifications.
"""

from django.db.models.signals import post_save
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
    
    @receiver(post_save, sender=Booking)
    def create_booking_notification(sender, instance, created, **kwargs):
        """
        Create a notification when a booking status changes.
        """
        if created:
            # Notify host of new booking
            Notification.objects.create(
                user=instance.listing.host,
                notification_type='booking_request',
                title="New Booking Request",
                message=f"New booking request for {instance.listing.title}",
                booking=instance,
                listing=instance.listing,
            )
        else:
            # Check if status changed
            if hasattr(instance, 'tracker') and instance.tracker.has_changed('status'):
                # Notify guest of booking status change
                # Determine notification type based on status
                notification_type = 'booking_confirmed' if instance.status == 'confirmed' else 'booking_canceled'
                
                Notification.objects.create(
                    user=instance.guest,
                    notification_type=notification_type,
                    title=f"Booking {instance.status.capitalize()}",
                    message=f"Your booking for {instance.listing.title} is now {instance.status}",
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