
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from subscriptions.models import SubscriptionPlan, UserSubscription, SubscriptionLog
from subscriptions.services import SubscriptionService
from datetime import datetime, timedelta
from decimal import Decimal
import random
import uuid

User = get_user_model()

class Command(BaseCommand):
    help = 'Create extended subscription history for existing users with realistic patterns'

    def add_arguments(self, parser):
        parser.add_argument(
            '--years',
            type=int,
            default=3,
            help='Number of years to generate history for (default: 3)'
        )
        parser.add_argument(
            '--min-subscriptions',
            type=int,
            default=1,
            help='Minimum subscriptions per user (default: 1)'
        )
        parser.add_argument(
            '--max-subscriptions',
            type=int,
            default=8,
            help='Maximum subscriptions per user (default: 8)'
        )

    def handle(self, *args, **options):
        self.stdout.write('Creating extended subscription history for existing users...')

        years = options['years']
        min_subs = options['min_subscriptions']
        max_subs = options['max_subscriptions']

        # Get existing users (excluding superusers)
        users = list(User.objects.filter(is_superuser=False, is_staff=False))
        plans = list(SubscriptionPlan.objects.all())

        if not users:
            self.stdout.write(self.style.ERROR('No regular users found. Create users first.'))
            return

        if not plans:
            self.stdout.write(self.style.ERROR('No subscription plans found. Run setup_default_plans first.'))
            return

        # Clear existing subscriptions for fresh start
        UserSubscription.objects.filter(user__in=users).delete()

        now = timezone.now()
        start_date = now - timedelta(days=365 * years)

        created_subscriptions = 0
        created_logs = 0

        # User behavior profiles
        user_profiles = {
            'loyal': 0.15,      # 15% - Multiple long subscriptions, rarely cancel
            'experimental': 0.25, # 25% - Try different plans, some cancellations
            'seasonal': 0.20,   # 20% - Subscribe in specific seasons
            'churner': 0.15,    # 15% - Frequently cancel and resubscribe
            'one_time': 0.25    # 25% - Few subscriptions, basic usage
        }

        # Assign profiles to users
        profile_assignments = []
        for profile, percentage in user_profiles.items():
            count = int(len(users) * percentage)
            profile_assignments.extend([profile] * count)
        
        # Fill remaining users with random profiles
        while len(profile_assignments) < len(users):
            profile_assignments.append(random.choice(list(user_profiles.keys())))
        
        random.shuffle(profile_assignments)

        for i, user in enumerate(users):
            profile = profile_assignments[i]
            user_subs = self.create_user_subscription_history(
                user, profile, plans, start_date, now, min_subs, max_subs
            )
            created_subscriptions += len(user_subs)
            
            # Create logs for each subscription
            for subscription in user_subs:
                logs = self.create_subscription_logs(subscription, now)
                created_logs += len(logs)

        # Create some special events and patterns
        self.create_holiday_patterns(users, plans, now, years)
        self.create_renewal_patterns(users, plans, now)
        self.create_upgrade_downgrade_chains(users, plans, now, years)

        # Final statistics
        final_stats = self.get_final_statistics()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created extended subscription history!\n'
                f'Total users processed: {len(users)}\n'
                f'Total subscriptions created: {created_subscriptions}\n'
                f'Total logs created: {created_logs}\n'
                f'Current active subscriptions: {final_stats["active"]}\n'
                f'Expired subscriptions: {final_stats["expired"]}\n'
                f'Canceled subscriptions: {final_stats["canceled"]}\n'
                f'Total revenue generated: ${final_stats["revenue"]:.2f}'
            )
        )

    def create_user_subscription_history(self, user, profile, plans, start_date, now, min_subs, max_subs):
        """Create subscription history based on user profile"""
        subscriptions = []
        
        if profile == 'loyal':
            # Loyal users: 3-6 subscriptions, mostly premium, long durations
            num_subs = random.randint(3, 6)
            preferred_plans = [p for p in plans if p.plan_type in ['premium', 'business']]
            if not preferred_plans:
                preferred_plans = plans
                
        elif profile == 'experimental':
            # Experimental users: 4-8 subscriptions, try all plans
            num_subs = random.randint(4, 8)
            preferred_plans = plans
            
        elif profile == 'seasonal':
            # Seasonal users: 2-4 subscriptions, specific times
            num_subs = random.randint(2, 4)
            preferred_plans = [p for p in plans if p.plan_type in ['basic', 'premium']]
            if not preferred_plans:
                preferred_plans = plans
                
        elif profile == 'churner':
            # Churners: 5-8 subscriptions, many short, canceled
            num_subs = random.randint(5, 8)
            preferred_plans = [p for p in plans if p.plan_type in ['basic', 'premium']]
            if not preferred_plans:
                preferred_plans = plans
                
        else:  # one_time
            # One-time users: 1-3 subscriptions, basic plans
            num_subs = random.randint(1, 3)
            preferred_plans = [p for p in plans if p.plan_type == 'basic']
            if not preferred_plans:
                preferred_plans = plans[:1]  # Just first plan

        # Ensure within bounds
        num_subs = max(min_subs, min(max_subs, num_subs))

        current_date = start_date
        for i in range(num_subs):
            # Time between subscriptions
            if i > 0:
                if profile == 'loyal':
                    gap_days = random.randint(0, 30)  # Small gaps
                elif profile == 'seasonal':
                    gap_days = random.randint(60, 180)  # Seasonal gaps
                elif profile == 'churner':
                    gap_days = random.randint(0, 60)  # Variable gaps
                else:
                    gap_days = random.randint(30, 120)  # Medium gaps
                    
                current_date += timedelta(days=gap_days)

            if current_date >= now:
                break

            # Select plan based on profile
            if profile == 'experimental' and i > 0:
                # Try different plans
                used_plans = [s.plan for s in subscriptions]
                available_plans = [p for p in preferred_plans if p not in used_plans]
                if not available_plans:
                    available_plans = preferred_plans
                plan = random.choice(available_plans)
            else:
                plan = random.choice(preferred_plans)

            # Determine subscription length and status
            sub_start = current_date
            base_duration = plan.duration_days
            
            if profile == 'loyal':
                # Loyal users often extend subscriptions
                duration_multiplier = random.choice([1, 1, 2, 3])  # Often multiple periods
                actual_duration = base_duration * duration_multiplier
                cancel_probability = 0.1  # Rarely cancel
            elif profile == 'churner':
                # Churners often cancel early
                duration_multiplier = random.choice([0.3, 0.5, 0.7, 1])  # Often partial
                actual_duration = int(base_duration * duration_multiplier)
                cancel_probability = 0.6  # Often cancel
            elif profile == 'seasonal':
                # Seasonal users complete most subscriptions
                duration_multiplier = 1
                actual_duration = base_duration
                cancel_probability = 0.2
            else:
                duration_multiplier = random.choice([0.7, 1, 1.2])
                actual_duration = int(base_duration * duration_multiplier)
                cancel_probability = 0.3

            sub_end = sub_start + timedelta(days=actual_duration)
            
            # Determine status
            if sub_end < now:
                if random.random() < cancel_probability:
                    status = 'canceled'
                    # If canceled, actual end might be earlier
                    if random.random() < 0.7:  # 70% cancel before natural end
                        actual_end_days = random.randint(
                            int(actual_duration * 0.1), 
                            int(actual_duration * 0.9)
                        )
                        sub_end = sub_start + timedelta(days=actual_end_days)
                else:
                    status = 'expired'
            elif sub_start <= now <= sub_end:
                status = 'active'
            else:
                status = 'pending'

            # Create subscription
            subscription = UserSubscription.objects.create(
                user=user,
                plan=plan,
                status=status,
                start_date=sub_start,
                end_date=sub_end,
                auto_renew=random.choice([True, False]) if profile != 'churner' else False,
                payment_reference=uuid.uuid4(),
                amount_paid=plan.price
            )
            subscriptions.append(subscription)
            current_date = sub_end

        return subscriptions

    def create_subscription_logs(self, subscription, now):
        """Create realistic logs for a subscription"""
        logs = []
        
        # Always create initial log
        logs.append(SubscriptionLog.objects.create(
            subscription=subscription,
            action='created',
            description=f'Subscription created for {subscription.plan.name} plan',
            timestamp=subscription.start_date
        ))

        # Payment logs
        payment_date = subscription.start_date
        while payment_date <= min(subscription.end_date, now):
            if payment_date <= subscription.end_date:
                logs.append(SubscriptionLog.objects.create(
                    subscription=subscription,
                    action='payment_processed',
                    description=f'Payment of ${subscription.plan.price} processed successfully',
                    timestamp=payment_date
                ))
            
            # Next payment date
            payment_date += timedelta(days=subscription.plan.duration_days)

        # Status change logs
        if subscription.status == 'canceled':
            cancel_date = subscription.end_date
            if subscription.end_date < subscription.start_date + timedelta(days=subscription.plan.duration_days):
                # Early cancellation
                cancel_date = subscription.end_date
            
            logs.append(SubscriptionLog.objects.create(
                subscription=subscription,
                action='canceled',
                description='Subscription canceled by user',
                timestamp=cancel_date
            ))
        elif subscription.status == 'expired' and subscription.end_date < now:
            logs.append(SubscriptionLog.objects.create(
                subscription=subscription,
                action='expired',
                description='Subscription expired naturally',
                timestamp=subscription.end_date
            ))

        # Random events
        if random.random() < 0.3:  # 30% chance of auto-renew toggle
            toggle_date = subscription.start_date + timedelta(
                days=random.randint(1, (subscription.end_date - subscription.start_date).days // 2)
            )
            if toggle_date <= now:
                logs.append(SubscriptionLog.objects.create(
                    subscription=subscription,
                    action='auto_renew_toggled',
                    description=f'Auto-renew {"enabled" if subscription.auto_renew else "disabled"}',
                    timestamp=toggle_date
                ))

        return logs

    def create_holiday_patterns(self, users, plans, now, years):
        """Create holiday subscription patterns"""
        holiday_periods = [
            (12, 'New Year promotions'),
            (3, 'Spring growth'),
            (9, 'Back-to-work surge'),
            (11, 'Black Friday deals')
        ]

        for year_offset in range(years):
            year = now.year - year_offset
            for month, description in holiday_periods:
                # Select random users for holiday promotions
                holiday_users = random.sample(users, min(20, len(users) // 4))
                
                for user in holiday_users:
                    # Check if user doesn't already have subscription in this period
                    period_start = timezone.make_aware(datetime(year, month, 1))
                    period_end = period_start + timedelta(days=30)
                    
                    existing = UserSubscription.objects.filter(
                        user=user,
                        start_date__gte=period_start,
                        start_date__lt=period_end
                    ).exists()
                    
                    if not existing and period_start < now:
                        plan = random.choice(plans)
                        
                        # Holiday subscriptions often have discounts
                        discount = random.choice([0.8, 0.9, 1.0])  # 0-20% discount
                        
                        subscription = UserSubscription.objects.create(
                            user=user,
                            plan=plan,
                            status='expired' if period_end < now else 'active',
                            start_date=period_start,
                            end_date=period_start + timedelta(days=plan.duration_days),
                            auto_renew=False,
                            payment_reference=uuid.uuid4(),
                            amount_paid=plan.price * discount
                        )
                        
                        SubscriptionLog.objects.create(
                            subscription=subscription,
                            action='created',
                            description=f'Holiday subscription: {description}',
                            timestamp=period_start
                        )

    def create_renewal_patterns(self, users, plans, now):
        """Create realistic renewal patterns"""
        # Get recently expired subscriptions that could be renewed
        recently_expired = UserSubscription.objects.filter(
            status='expired',
            end_date__gte=now - timedelta(days=90),
            end_date__lt=now - timedelta(days=7)
        )

        for expired_sub in recently_expired:
            # 30% chance of renewal within 3 months
            if random.random() < 0.3:
                renewal_delay = random.randint(7, 60)  # 1 week to 2 months delay
                renewal_start = expired_sub.end_date + timedelta(days=renewal_delay)
                
                if renewal_start < now:
                    # Sometimes users change plans when renewing
                    if random.random() < 0.3:  # 30% change plan
                        new_plan = random.choice(plans)
                    else:
                        new_plan = expired_sub.plan
                    
                    renewal_sub = UserSubscription.objects.create(
                        user=expired_sub.user,
                        plan=new_plan,
                        status='active' if renewal_start + timedelta(days=new_plan.duration_days) > now else 'expired',
                        start_date=renewal_start,
                        end_date=renewal_start + timedelta(days=new_plan.duration_days),
                        auto_renew=random.choice([True, False]),
                        payment_reference=uuid.uuid4(),
                        amount_paid=new_plan.price
                    )
                    
                    SubscriptionLog.objects.create(
                        subscription=renewal_sub,
                        action='created',
                        description=f'Renewal after {renewal_delay} days gap',
                        timestamp=renewal_start
                    )

    def create_upgrade_downgrade_chains(self, users, plans, now, years):
        """Create upgrade/downgrade chains"""
        sorted_plans = sorted(plans, key=lambda p: p.price)
        
        # Select users for upgrade/downgrade chains
        chain_users = random.sample(users, min(30, len(users) // 3))
        
        for user in chain_users:
            # Create a chain of 2-4 subscriptions with upgrades/downgrades
            chain_length = random.randint(2, 4)
            chain_start = now - timedelta(days=random.randint(200, 365 * years))
            
            current_plan_idx = random.randint(0, len(sorted_plans) - 1)
            current_date = chain_start
            
            for i in range(chain_length):
                if current_date >= now:
                    break
                    
                current_plan = sorted_plans[current_plan_idx]
                duration = current_plan.duration_days
                
                # Determine next plan for upgrade/downgrade
                if i < chain_length - 1:  # Not the last subscription
                    if current_plan_idx == 0:  # Lowest plan - likely to upgrade
                        next_plan_idx = min(current_plan_idx + random.randint(1, 2), len(sorted_plans) - 1)
                        action_type = 'upgrade'
                    elif current_plan_idx == len(sorted_plans) - 1:  # Highest plan - might downgrade
                        next_plan_idx = max(current_plan_idx - random.randint(1, 2), 0)
                        action_type = 'downgrade'
                    else:  # Middle plan - could go either way
                        direction = random.choice([-1, 1])
                        next_plan_idx = max(0, min(len(sorted_plans) - 1, current_plan_idx + direction))
                        action_type = 'upgrade' if direction > 0 else 'downgrade'
                else:
                    next_plan_idx = current_plan_idx
                    action_type = 'continuation'

                # Create subscription
                sub_end = current_date + timedelta(days=duration)
                status = 'expired' if sub_end < now else ('active' if current_date <= now else 'pending')
                
                subscription = UserSubscription.objects.create(
                    user=user,
                    plan=current_plan,
                    status=status,
                    start_date=current_date,
                    end_date=sub_end,
                    auto_renew=random.choice([True, False]),
                    payment_reference=uuid.uuid4(),
                    amount_paid=current_plan.price
                )
                
                # Create logs
                SubscriptionLog.objects.create(
                    subscription=subscription,
                    action='created',
                    description=f'Chain subscription #{i+1} - {action_type}',
                    timestamp=current_date
                )
                
                # Move to next in chain
                current_plan_idx = next_plan_idx
                current_date = sub_end + timedelta(days=random.randint(0, 7))  # Small gap

    def get_final_statistics(self):
        """Get final statistics"""
        active = UserSubscription.objects.filter(status='active').count()
        expired = UserSubscription.objects.filter(status='expired').count()
        canceled = UserSubscription.objects.filter(status='canceled').count()
        
        revenue = UserSubscription.objects.aggregate(
            total=sum([s.amount_paid for s in UserSubscription.objects.all()])
        )
        
        return {
            'active': active,
            'expired': expired,
            'canceled': canceled,
            'revenue': revenue['total'] if revenue['total'] else 0
        }
