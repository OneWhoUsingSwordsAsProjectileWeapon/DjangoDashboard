from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import UserComplaint, ModerationLog
from .models import UserComplaint
```# I will replace the original signal handlers with the new ones for logging complaint creation and status changes.
@receiver(post_save, sender=UserComplaint)
def log_complaint_creation(sender, instance, created, **kwargs):
    """Log when a new complaint is created"""
    if created:
        ModerationLog.objects.create(
            moderator=None,  # System action
            action_type='complaint_handled',
            target_user=instance.complainant,
            description=f"Новая жалоба подана пользователем {instance.complainant.username}: {instance.subject}",
            notes=f"Тип: {instance.get_complaint_type_display()}, Приоритет: {instance.get_priority_display()}"
        )

@receiver(post_save, sender=UserComplaint)
def log_complaint_status_change(sender, instance, created, **kwargs):
    """Log when complaint status changes"""
    if not created and instance.assigned_moderator:
        # Get the previous status from database
        try:
            old_instance = UserComplaint.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                ModerationLog.objects.create(
                    moderator=instance.assigned_moderator,
                    action_type='complaint_handled',
                    target_user=instance.complainant,
                    description=f"Статус жалобы #{instance.id} изменен с '{old_instance.get_status_display()}' на '{instance.get_status_display()}'",
                    notes=f"Ответ модератора: {instance.moderator_response[:100] if instance.moderator_response else 'Без ответа'}"
                )
        except UserComplaint.DoesNotExist:
            pass