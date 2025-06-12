
from django.core.management.base import BaseCommand
from subscriptions.models import SubscriptionPlan, DefaultSubscriptionSettings
from decimal import Decimal

class Command(BaseCommand):
    help = 'Setup default subscription plans and settings'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset existing plans and settings',
        )
    
    def handle(self, *args, **options):
        reset = options['reset']
        
        if reset:
            self.stdout.write('Resetting existing plans...')
            SubscriptionPlan.objects.all().delete()
            DefaultSubscriptionSettings.objects.all().delete()
        
        # Create default subscription plans
        self.create_default_plans()
        
        # Create default settings
        self.create_default_settings()
        
        self.stdout.write(self.style.SUCCESS('Default subscription plans and settings created'))
    
    def create_default_plans(self):
        """Create default subscription plans"""
        plans = [
            {
                'name': 'Basic',
                'slug': 'basic',
                'plan_type': 'basic',
                'description': 'Perfect for individuals getting started',
                'price': Decimal('9.99'),
                'duration_days': 30,
                'ads_limit': 5,
                'featured_ads_limit': 1,
                'premium_features': ['basic_support', 'standard_analytics'],
                'is_active': True,
                'is_popular': False
            },
            {
                'name': 'Premium',
                'slug': 'premium',
                'plan_type': 'premium',
                'description': 'Most popular plan for growing businesses',
                'price': Decimal('19.99'),
                'duration_days': 30,
                'ads_limit': 15,
                'featured_ads_limit': 5,
                'premium_features': ['priority_support', 'advanced_analytics', 'custom_branding'],
                'is_active': True,
                'is_popular': True
            },
            {
                'name': 'Business',
                'slug': 'business',
                'plan_type': 'business',
                'description': 'For established businesses with high volume',
                'price': Decimal('39.99'),
                'duration_days': 30,
                'ads_limit': 50,
                'featured_ads_limit': 15,
                'premium_features': [
                    'dedicated_support', 'premium_analytics', 'custom_branding',
                    'api_access', 'bulk_operations'
                ],
                'is_active': True,
                'is_popular': False
            },
            {
                'name': 'Enterprise',
                'slug': 'enterprise',
                'plan_type': 'enterprise',
                'description': 'Custom solution for large organizations',
                'price': Decimal('99.99'),
                'duration_days': 30,
                'ads_limit': 200,
                'featured_ads_limit': 50,
                'premium_features': [
                    'dedicated_manager', 'enterprise_analytics', 'white_label',
                    'api_access', 'bulk_operations', 'custom_integrations'
                ],
                'is_active': True,
                'is_popular': False
            }
        ]
        
        for plan_data in plans:
            plan, created = SubscriptionPlan.objects.get_or_create(
                slug=plan_data['slug'],
                defaults=plan_data
            )
            
            if created:
                self.stdout.write(f'Created plan: {plan.name}')
            else:
                self.stdout.write(f'Plan already exists: {plan.name}')
    
    def create_default_settings(self):
        """Create default subscription settings"""
        settings = [
            {
                'name': 'free_ads_limit',
                'value': '2',
                'description': 'Number of ads free users can create'
            },
            {
                'name': 'grace_period_days',
                'value': '3',
                'description': 'Grace period days after subscription expires'
            },
            {
                'name': 'notification_days_before_expiry',
                'value': '3',
                'description': 'Days before expiry to send notification'
            },
            {
                'name': 'auto_renew_enabled',
                'value': 'true',
                'description': 'Whether auto-renewal is enabled by default'
            },
            {
                'name': 'payment_processing_enabled',
                'value': 'false',
                'description': 'Whether payment processing is enabled'
            }
        ]
        
        for setting_data in settings:
            setting, created = DefaultSubscriptionSettings.objects.get_or_create(
                name=setting_data['name'],
                defaults=setting_data
            )
            
            if created:
                self.stdout.write(f'Created setting: {setting.name}')
            else:
                self.stdout.write(f'Setting already exists: {setting.name}')
