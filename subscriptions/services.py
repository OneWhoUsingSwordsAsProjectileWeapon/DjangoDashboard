
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

logger = logging.getLogger(__name__)

class SubscriptionService:
    """
    Core service for subscription management
    """
    
    @staticmethod
    def can_create_ad(user_id):
        """
        Check if user can create a new ad
        Returns: (bool, str) - (can_create, error_message)
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(id=user_id)
            
            # Admin users have no limits
            if user.is_superuser or user.role == 'admin':
                logger.info(f"Admin user {user.username} bypass subscription check")
                return True, ""
            
            # Get current subscription
            current_subscription = SubscriptionService.get_current_subscription(user)
            
            if not current_subscription:
                # Check if free tier is allowed
                free_ads_limit = int(DefaultSubscriptionSettings.get_setting('free_ads_limit', '0'))
                if free_ads_limit > 0:
                    current_ads = Listing.objects.filter(host=user, is_active=True).count()
                    if current_ads < free_ads_limit:
                        logger.info(f"User {user.username} can create ad (free tier: {current_ads}/{free_ads_limit})")
                        return True, ""
                
                logger.warning(f"User {user.username} has no active subscription")
                return False, _("No active subscription found")
            
            # Check subscription status
            if not current_subscription.is_active:
                logger.warning(f"User {user.username} subscription is not active")
                return False, _("Your subscription has expired")
            
            # Get or create usage tracking
            usage, created = SubscriptionUsage.objects.get_or_create(
                subscription=current_subscription,
                defaults={
                    'ads_count': Listing.objects.filter(host=user, is_active=True).count()
                }
            )
            
            # Check limits
            can_create, error_msg = usage.can_create_ad()
            
            # Log the check
            SubscriptionLog.objects.create(
                subscription=current_subscription,
                action='limit_check',
                description=f"Ad creation check: {can_create}",
                metadata={
                    'current_ads': usage.ads_count,
                    'limit': current_subscription.plan.ads_limit,
                    'result': can_create
                }
            )
            
            if can_create:
                logger.info(f"User {user.username} can create ad ({usage.ads_count}/{current_subscription.plan.ads_limit})")
            else:
                logger.warning(f"User {user.username} cannot create ad: {error_msg}")
            
            return can_create, error_msg
            
        except Exception as e:
            logger.error(f"Error checking ad creation for user {user_id}: {e}")
            return False, _("Error checking subscription status")
    
    @staticmethod
    def get_ads_limits(user_id):
        """
        Get current ads limits for user
        Returns: dict with current and limit counts
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(id=user_id)
            
            # Admin users have unlimited ads
            if user.is_superuser or user.role == 'admin':
                current_ads = Listing.objects.filter(host=user, is_active=True).count()
                return {
                    'current': current_ads,
                    'limit': -1,  # Unlimited
                    'plan_name': 'Admin',
                    'subscription_status': 'admin'
                }
            
            current_subscription = SubscriptionService.get_current_subscription(user)
            current_ads = Listing.objects.filter(host=user, is_active=True).count()
            
            if not current_subscription:
                free_limit = int(DefaultSubscriptionSettings.get_setting('free_ads_limit', '0'))
                return {
                    'current': current_ads,
                    'limit': free_limit,
                    'plan_name': 'Free',
                    'subscription_status': 'none'
                }
            
            return {
                'current': current_ads,
                'limit': current_subscription.plan.ads_limit if current_subscription.is_active else 0,
                'plan_name': current_subscription.plan.name,
                'subscription_status': current_subscription.status,
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
    def get_current_subscription(user):
        """Get user's current active subscription"""
        return UserSubscription.objects.filter(
            user=user,
            status='active',
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).first()
    
    @staticmethod
    @transaction.atomic
    def create_subscription(user, plan, payment_reference=None, auto_renew=False):
        """Create a new subscription for user"""
        try:
            # Cancel any existing active subscriptions
            existing_subscriptions = UserSubscription.objects.filter(
                user=user,
                status='active'
            )
            for sub in existing_subscriptions:
                sub.cancel()
                SubscriptionLog.objects.create(
                    subscription=sub,
                    action='canceled',
                    description="Canceled due to new subscription"
                )
            
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
                amount_paid=plan.price,
                payment_reference=payment_reference
            )
            
            # Create usage tracking
            SubscriptionUsage.objects.create(
                subscription=subscription,
                ads_count=Listing.objects.filter(host=user, is_active=True).count()
            )
            
            # Log creation
            SubscriptionLog.objects.create(
                subscription=subscription,
                action='created',
                description=f"Subscription created for plan {plan.name}",
                metadata={
                    'plan_id': plan.id,
                    'amount_paid': str(plan.price),
                    'auto_renew': auto_renew
                }
            )
            
            logger.info(f"Created subscription for user {user.username} with plan {plan.name}")
            return subscription
            
        except Exception as e:
            logger.error(f"Error creating subscription for user {user.id}: {e}")
            raise
    
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
    
    @staticmethod
    def get_subscription_stats():
        """Get subscription statistics for admin dashboard"""
        total_subscriptions = UserSubscription.objects.count()
        active_subscriptions = UserSubscription.objects.filter(
            status='active',
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).count()
        
        expired_subscriptions = UserSubscription.objects.filter(
            status='expired'
        ).count()
        
        expiring_soon = UserSubscription.objects.filter(
            status='active',
            end_date__lte=timezone.now() + timedelta(days=3),
            end_date__gte=timezone.now()
        ).count()
        
        # Revenue by plan
        from django.db.models import Sum, Count
        plan_stats = SubscriptionPlan.objects.annotate(
            subscription_count=Count('subscriptions'),
            total_revenue=Sum('subscriptions__amount_paid')
        ).filter(subscription_count__gt=0)
        
        return {
            'total_subscriptions': total_subscriptions,
            'active_subscriptions': active_subscriptions,
            'expired_subscriptions': expired_subscriptions,
            'expiring_soon': expiring_soon,
            'plan_stats': plan_stats
        }

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
