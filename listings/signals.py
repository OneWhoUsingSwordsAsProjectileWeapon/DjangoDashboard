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

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Listing
from notifications.models import Notification

@receiver(post_save, sender=Listing)
def notify_host_listing_created(sender, instance, created, **kwargs):
    """Send notification to host when listing is created and create moderation record"""
    if created:
        # Create notification
        Notification.objects.create(
            user=instance.host,
            notification_type='system',
            title='Объявление создано',
            message=f'Ваше объявление "{instance.title}" успешно создано и отправлено на модерацию.'
        )

        # Create moderation record
        from moderation.models import ListingApproval
        ListingApproval.objects.get_or_create(
            listing=instance,
            defaults={
                'status': 'pending',
                'has_valid_title': False,
                'has_valid_description': False,
                'has_valid_images': False,
                'has_valid_address': False,
                'has_appropriate_pricing': False,
                'follows_content_policy': False,
                'has_verification_video': False
            }
        )
    else:
        # Объявление было изменено - обновляем статус существующей записи модерации
        if not instance.is_approved:
            from moderation.models import ListingApproval
            
            # Получаем или создаем запись модерации
            approval, created = ListingApproval.objects.get_or_create(
                listing=instance,
                defaults={
                    'status': 'pending',
                    'has_verification_video': bool(instance.verification_video)
                }
            )
            
            # Если запись уже существовала, обновляем её статус
            if not created:
                approval.status = 'pending'
                approval.has_verification_video = bool(instance.verification_video)
                approval.moderator = None  # Сбрасываем модератора
                approval.moderator_notes = ''  # Очищаем заметки
                approval.reviewed_at = None  # Сбрасываем дату рассмотрения
                approval.save()
            
            # Уведомляем хоста
            Notification.objects.create(
                user=instance.host,
                notification_type='system',
                title='Объявление отправлено на повторную модерацию',
                message=f'Ваше объявление "{instance.title}" было изменено и отправлено на повторную модерацию.'
            )