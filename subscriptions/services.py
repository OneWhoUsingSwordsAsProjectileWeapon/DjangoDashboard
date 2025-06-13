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

from django.db.models import Sum, Count, Q, Avg, F
from decimal import Decimal
from django.db.models.functions import TruncMonth, TruncQuarter, Extract

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

    @staticmethod
    def get_analytics_data(start_date=None, end_date=None, days=None):
        """Get comprehensive analytics data"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Determine date range
        if days:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=int(days))
        elif not start_date or not end_date:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=365)
        
        # Base queryset
        subscriptions = UserSubscription.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Summary statistics
        summary = SubscriptionService.get_summary_stats(subscriptions)
        
        # Revenue by month
        monthly_revenue = SubscriptionService.get_monthly_revenue(subscriptions)
        
        # Revenue by quarter
        quarterly_revenue = SubscriptionService.get_quarterly_revenue(subscriptions)
        
        # Seasonal data
        seasonal_data = SubscriptionService.get_seasonal_data()
        
        # Plans distribution
        plans_distribution = SubscriptionService.get_plans_distribution(subscriptions)
        
        # Conversion and retention data
        conversion_data = SubscriptionService.get_conversion_data(start_date, end_date)
        
        # ARPU data
        arpu_data = SubscriptionService.get_arpu_data(subscriptions)
        
        # Recent subscriptions
        recent_subscriptions = SubscriptionService.get_recent_subscriptions()
        
        # Seasonal insights
        seasonal_insights = SubscriptionService.get_seasonal_insights()
        
        return {
            'summary': summary,
            'monthly_revenue': monthly_revenue,
            'quarterly_revenue': quarterly_revenue,
            'seasonal_data': seasonal_data,
            'plans_distribution': plans_distribution,
            'conversion_data': conversion_data,
            'arpu_data': arpu_data,
            'recent_subscriptions': recent_subscriptions,
            'seasonal_insights': seasonal_insights
        }
    
    @staticmethod
    def get_summary_stats(subscriptions):
        """Get summary statistics with period comparisons"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        
        # Current stats
        total_subscriptions = UserSubscription.objects.count()
        active_subscriptions = UserSubscription.objects.filter(
            status='active',
            start_date__lte=now,
            end_date__gte=now
        ).count()
        expired_subscriptions = UserSubscription.objects.filter(status='expired').count()
        total_revenue = UserSubscription.objects.aggregate(
            total=Sum('amount_paid')
        )['total'] or Decimal('0.00')
        
        # Previous period for comparison
        prev_period_subscriptions = UserSubscription.objects.filter(
            created_at__gte=last_month_start,
            created_at__lt=current_month_start
        ).count()
        
        current_period_subscriptions = UserSubscription.objects.filter(
            created_at__gte=current_month_start
        ).count()
        
        prev_period_revenue = UserSubscription.objects.filter(
            created_at__gte=last_month_start,
            created_at__lt=current_month_start
        ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
        
        current_period_revenue = UserSubscription.objects.filter(
            created_at__gte=current_month_start
        ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
        
        # Calculate changes
        subscriptions_change = 0
        if prev_period_subscriptions > 0:
            subscriptions_change = ((current_period_subscriptions - prev_period_subscriptions) / prev_period_subscriptions) * 100
        
        revenue_change = 0
        if prev_period_revenue > 0:
            revenue_change = float(((current_period_revenue - prev_period_revenue) / prev_period_revenue) * 100)
        
        # Churn rate (expired in last 30 days / total active at start of period)
        thirty_days_ago = now - timedelta(days=30)
        expired_last_30 = UserSubscription.objects.filter(
            status='expired',
            end_date__gte=thirty_days_ago
        ).count()
        
        active_30_days_ago = UserSubscription.objects.filter(
            status='active',
            start_date__lte=thirty_days_ago
        ).count()
        
        churn_rate = (expired_last_30 / active_30_days_ago * 100) if active_30_days_ago > 0 else 0
        
        return {
            'total_subscriptions': total_subscriptions,
            'active_subscriptions': active_subscriptions,
            'expired_subscriptions': expired_subscriptions,
            'total_revenue': float(total_revenue),
            'changes': {
                'subscriptions_change': subscriptions_change,
                'revenue_change': revenue_change,
                'churn_rate': churn_rate
            }
        }
    
    @staticmethod
    def get_monthly_revenue(subscriptions):
        """Get monthly revenue breakdown"""
        monthly_data = subscriptions.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            revenue=Sum('amount_paid'),
            count=Count('id')
        ).order_by('month')
        
        result = []
        for item in monthly_data:
            result.append({
                'label': item['month'].strftime('%B %Y'),
                'revenue': float(item['revenue'] or 0),
                'subscriptions': item['count']
            })
        
        return result
    
    @staticmethod
    def get_quarterly_revenue(subscriptions):
        """Get quarterly revenue breakdown"""
        quarterly_data = subscriptions.annotate(
            quarter=TruncQuarter('created_at')
        ).values('quarter').annotate(
            revenue=Sum('amount_paid'),
            count=Count('id')
        ).order_by('quarter')
        
        result = []
        for item in quarterly_data:
            quarter_num = ((item['quarter'].month - 1) // 3) + 1
            result.append({
                'label': f"Q{quarter_num} {item['quarter'].year}",
                'revenue': float(item['revenue'] or 0),
                'subscriptions': item['count']
            })
        
        return result
    
    @staticmethod
    def get_seasonal_data():
        """Get seasonal analysis data"""
        all_subscriptions = UserSubscription.objects.all()
        
        # Group by month across all years
        monthly_stats = {}
        month_names = [
            '', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
            'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
        ]
        
        for month in range(1, 13):
            month_data = all_subscriptions.filter(
                created_at__month=month
            ).aggregate(
                revenue=Sum('amount_paid'),
                count=Count('id')
            )
            
            monthly_stats[month_names[month]] = {
                'revenue': float(month_data['revenue'] or 0),
                'subscriptions': month_data['count']
            }
        
        return {
            'monthly_revenue': [monthly_stats[month]['revenue'] for month in month_names[1:]],
            'monthly_subscriptions': [monthly_stats[month]['subscriptions'] for month in month_names[1:]]
        }
    
    @staticmethod
    def get_plans_distribution(subscriptions):
        """Get distribution by subscription plans"""
        distribution = subscriptions.values('plan__name').annotate(
            count=Count('id')
        ).order_by('-count')
        
        result = {}
        for item in distribution:
            result[item['plan__name']] = item['count']
        
        return result
    
    @staticmethod
    def get_conversion_data(start_date, end_date):
        """Get conversion and retention data"""
        from django.contrib.auth import get_user_model
        from dateutil.relativedelta import relativedelta
        
        User = get_user_model()
        
        # Generate monthly data points
        current = start_date
        labels = []
        conversion = []
        retention = []
        
        while current <= end_date:
            month_end = current + relativedelta(months=1)
            
            # Total users registered in this month
            total_users = User.objects.filter(
                date_joined__gte=current,
                date_joined__lt=month_end
            ).count()
            
            # Users who subscribed in this month
            subscribed_users = UserSubscription.objects.filter(
                created_at__gte=current,
                created_at__lt=month_end,
                user__date_joined__gte=current,
                user__date_joined__lt=month_end
            ).values('user').distinct().count()
            
            # Conversion rate
            conv_rate = (subscribed_users / total_users * 100) if total_users > 0 else 0
            
            # Retention: users who renewed after their first subscription
            renewal_month = current + relativedelta(months=1)
            renewed_users = UserSubscription.objects.filter(
                created_at__gte=renewal_month,
                created_at__lt=renewal_month + relativedelta(months=1),
                user__in=UserSubscription.objects.filter(
                    created_at__gte=current,
                    created_at__lt=month_end
                ).values('user')
            ).values('user').distinct().count()
            
            retention_rate = (renewed_users / subscribed_users * 100) if subscribed_users > 0 else 0
            
            labels.append(current.strftime('%B %Y'))
            conversion.append(round(conv_rate, 2))
            retention.append(round(retention_rate, 2))
            
            current = month_end
        
        return {
            'labels': labels,
            'conversion': conversion,
            'retention': retention
        }
    
    @staticmethod
    def get_arpu_data(subscriptions):
        """Get Average Revenue Per User data"""
        monthly_arpu = subscriptions.annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            total_revenue=Sum('amount_paid'),
            user_count=Count('user', distinct=True)
        ).order_by('month')
        
        labels = []
        values = []
        
        for item in monthly_arpu:
            if item['user_count'] > 0:
                arpu = float(item['total_revenue']) / item['user_count']
                labels.append(item['month'].strftime('%B %Y'))
                values.append(round(arpu, 2))
        
        return {
            'labels': labels,
            'values': values
        }
    
    @staticmethod
    def get_recent_subscriptions(limit=10):
        """Get recent subscriptions for table display"""
        recent = UserSubscription.objects.select_related(
            'user', 'plan'
        ).order_by('-created_at')[:limit]
        
        result = []
        for subscription in recent:
            result.append({
                'user': subscription.user.username,
                'plan': subscription.plan.name,
                'status': subscription.status,
                'start_date': subscription.start_date.isoformat(),
                'end_date': subscription.end_date.isoformat(),
                'amount_paid': float(subscription.amount_paid),
                'auto_renew': subscription.auto_renew
            })
        
        return result
    
    @staticmethod
    def get_seasonal_insights():
        """Get seasonal insights and patterns"""
        all_subscriptions = UserSubscription.objects.all()
        
        monthly_revenue = {}
        for month in range(1, 13):
            revenue = all_subscriptions.filter(
                created_at__month=month
            ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
            monthly_revenue[month] = float(revenue)
        
        if not monthly_revenue:
            return {}
        
        # Find best and worst months
        best_month_num = max(monthly_revenue, key=monthly_revenue.get)
        worst_month_num = min(monthly_revenue, key=monthly_revenue.get)
        
        month_names = [
            '', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
            'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
        ]
        
        # Calculate seasonality index (coefficient of variation)
        revenues = list(monthly_revenue.values())
        if revenues:
            avg_revenue = sum(revenues) / len(revenues)
            variance = sum((r - avg_revenue) ** 2 for r in revenues) / len(revenues)
            std_dev = variance ** 0.5
            seasonality_index = (std_dev / avg_revenue) * 100 if avg_revenue > 0 else 0
        else:
            seasonality_index = 0
        
        return {
            'best_month': month_names[best_month_num],
            'worst_month': month_names[worst_month_num],
            'seasonality_index': seasonality_index
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