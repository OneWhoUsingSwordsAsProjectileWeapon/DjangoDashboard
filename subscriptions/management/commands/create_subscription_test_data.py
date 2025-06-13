
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from subscriptions.models import SubscriptionPlan, UserSubscription, SubscriptionLog
from subscriptions.services import SubscriptionService
from datetime import datetime, timedelta
from decimal import Decimal
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Create extensive subscription test data for analytics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=200,
            help='Number of users to create (default: 200)'
        )
        parser.add_argument(
            '--subscriptions',
            type=int,
            default=500,
            help='Number of subscriptions to create (default: 500)'
        )

    def handle(self, *args, **options):
        self.stdout.write('Creating extensive subscription test data...')
        
        num_users = options['users']
        num_subscriptions = options['subscriptions']
        
        # Create users if needed
        existing_users = User.objects.filter(is_superuser=False).count()
        users_to_create = max(0, num_users - existing_users)
        
        created_users = []
        for i in range(users_to_create):
            try:
                user = User.objects.create_user(
                    username=f'testuser_{i + existing_users + 1}',
                    email=f'testuser{i + existing_users + 1}@example.com',
                    password='testpass123',
                    first_name=f'Test{i + existing_users + 1}',
                    last_name='User'
                )
                created_users.append(user)
            except:
                pass  # Skip if user already exists
        
        self.stdout.write(f'Created {len(created_users)} users')
        
        # Get all users and plans
        users = list(User.objects.filter(is_superuser=False)[:num_users])
        plans = list(SubscriptionPlan.objects.all())
        
        if not plans:
            self.stdout.write(self.style.ERROR('No subscription plans found. Run setup_default_plans first.'))
            return
        
        # Generate subscription data over the past year
        now = timezone.now()
        start_date = now - timedelta(days=365)
        
        created_subscriptions = 0
        created_logs = 0
        
        # Create subscriptions with realistic distribution
        for _ in range(num_subscriptions):
            user = random.choice(users)
            plan = random.choice(plans)
            
            # Random start date in the past year
            days_ago = random.randint(1, 365)
            subscription_start = now - timedelta(days=days_ago)
            subscription_end = subscription_start + timedelta(days=plan.duration_days)
            
            # Determine status based on dates
            if subscription_end < now:
                if random.random() < 0.8:  # 80% complete normally
                    status = 'expired'
                else:
                    status = 'canceled'
            elif subscription_start <= now <= subscription_end:
                status = 'active'
            else:
                status = 'pending'
            
            # Create subscription
            subscription = UserSubscription.objects.create(
                user=user,
                plan=plan,
                status=status,
                start_date=subscription_start,
                end_date=subscription_end,
                auto_renew=random.choice([True, False]),
                payment_method='test',
                payment_reference=f'test_ref_{random.randint(100000, 999999)}'
            )
            created_subscriptions += 1
            
            # Create subscription logs for each subscription
            log_events = []
            
            # Always have creation log
            log_events.append({
                'action': 'created',
                'timestamp': subscription_start,
                'details': f'Subscription created for plan {plan.name}'
            })
            
            # Add payment logs
            payment_date = subscription_start
            while payment_date < min(subscription_end, now):
                log_events.append({
                    'action': 'payment_processed',
                    'timestamp': payment_date,
                    'details': f'Payment of ${plan.price} processed successfully'
                })
                payment_date += timedelta(days=plan.duration_days)
            
            # Add random events
            if random.random() < 0.3:  # 30% chance of status changes
                if status in ['expired', 'canceled']:
                    if status == 'canceled':
                        cancel_date = subscription_start + timedelta(
                            days=random.randint(1, (subscription_end - subscription_start).days)
                        )
                        log_events.append({
                            'action': 'canceled',
                            'timestamp': cancel_date,
                            'details': 'Subscription canceled by user'
                        })
                    else:
                        log_events.append({
                            'action': 'expired',
                            'timestamp': subscription_end,
                            'details': 'Subscription expired naturally'
                        })
            
            if random.random() < 0.2:  # 20% chance of auto-renew toggle
                toggle_date = subscription_start + timedelta(
                    days=random.randint(1, (min(subscription_end, now) - subscription_start).days)
                )
                log_events.append({
                    'action': 'auto_renew_toggled',
                    'timestamp': toggle_date,
                    'details': f'Auto-renew {"enabled" if subscription.auto_renew else "disabled"}'
                })
            
            # Create logs
            for log_event in log_events:
                SubscriptionLog.objects.create(
                    subscription=subscription,
                    action=log_event['action'],
                    details=log_event['details'],
                    timestamp=log_event['timestamp']
                )
                created_logs += 1
        
        # Create some recent activity for better charts
        recent_users = random.sample(users, min(50, len(users)))
        for user in recent_users:
            plan = random.choice(plans)
            
            # Create recent subscription (last 30 days)
            days_ago = random.randint(1, 30)
            subscription_start = now - timedelta(days=days_ago)
            subscription_end = subscription_start + timedelta(days=plan.duration_days)
            
            subscription = UserSubscription.objects.create(
                user=user,
                plan=plan,
                status='active',
                start_date=subscription_start,
                end_date=subscription_end,
                auto_renew=random.choice([True, False]),
                payment_method='test',
                payment_reference=f'recent_ref_{random.randint(100000, 999999)}'
            )
            created_subscriptions += 1
            
            # Create logs
            SubscriptionLog.objects.create(
                subscription=subscription,
                action='created',
                details=f'Recent subscription created for plan {plan.name}',
                timestamp=subscription_start
            )
            
            SubscriptionLog.objects.create(
                subscription=subscription,
                action='payment_processed',
                details=f'Recent payment of ${plan.price} processed',
                timestamp=subscription_start
            )
            created_logs += 2
        
        # Create seasonal patterns for more realistic data
        seasonal_multipliers = {
            1: 0.8,   # January - low
            2: 0.9,   # February - low
            3: 1.1,   # March - increase
            4: 1.2,   # April - spring growth
            5: 1.3,   # May - peak spring
            6: 1.1,   # June - summer start
            7: 0.9,   # July - summer low
            8: 0.8,   # August - summer low
            9: 1.2,   # September - back to work
            10: 1.4,  # October - peak fall
            11: 1.3,  # November - pre-holiday
            12: 1.1   # December - holiday
        }
        
        # Create additional seasonal subscriptions
        for month, multiplier in seasonal_multipliers.items():
            additional_subs = int(20 * multiplier)  # Base 20 subscriptions per month
            
            for _ in range(additional_subs):
                user = random.choice(users)
                plan = random.choice(plans)
                
                # Create subscription in specific month over past year
                year = now.year if month <= now.month else now.year - 1
                subscription_start = datetime(year, month, random.randint(1, 28), tzinfo=timezone.get_current_timezone())
                subscription_end = subscription_start + timedelta(days=plan.duration_days)
                
                if subscription_end < now:
                    status = random.choice(['expired', 'canceled']) if random.random() < 0.3 else 'expired'
                elif subscription_start <= now <= subscription_end:
                    status = 'active'
                else:
                    continue  # Skip future dates
                
                subscription = UserSubscription.objects.create(
                    user=user,
                    plan=plan,
                    status=status,
                    start_date=subscription_start,
                    end_date=subscription_end,
                    auto_renew=random.choice([True, False]),
                    payment_method='seasonal_test',
                    payment_reference=f'seasonal_{month}_{random.randint(100000, 999999)}'
                )
                created_subscriptions += 1
                
                # Create basic logs
                SubscriptionLog.objects.create(
                    subscription=subscription,
                    action='created',
                    details=f'Seasonal subscription for {plan.name}',
                    timestamp=subscription_start
                )
                created_logs += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created subscription test data!\n'
                f'Created users: {len(created_users)}\n'
                f'Total subscriptions: {created_subscriptions}\n'
                f'Total logs: {created_logs}\n'
                f'Active subscriptions: {UserSubscription.objects.filter(status="active").count()}\n'
                f'Expired subscriptions: {UserSubscription.objects.filter(status="expired").count()}\n'
                f'Canceled subscriptions: {UserSubscription.objects.filter(status="canceled").count()}'
            )
        )
