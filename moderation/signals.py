from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import UserComplaint
from listings.models import Listing
from .models import ListingApproval, BannedUser
from notifications.tasks import create_notification

@receiver(post_save, sender=UserComplaint)
def handle_complaint_status_change(sender, instance, created, **kwargs):
    """Handle complaint creation and status changes"""
    try:
        from notifications.models import Notification

        if created:
            # Notify moderators about new complaint
            from django.contrib.auth import get_user_model
            User = get_user_model()
            moderators = User.objects.filter(is_staff=True)

            for moderator in moderators:
                Notification.objects.create(
                    user=moderator,
                    notification_type='system',
                    title=f"Новая жалоба #{instance.id}",
                    message=f"Пользователь {instance.complainant.username} подал жалобу: {instance.subject}",
                )
        else:
            # Check if status changed by comparing with original
            if hasattr(instance, '_original_status') and instance._original_status != instance.status:
                # Notify complainant about status change
                status_display = instance.get_status_display()
                Notification.objects.create(
                    user=instance.complainant,
                    notification_type='system',
                    title=f"Обновление жалобы #{instance.id}",
                    message=f"Статус вашей жалобы изменен на: {status_display}",
                )

                # If there's a response, also notify about it
                if instance.moderator_response:
                    Notification.objects.create(
                        user=instance.complainant,
                        notification_type='system',
                        title=f"Ответ на жалобу #{instance.id}",
                        message=f"Модератор ответил на вашу жалобу. Проверьте раздел 'Мои жалобы'.",
                    )
    except ImportError:
        # notifications app not available
        pass

@receiver(pre_save, sender=UserComplaint)
def store_original_complaint_status(sender, instance, **kwargs):
    """Store original complaint status before save"""
    if instance.pk:
        try:
            instance._original_status = UserComplaint.objects.get(pk=instance.pk).status
        except UserComplaint.DoesNotExist:
            instance._original_status = None
    else:
        instance._original_status = None


@receiver(post_save, sender=Listing)
def create_listing_approval(sender, instance, created, **kwargs):
    """Create a listing approval record when a new listing is created"""
    if created:
        ListingApproval.objects.create(listing=instance)


@receiver(post_save, sender=BannedUser)
def handle_user_ban(sender, instance, created, **kwargs):
    """Handle user ban by deactivating their listings and sending notification"""
    if created or instance.is_active:
        # Deactivate all user's listings
        user_listings = Listing.objects.filter(host=instance.user, is_active=True)
        deactivated_count = user_listings.update(is_active=False)

        # Create notification for the banned user
        if instance.is_permanent:
            message = f"Ваша учетная запись была заблокирована навсегда. Причина: {instance.reason}. Все ваши объявления ({deactivated_count}) были деактивированы."
            title = "Учетная запись заблокирована навсегда"
        else:
            ban_until = instance.banned_until.strftime('%d.%m.%Y %H:%M') if instance.banned_until else "неопределенное время"
            message = f"Ваша учетная запись была заблокирована до {ban_until}. Причина: {instance.reason}. Все ваши объявления ({deactivated_count}) были деактивированы."
            title = "Учетная запись временно заблокирована"

        create_notification(
            user=instance.user,
            notification_type='system',
            title=title,
            message=message
        )