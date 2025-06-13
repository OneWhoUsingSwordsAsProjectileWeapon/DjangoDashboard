
from django.core.management.base import BaseCommand
from subscriptions.models import SubscriptionPlan
from decimal import Decimal

class Command(BaseCommand):
    help = 'Setup default subscription plans'

    def handle(self, *args, **options):
        # Clear existing plans
        SubscriptionPlan.objects.all().delete()
        
        # Create default plans
        plans_data = [
            {
                'name': 'Базовый',
                'slug': 'basic',
                'plan_type': 'basic',
                'description': 'Идеально для начинающих',
                'price': Decimal('9.99'),
                'duration_days': 30,
                'ads_limit': 5,
                'featured_ads_limit': 1,
                'premium_features': ['basic_support', 'standard_analytics'],
                'is_popular': False
            },
            {
                'name': 'Премиум',
                'slug': 'premium',
                'plan_type': 'premium',
                'description': 'Лучший выбор для активных пользователей',
                'price': Decimal('19.99'),
                'duration_days': 30,
                'ads_limit': 15,
                'featured_ads_limit': 5,
                'premium_features': ['priority_support', 'advanced_analytics', 'featured_placement'],
                'is_popular': True
            },
            {
                'name': 'Бизнес',
                'slug': 'business',
                'plan_type': 'business',
                'description': 'Для серьезного бизнеса',
                'price': Decimal('39.99'),
                'duration_days': 30,
                'ads_limit': 50,
                'featured_ads_limit': 15,
                'premium_features': ['24_7_support', 'detailed_analytics', 'priority_placement', 'bulk_operations'],
                'is_popular': False
            },
            {
                'name': 'Корпоративный',
                'slug': 'enterprise',
                'plan_type': 'enterprise',
                'description': 'Неограниченные возможности',
                'price': Decimal('99.99'),
                'duration_days': 30,
                'ads_limit': 200,
                'featured_ads_limit': 50,
                'premium_features': ['dedicated_support', 'custom_analytics', 'api_access', 'white_label'],
                'is_popular': False
            }
        ]
        
        created_count = 0
        for plan_data in plans_data:
            plan, created = SubscriptionPlan.objects.get_or_create(
                slug=plan_data['slug'],
                defaults=plan_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created plan: {plan.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Plan already exists: {plan.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} subscription plans')
        )
