from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext as _
from django.db import transaction
from datetime import timedelta, date, datetime
from .models import (
    SubscriptionPlan, UserSubscription, SubscriptionUsage, 
    SubscriptionLog, DefaultSubscriptionSettings
)
from listings.models import Listing
import logging

from django.db.models import Sum, Count, Q, Avg, F
from decimal import Decimal
from django.db.models.functions import TruncMonth, TruncQuarter, Extract
from dateutil.relativedelta import relativedelta

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
            from listings.models import Listing
            User = get_user_model()
            user = User.objects.get(id=user_id)

            # Count actual active listings from database
            current_ads = Listing.objects.filter(
                host=user,
                is_active=True
            ).count()

            current_subscription = SubscriptionService.get_current_subscription(user)

            if not current_subscription:
                # Return free tier limits
                return {
                    'current': current_ads,
                    'limit': 2,    # Free tier limit
                    'plan_name': 'Free',
                    'subscription_status': 'none'
                }

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
    def create_subscription(user, plan, payment_reference=None, amount_paid=None, auto_renew=False):
        """Create a new subscription for a user"""
        from django.utils import timezone
        from datetime import timedelta
        from moderation.models import ModerationLog

        # End current active subscriptions
        current_subscriptions = UserSubscription.objects.filter(
            user=user,
            status='active'
        )
        for sub in current_subscriptions:
            sub.status = 'canceled'
            sub.save()

        # Create new subscription
        start_date = timezone.now()
        end_date = start_date + timedelta(days=plan.duration_days)

        subscription = UserSubscription.objects.create(
            user=user,
            plan=plan,
            status='active',
            start_date=start_date,
            end_date=end_date,
            amount_paid=amount_paid or plan.price,
            payment_reference=payment_reference,
            auto_renew=auto_renew
        )

        # Create usage tracking
        SubscriptionUsage.objects.create(subscription=subscription)

        # Log the action
        SubscriptionLog.objects.create(
            subscription=subscription,
            action='created',
            description=f'Subscription created for plan {plan.name}'
        )

        # Log in moderation system
        try:
            ModerationLog.objects.create(
                moderator=user,  # User who created subscription
                action_type='subscription_created',
                target_user=user,
                description=f'User {user.username} subscribed to {plan.name} plan',
                notes=f'Amount paid: ${amount_paid or plan.price}, Duration: {plan.duration_days} days'
            )
        except Exception:
            pass  # Don't fail subscription creation if logging fails

        return subscription

    @staticmethod
    def get_analytics_data(start_date=None, end_date=None, days=None):
        """Get comprehensive analytics data for subscriptions"""
        try:
            # Calculate date range
            if start_date and end_date:
                # Use provided dates
                pass
            elif days:
                # Calculate based on days parameter
                end_date = timezone.now().date()
                start_date = end_date - timedelta(days=int(days))
            else:
                # Default to last year
                end_date = timezone.now().date()
                start_date = end_date - timedelta(days=365)

            # Get all subscriptions and period-specific subscriptions
            all_subscriptions = UserSubscription.objects.all()
            period_subscriptions = all_subscriptions.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            )

            # Summary statistics - mix of all-time and period-specific
            summary = {
                'total_subscriptions': all_subscriptions.count(),
                'active_subscriptions': all_subscriptions.filter(status='active').count(),
                'expired_subscriptions': all_subscriptions.filter(status='expired').count(),
                'canceled_subscriptions': all_subscriptions.filter(status='canceled').count(),
                'period_subscriptions': period_subscriptions.count(),
                'total_revenue': float(all_subscriptions.aggregate(
                    total=Sum('amount_paid')
                )['total'] or 0),
                'period_revenue': float(period_subscriptions.aggregate(
                    total=Sum('amount_paid')
                )['total'] or 0),
                'average_subscription_value': float(period_subscriptions.aggregate(
                    avg=Avg('amount_paid')
                )['avg'] or 0)
            }

            # Monthly revenue data - limit to filtered period
            monthly_data = []

            # Calculate how many months to show based on period
            if (end_date - start_date).days <= 92:  # ~3 months
                months_to_show = 3
            elif (end_date - start_date).days <= 366:  # ~1 year
                months_to_show = 12
            else:
                months_to_show = 24

            current_date = end_date

            for i in range(months_to_show - 1, -1, -1):
                month_start = current_date.replace(day=1) - relativedelta(months=i)
                month_end = month_start + relativedelta(months=1)

                # Only include months within our date range
                if month_start >= start_date and month_start <= end_date:
                    month_subscriptions = all_subscriptions.filter(
                        created_at__date__gte=max(month_start, start_date),
                        created_at__date__lt=min(month_end, end_date + timedelta(days=1))
                    )

                    month_revenue = month_subscriptions.aggregate(
                        total=Sum('amount_paid')
                    )['total'] or 0

                    monthly_data.append({
                        'label': month_start.strftime('%Y-%m'),
                        'month_name': month_start.strftime('%b %Y'),
                        'revenue': float(month_revenue),
                        'subscriptions': month_subscriptions.count()
                    })

            # Plans distribution
            plans_data = period_subscriptions.values(
                'plan__name'
            ).annotate(
                count=Count('id')
            ).order_by('-count')

            plans_distribution = {}
            for item in plans_data:
                plans_distribution[item['plan__name']] = item['count']

            # Seasonal data (monthly aggregation across all years)
            seasonal_data = []
            month_names = [
                '', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
            ]

            for month_num in range(1, 13):
                month_subs = period_subscriptions.filter(created_at__month=month_num)
                month_revenue = month_subs.aggregate(total=Sum('amount_paid'))['total'] or 0
                seasonal_data.append({
                    'month': month_num,
                    'month_name': month_names[month_num],
                    'total_revenue': float(month_revenue),
                    'subscriptions': month_subs.count(),
                    'avg_revenue': float(month_revenue / max(month_subs.count(), 1))
                })

            # Recent subscriptions - from filtered period
            recent_subscriptions = period_subscriptions.select_related('user', 'plan').order_by('-created_at')[:10]
            recent_subscriptions_list = []
            for sub in recent_subscriptions:
                recent_subscriptions_list.append({
                    'user': sub.user.username,
                    'plan': sub.plan.name,
                    'status': sub.status,
                    'start_date': sub.start_date.isoformat() if sub.start_date else None,
                    'end_date': sub.end_date.isoformat() if sub.end_date else None,
                    'amount_paid': float(sub.amount_paid),
                    'auto_renew': sub.auto_renew
                })

            # Status distribution
            status_data = period_subscriptions.values('status').annotate(
                count=Count('id')
            )
            status_distribution = {}
            for item in status_data:
                status_distribution[item['status']] = item['count']

            return {
                'summary': summary,
                'monthly_revenue': monthly_data,
                'plans_distribution': plans_distribution,
                'seasonal_data': seasonal_data,
                'recent_subscriptions': recent_subscriptions_list,
                'status_distribution': status_distribution,
                'period': {
                    'start': start_date.isoformat() if hasattr(start_date, 'isoformat') else str(start_date),
                    'end': end_date.isoformat() if hasattr(end_date, 'isoformat') else str(end_date)
                }
            }
        except Exception as e:
            logger.error(f"Error getting subscription analytics data: {e}")
            return {
                'summary': {},
                'monthly_revenue': [],
                'plans_distribution': {},
                'seasonal_data': [],
                'recent_subscriptions': [],
                'status_distribution': {},
                'period': {}
            }

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
            from listings.models import Listing
            # Get actual count of active listings
            actual_count = Listing.objects.filter(
                host=user,
                is_active=True
            ).count()

            usage, created = SubscriptionUsage.objects.get_or_create(
                subscription=current_subscription
            )
            # Sync with actual count
            usage.ads_count = actual_count
            usage.total_ads_created += 1
            usage.last_ad_created = timezone.now()
            usage.save()

    @staticmethod
    def update_usage_on_ad_deleted(user):
        """Update subscription usage when ad is deleted"""
        current_subscription = SubscriptionService.get_current_subscription(user)
        if current_subscription:
            try:
                from listings.models import Listing
                # Get actual count of active listings
                actual_count = Listing.objects.filter(
                    host=user,
                    is_active=True
                ).count()

                usage = current_subscription.usage
                # Sync with actual count
                usage.ads_count = actual_count
                usage.save()
            except SubscriptionUsage.DoesNotExist:
                pass

    @staticmethod
    def get_analytics_data_old(start_date=None, end_date=None, days=None):
        """Get comprehensive analytics data for subscriptions"""

        # Calculate date range
        if days:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=int(days))
        elif start_date and end_date:
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date).date()
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date).date()
        else:
            # Default to last 2+ years for comprehensive analytics
            end_date = timezone.now().date()
            start_date = date(2023, 1, 1)

        # Base queryset
        subscriptions = UserSubscription.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        )

        # Summary statistics
        summary = SubscriptionService.get_summary_stats(subscriptions)

        # Revenue by month
        monthly_revenue = SubscriptionService.get_monthly_revenue(subscriptions, start_date, end_date)

        # Revenue by quarter
        quarterly_revenue = SubscriptionService.get_quarterly_revenue(subscriptions, start_date, end_date)

        # Seasonal data
        seasonal_data = SubscriptionService.get_seasonal_data(subscriptions, start_date, end_date)

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
    def get_monthly_revenue(subscriptions, start_date, end_date):
        """Get monthly revenue breakdown"""
        # Calculate revenue over time (monthly)
        revenue_data = []
        current_date = start_date.replace(day=1)  # Start from first day of month

        while current_date <= end_date:
            # Calculate month end properly
            if current_date.month == 12:
                next_month = current_date.replace(year=current_date.year + 1, month=1)
            else:
                next_month = current_date.replace(month=current_date.month + 1)
            month_end = next_month - timedelta(days=1)

            # Get subscriptions that were created in this month
            month_subscriptions = subscriptions.filter(
                start_date__gte=current_date,
                start_date__lte=month_end
            )

            # Calculate actual revenue from payments in this month
            month_revenue = Decimal('0')
            for subscription in month_subscriptions:
                if subscription.status in ['active', 'expired', 'canceled']:
                    month_revenue += subscription.plan.price

            revenue_data.append({
                'month': current_date.strftime('%Y-%m-%d'),
                'month_name': current_date.strftime('%b %Y'),
                'revenue': float(month_revenue),
                'subscriptions': month_subscriptions.count()
            })

            # Move to next month
            current_date = next_month

        return revenue_data

    @staticmethod
    def get_quarterly_revenue(subscriptions, start_date, end_date):
        """Get quarterly revenue breakdown"""
        # Quarterly analysis
        quarterly_data = []
        quarters = [
            (1, 'Q1'), (4, 'Q2'), (7, 'Q3'), (10, 'Q4')
        ]

        for year in range(start_date.year, end_date.year + 1):
            for quarter_start_month, quarter_name in quarters:
                quarter_start = date(year, quarter_start_month, 1)

                # Calculate quarter end properly
                if quarter_start_month == 10:  # Q4
                    quarter_end = date(year, 12, 31)
                else:
                    quarter_end_month = quarter_start_month + 2
                    # Get last day of the quarter end month
                    if quarter_end_month == 12:
                        quarter_end = date(year, 12, 31)
                    else:
                        next_month = date(year, quarter_end_month + 1, 1)
                        quarter_end = next_month - timedelta(days=1)

                if quarter_start > end_date:
                    break

                quarter_subscriptions = subscriptions.filter(
                    start_date__gte=quarter_start,
                    start_date__lte=min(quarter_end, end_date)
                )

                quarter_revenue = Decimal('0')
                for subscription in quarter_subscriptions:
                    if subscription.status in ['active', 'expired', 'canceled']:
                        quarter_revenue += subscription.plan.price

                quarterly_data.append({
                    'quarter': f'{year}-{quarter_name}',
                    'quarter_name': f'{quarter_name} {year}',
                    'revenue': float(quarter_revenue),
                    'subscriptions': quarter_subscriptions.count()
                })

        return quarterly_data

    @staticmethod
    def get_seasonal_data(subscriptions, start_date, end_date):
        """Get seasonal analysis data"""
        # Seasonal analysis (by month across all years)
        seasonal_data = []
        month_names = {
            1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
            5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
            9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
        }

        for month in range(1, 13):
            month_subscriptions = subscriptions.filter(
                start_date__month=month,
                start_date__gte=start_date,
                start_date__lte=end_date
            )

            month_revenue = Decimal('0')
            for subscription in month_subscriptions:
                if subscription.status in ['active', 'expired', 'canceled']:
                    month_revenue += subscription.plan.price

            subscription_count = month_subscriptions.count()
            avg_revenue = float(month_revenue / max(subscription_count, 1))

            seasonal_data.append({
                'month': month,
                'month_name': month_names[month],
                'total_revenue': float(month_revenue),
                'subscriptions': subscription_count,
                'avg_revenue': avg_revenue
            })
        return seasonal_data

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

    @staticmethod
    def renew_subscription(subscription):
        """Renew an existing subscription"""
        from django.utils import timezone
        from datetime import timedelta
        from moderation.models import ModerationLog

        if not subscription.auto_renew or not subscription.plan.is_active:
            return False

        # Extend subscription
        subscription.start_date = subscription.end_date
        subscription.end_date = subscription.start_date + timedelta(days=subscription.plan.duration_days)
        subscription.status = 'active'
        subscription.save()

        # Log the renewal
        SubscriptionLog.objects.create(
            subscription=subscription,
            action='renewed',
            description=f'Subscription renewed for plan {subscription.plan.name}'
        )

        # Log in moderation system
        try:
            ModerationLog.objects.create(
                moderator=subscription.user,  # User whose subscription was renewed
                action_type='subscription_renewed',
                target_user=subscription.user,
                description=f'Subscription renewed for user {subscription.user.username} - {subscription.plan.name}',
                notes=f'Auto-renewal, Duration: {subscription.plan.duration_days} days'
            )
        except Exception:
            pass

        return True

    @staticmethod
    def cancel_subscription(subscription, reason=''):
        """Cancel a subscription"""
        from moderation.models import ModerationLog

        subscription.status = 'canceled'
        subscription.auto_renew = False
        subscription.save()

        # Log the cancellation
        SubscriptionLog.objects.create(
            subscription=subscription,
            action='canceled',
            description=f'Subscription canceled: {reason}' if reason else 'Subscription canceled'
        )

        # Log in moderation system
        try:
            ModerationLog.objects.create(
                moderator=subscription.user,
                action_type='subscription_canceled',
                target_user=subscription.user,
                description=f'Subscription canceled for user {subscription.user.username} - {subscription.plan.name}',
                notes=f'Reason: {reason}' if reason else 'No reason provided'
            )
        except Exception:
            pass

        return True

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