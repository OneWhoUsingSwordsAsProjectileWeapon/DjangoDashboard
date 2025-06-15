"""
Signal handlers for the listings app.

This module contains signal handlers for listings-related events,
such as handling booking updates, review notifications, etc.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

try:
    from .models import Listing, Booking, Review
    # We'll use this to check if models are available
    LISTING_MODELS_AVAILABLE = True
except ImportError:
    # During initial app loading, models might not be available yet
    LISTING_MODELS_AVAILABLE = False

# Only register signals if the models are available
if LISTING_MODELS_AVAILABLE:
    @receiver(post_save, sender=Booking)
    def booking_created_handler(sender, instance, created, **kwargs):
        """
        Handler for when a booking is created or updated.
        """
        if created:
            # Logic for new booking
            print(f"New booking created: {instance.booking_reference}")

            # You could implement notification logic, availability updates, etc. here
        else:
            # Logic for booking updates
            print(f"Booking updated: {instance.booking_reference}")

    @receiver(post_save, sender=Review)
    def review_created_handler(sender, instance, created, **kwargs):
        """
        Handler for when a review is created.
        """
        if created:
            # Logic for new review
            print(f"New review for listing {instance.listing.id} created")

            # You could implement notification logic, rating updates, etc. here

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Booking, Review, Listing
from notifications.models import Notification

User = get_user_model()

@receiver(post_save, sender=Listing)
def create_listing_moderation_request(sender, instance, created, **kwargs):
    """Create moderation request when listing is created or updated"""
    if not created:  # Only for updates, not new listings
        # Check if listing needs re-moderation
        if instance.is_active and not instance.is_approved:
            # Import here to avoid circular imports
            from moderation.models import ListingApproval

            # Create new approval request
            ListingApproval.objects.create(
                listing=instance,
                status='pending',
                has_verification_video=bool(instance.verification_video)
            )

@receiver(post_save, sender=Booking)
def create_booking_notifications(sender, instance, created, **kwargs):
    """Create notifications for booking events"""
    if created:
        # Notify the host about new booking request
        Notification.objects.create(
            user=instance.listing.host,
            notification_type='booking_request',
            title='Новый запрос на бронирование',
            message=f'Пользователь {instance.guest.first_name or instance.guest.username} хочет забронировать {instance.listing.title}',
            booking=instance,
            listing=instance.listing
        )
    else:
        # Check if status changed
        if instance.status == 'confirmed':
            # Notify guest about confirmation
            Notification.objects.create(
                user=instance.guest,
                notification_type='booking_confirmed',
                title='Бронирование подтверждено',
                message=f'Ваше бронирование {instance.listing.title} было подтверждено',
                booking=instance,
                listing=instance.listing
            )
        elif instance.status == 'canceled':
            # Notify both parties about cancellation
            Notification.objects.create(
                user=instance.guest,
                notification_type='booking_canceled',
                title='Бронирование отменено',
                message=f'Ваше бронирование {instance.listing.title} было отменено',
                booking=instance,
                listing=instance.listing
            )

@receiver(post_save, sender=Review)
def create_review_notification(sender, instance, created, **kwargs):
    """Create notification when review is posted"""
    if created:
        Notification.objects.create(
            user=instance.listing.host,
            notification_type='review_received',
            title='Новый отзыв',
            message=f'Пользователь {instance.user.first_name or instance.user.username} оставил отзыв на {instance.listing.title}',
            listing=instance.listing,
            review=instance
        )