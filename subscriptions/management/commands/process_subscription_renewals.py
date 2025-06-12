
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from subscriptions.models import UserSubscription
from subscriptions.services import NotificationService
from subscriptions.models import SubscriptionLog
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Process subscription renewals and notifications'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making changes',
        )
        parser.add_argument(
            '--notify-only',
            action='store_true',
            help='Only send notifications, do not process renewals',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        notify_only = options['notify_only']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Running in DRY-RUN mode - no changes will be made'))
        
        # Send expiration notifications
        self.stdout.write('Processing expiration notifications...')
        self.send_expiration_notifications(dry_run)
        
        if not notify_only:
            # Process auto-renewals
            self.stdout.write('Processing auto-renewals...')
            self.process_auto_renewals(dry_run)
            
            # Mark expired subscriptions
            self.stdout.write('Marking expired subscriptions...')
            self.mark_expired_subscriptions(dry_run)
        
        self.stdout.write(self.style.SUCCESS('Subscription processing completed'))
    
    def send_expiration_notifications(self, dry_run=False):
        """Send notifications for expiring subscriptions"""
        try:
            if not dry_run:
                NotificationService.notify_expiring_subscriptions()
            
            # Count subscriptions that would be notified
            from datetime import timedelta
            expiring_count = UserSubscription.objects.filter(
                status='active',
                end_date__lte=timezone.now() + timedelta(days=3),
                end_date__gte=timezone.now()
            ).count()
            
            self.stdout.write(f'Processed {expiring_count} expiration notifications')
            
        except Exception as e:
            logger.error(f"Error sending expiration notifications: {e}")
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
    
    def process_auto_renewals(self, dry_run=False):
        """Process automatic subscription renewals"""
        now = timezone.now()
        expired_auto_renew = UserSubscription.objects.filter(
            status='active',
            auto_renew=True,
            end_date__lte=now
        )
        
        renewed_count = 0
        failed_count = 0
        
        for subscription in expired_auto_renew:
            try:
                if not dry_run:
                    with transaction.atomic():
                        success = subscription.renew()
                        
                        if success:
                            NotificationService.send_renewal_success(subscription)
                            SubscriptionLog.objects.create(
                                subscription=subscription,
                                action='renewed',
                                description='Auto-renewal processed successfully',
                                metadata={'renewal_date': now.isoformat()}
                            )
                            renewed_count += 1
                        else:
                            NotificationService.send_renewal_failed(
                                subscription, 
                                "Plan no longer available or auto-renewal disabled"
                            )
                            failed_count += 1
                else:
                    # Dry run - just count
                    if subscription.plan.is_active:
                        renewed_count += 1
                    else:
                        failed_count += 1
                        
            except Exception as e:
                logger.error(f"Error renewing subscription {subscription.id}: {e}")
                if not dry_run:
                    NotificationService.send_renewal_failed(subscription, str(e))
                failed_count += 1
        
        self.stdout.write(f'Auto-renewals: {renewed_count} successful, {failed_count} failed')
    
    def mark_expired_subscriptions(self, dry_run=False):
        """Mark subscriptions as expired"""
        now = timezone.now()
        expired_subscriptions = UserSubscription.objects.filter(
            status='active',
            end_date__lt=now,
            auto_renew=False
        )
        
        count = expired_subscriptions.count()
        
        if not dry_run and count > 0:
            expired_subscriptions.update(status='expired')
            
            # Log the expiration
            for subscription in expired_subscriptions:
                SubscriptionLog.objects.create(
                    subscription=subscription,
                    action='expired',
                    description='Subscription expired automatically',
                    metadata={'expiration_date': now.isoformat()}
                )
        
        self.stdout.write(f'Marked {count} subscriptions as expired')
