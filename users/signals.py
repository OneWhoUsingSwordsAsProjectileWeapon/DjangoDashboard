"""
Signal handlers for the users app.

This module contains signal handlers for user-related events,
such as set default preferences and performing other post-user creation tasks.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.conf import settings

# Get the custom user model
User = get_user_model()

@receiver(post_save, sender=User)
def user_created_handler(sender, instance, created, **kwargs):
    """
    Signal handler for actions to perform when a user is created.
    """
    if created:
        # For now, we'll just log the action (in a real app, we might add more logic here)
        print(f"User created: {instance.username}")
        
        # Example of setting default preferences or performing other initialization
        # instance.email_notifications = True
        # instance.save(update_fields=['email_notifications'])