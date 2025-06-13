from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext as _
from django.db import transaction
from datetime import timedelta
from .models import (
    SubscriptionPlan, UserSubscription, SubscriptionUsage, 
    SubscriptionLog, DefaultSubscriptionSettings
)
from listings.models import Listing
import logging

from django.db.models import Sum, Count, Q
from decimal import Decimal

logger = logging.getLogger(__name__)

class SubscriptionService:
    @staticmethod
    def get_current_subscription(user):
        """Get user's current active subscription"""
        try:
            return UserSubscription.objects.filter(
                user=user,
                status='active',
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now()
            ).select_related('plan').first()
        except Exception as e:
            logger.error(f"Error getting current subscription for user {user.id}: {e}")
            return None

    @staticmethod
    def get_ads_limits(user_id):
        """Get ad limits for user"""
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)

            current_subscription = SubscriptionService.get_current_subscription(user)

            if not current_subscription:
                # Return free tier limits
                return {
                    'current': 0,  # Count user's current ads
                    'limit': 2,    # Free tier limit
                    'plan_name': 'Free',
                    'subscription_status': 'none'
                }

            # Get usage
            try:
                usage = current_subscription.usage
                current_ads = usage.ads_count
            except SubscriptionUsage.DoesNotExist:
                current_ads = 0

            return {
                'current': current_ads,
                'limit': current_subscription.plan.ads_limit,
                'plan_name': current_subscription.plan.name,
                'subscription_status': 'active' if current_subscription.is_active else 'expired',
                'expires_at': current_subscription.end_date,
                'days_remaining': current_subscription.days_remaining
            }
        except Exception as e:
            logger.error(f"Error getting ads limits for user {user_id}: {e}")
            return {
                'current': 0,
                'limit': 0,
                'plan_name': 'Error',
                'subscription_status': 'error'
            }

    @staticmethod
    def can_create_ad(user_id):
        """Check if user can create a new ad"""
        limits = SubscriptionService.get_ads_limits(user_id)

        if limits['subscription_status'] == 'error':
            return False, "Ошибка проверки подписки"

        if limits['current'] >= limits['limit']:
            return False, f"Достигнут лимит объявлений ({limits['limit']}) для плана {limits['plan_name']}"

        return True, ""

    @staticmethod
    def create_subscription(user, plan, payment_reference=None, auto_renew=False):
        """Create a new subscription for user"""
        import uuid
        from datetime import timedelta

        if not payment_reference:
            payment_reference = str(uuid.uuid4())

        # Cancel any existing active subscriptions
        UserSubscription.objects.filter(
            user=user,
            status='active'
        ).update(status='canceled')

        # Create new subscription
        start_date = timezone.now()
        end_date = start_date + timedelta(days=plan.duration_days)

        subscription = UserSubscription.objects.create(
            user=user,
            plan=plan,
            status='active',
            start_date=start_date,
            end_date=end_date,
            auto_renew=auto_renew,
            payment_reference=payment_reference,
            amount_paid=plan.price
        )

        # Create usage tracking
        SubscriptionUsage.objects.create(
            subscription=subscription,
            ads_count=0,
            featured_ads_count=0,
            total_ads_created=0
        )

        return subscription

    @staticmethod
    def get_subscription_stats():
        """Get subscription statistics for admin dashboard"""
        try:
            total_subscriptions = UserSubscription.objects.count()
            active_subscriptions = UserSubscription.objects.filter(
                status='active',
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now()
            ).count()
            expired_subscriptions = UserSubscription.objects.filter(
                status='expired'
            ).count()

            # Calculate total revenue
            total_revenue = UserSubscription.objects.aggregate(
                total=Sum('amount_paid')
            )['total'] or Decimal('0.00')

            # Plans distribution
            plans_distribution = {}
            plans_data = UserSubscription.objects.filter(
                status='active'
            ).values('plan__name').annotate(
                count=Count('id')
            ).order_by('-count')

            for plan_data in plans_data:
                plans_distribution[plan_data['plan__name']] = plan_data['count']

            return {
                'total_subscriptions': total_subscriptions,
                'active_subscriptions': active_subscriptions,
                'expired_subscriptions': expired_subscriptions,
                'total_revenue': float(total_revenue),
                'plans_distribution': plans_distribution
            }
        except Exception as e:
            logger.error(f"Error getting subscription stats: {e}")
            return {
                'total_subscriptions': 0,
                'active_subscriptions': 0,
                'expired_subscriptions': 0,
                'total_revenue': 0.0,
                'plans_distribution': {}
            }
    
    @staticmethod
    def update_usage_on_ad_created(user):
        """Update subscription usage when ad is created"""
        current_subscription = SubscriptionService.get_current_subscription(user)
        if current_subscription:
            usage, created = SubscriptionUsage.objects.get_or_create(
                subscription=current_subscription
            )
            usage.increment_ads_count()
    
    @staticmethod
    def update_usage_on_ad_deleted(user):
        """Update subscription usage when ad is deleted"""
        current_subscription = SubscriptionService.get_current_subscription(user)
        if current_subscription:
            try:
                usage = current_subscription.usage
                usage.decrement_ads_count()
            except SubscriptionUsage.DoesNotExist:
                pass

class NotificationService:
    """
    Service for subscription-related notifications
    """
    
    @staticmethod
    def notify_expiring_subscriptions():
        """Send notifications for expiring subscriptions"""
        expiring_subscriptions = UserSubscription.objects.filter(
            status='active',
            end_date__lte=timezone.now() + timedelta(days=3),
            end_date__gte=timezone.now()
        )
        
        for subscription in expiring_subscriptions:
            NotificationService.send_expiration_warning(subscription)
    
    @staticmethod
    def send_expiration_warning(subscription):
        """Send expiration warning notification"""
        from notifications.models import Notification
        
        Notification.objects.create(
            user=subscription.user,
            notification_type='subscription_expiring',
            title=_("Subscription Expiring Soon"),
            message=_(
                "Your {} subscription will expire in {} days. "
                "Renew now to continue enjoying premium features."
            ).format(subscription.plan.name, subscription.days_remaining),
            metadata={
                'subscription_id': subscription.id,
                'plan_name': subscription.plan.name,
                'days_remaining': subscription.days_remaining
            }
        )
        
        logger.info(f"Sent expiration warning to user {subscription.user.username}")
    
    @staticmethod
    def send_renewal_success(subscription):
        """Send successful renewal notification"""
        from notifications.models import Notification
        
        Notification.objects.create(
            user=subscription.user,
            notification_type='subscription_renewed',
            title=_("Subscription Renewed Successfully"),
            message=_(
                "Your {} subscription has been renewed successfully. "
                "It will expire on {}."
            ).format(subscription.plan.name, subscription.end_date.strftime('%B %d, %Y')),
            metadata={
                'subscription_id': subscription.id,
                'plan_name': subscription.plan.name,
                'end_date': subscription.end_date.isoformat()
            }
        )
    
    @staticmethod
    def send_renewal_failed(subscription, error_message):
        """Send failed renewal notification"""
        from notifications.models import Notification
        
        Notification.objects.create(
            user=subscription.user,
            notification_type='subscription_renewal_failed',
            title=_("Subscription Renewal Failed"),
            message=_(
                "We couldn't renew your {} subscription automatically. "
                "Please update your payment method or renew manually. Error: {}"
            ).format(subscription.plan.name, error_message),
            metadata={
                'subscription_id': subscription.id,
                'plan_name': subscription.plan.name,
                'error_message': error_message
            }
        )