
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from listings.models import Listing
from .services import SubscriptionService
from .models import UserSubscription, SubscriptionLog
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Listing)
def update_subscription_usage_on_listing_save(sender, instance, created, **kwargs):
    """Update subscription usage when a listing is created or activated"""
    if created and instance.is_active:
        # New active listing created
        SubscriptionService.update_usage_on_ad_created(instance.host)
        logger.info(f"Updated subscription usage for user {instance.host.username} - listing created")
    
    elif not created and instance.is_active:
        # Check if listing was just activated
        if kwargs.get('update_fields') and 'is_active' in kwargs['update_fields']:
            try:
                old_instance = Listing.objects.get(pk=instance.pk)
                if not old_instance.is_active and instance.is_active:
                    SubscriptionService.update_usage_on_ad_created(instance.host)
                    logger.info(f"Updated subscription usage for user {instance.host.username} - listing activated")
            except Listing.DoesNotExist:
                pass

@receiver(post_delete, sender=Listing)
def update_subscription_usage_on_listing_delete(sender, instance, **kwargs):
    """Update subscription usage when a listing is deleted"""
    if instance.is_active:
        SubscriptionService.update_usage_on_ad_deleted(instance.host)
        logger.info(f"Updated subscription usage for user {instance.host.username} - listing deleted")

@receiver(post_save, sender=UserSubscription)
def log_subscription_changes(sender, instance, created, **kwargs):
    """Log subscription status changes"""
    if created:
        SubscriptionLog.objects.create(
            subscription=instance,
            action='created',
            description=f"Subscription created for plan {instance.plan.name}",
            metadata={
                'plan_id': instance.plan.id,
                'amount_paid': str(instance.amount_paid),
                'auto_renew': instance.auto_renew
            }
        )
    else:
        # Check if status changed
        if kwargs.get('update_fields'):
            if 'status' in kwargs['update_fields']:
                SubscriptionLog.objects.create(
                    subscription=instance,
                    action='status_changed',
                    description=f"Subscription status changed to {instance.status}",
                    metadata={'new_status': instance.status}
                )
