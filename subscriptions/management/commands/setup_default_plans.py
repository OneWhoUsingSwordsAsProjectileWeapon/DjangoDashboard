from django.core.management.base import BaseCommand
from subscriptions.models import SubscriptionPlan

class Command(BaseCommand):
    help = 'Setup default subscription plans'

    def handle(self, *args, **options):
        plans = [
            {
                'name': 'Базовый',
                'slug': 'basic',
                'plan_type': 'basic',
                'description': 'Идеально для начинающих',
                'price': 9.99,
                'duration_days': 30,
                'ads_limit': 5,
                'featured_ads_limit': 0,
                'premium_features': ['basic_support', 'standard_listing'],
                'is_active': True,
                'is_popular': False,
            },
            {
                'name': 'Премиум',
                'slug': 'premium',
                'plan_type': 'premium',
                'description': 'Лучший выбор для активных пользователей',
                'price': 19.99,
                'duration_days': 30,
                'ads_limit': 20,
                'featured_ads_limit': 3,
                'premium_features': ['priority_support', 'featured_listings', 'analytics'],
                'is_active': True,
                'is_popular': True,
            },
            {
                'name': 'Бизнес',
                'slug': 'business',
                'plan_type': 'business',
                'description': 'Для серьезного бизнеса',
                'price': 49.99,
                'duration_days': 30,
                'ads_limit': 100,
                'featured_ads_limit': 10,
                'premium_features': ['priority_support', 'featured_listings', 'analytics', 'custom_branding'],
                'is_active': True,
                'is_popular': False,
            },
            {
                'name': 'Корпоративный',
                'slug': 'enterprise',
                'plan_type': 'enterprise',
                'description': 'Безлимитные возможности',
                'price': 99.99,
                'duration_days': 30,
                'ads_limit': 1000,
                'featured_ads_limit': 50,
                'premium_features': ['priority_support', 'featured_listings', 'analytics', 'custom_branding', 'api_access'],
                'is_active': True,
                'is_popular': False,
            },
        ]

        for plan_data in plans:
            plan, created = SubscriptionPlan.objects.get_or_create(
                slug=plan_data['slug'],
                defaults=plan_data
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created plan: {plan.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Plan already exists: {plan.name}')
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully setup default plans')
        )