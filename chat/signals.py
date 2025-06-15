from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Message, Conversation

User = get_user_model()

# Убираем создание уведомлений для сообщений - чат имеет свою систему уведомлений
# @receiver(post_save, sender=Message)
# def create_message_notification(sender, instance, created, **kwargs):
#     """Create notification when new message is sent"""
#     pass