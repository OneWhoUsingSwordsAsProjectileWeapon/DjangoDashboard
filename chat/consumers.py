import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Conversation, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.conversation_group_name = f"chat_{self.conversation_id}"
        
        # Check user permissions
        if not await self.user_can_access_conversation():
            await self.close()
            return
        
        # Join conversation group
        await self.channel_layer.group_add(
            self.conversation_group_name,
            self.channel_name
        )
        
        # Accept the connection
        await self.accept()
        
        # Mark messages as read
        await self.mark_messages_as_read()
    
    async def disconnect(self, close_code):
        # Leave conversation group
        await self.channel_layer.group_discard(
            self.conversation_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        # Parse the received message
        text_data_json = json.loads(text_data)
        message_content = text_data_json.get("message", "").strip()
        
        if not message_content:
            return
        
        # Create message in database
        message = await self.create_message(message_content)
        
        # Send message to conversation group
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                "type": "chat_message",
                "message": message_content,
                "sender_id": self.user.id,
                "sender_username": self.user.username,
                "timestamp": message["timestamp"],
                "message_id": message["id"]
            }
        )
    
    async def chat_message(self, event):
        """
        Send message to WebSocket when a message is sent to the group
        """
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "sender_id": event["sender_id"],
            "sender_username": event["sender_username"],
            "timestamp": event["timestamp"],
            "message_id": event["message_id"]
        }))
    
    @database_sync_to_async
    def user_can_access_conversation(self):
        """Check if user has permission to access this conversation"""
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return self.user in conversation.participants.all()
        except Conversation.DoesNotExist:
            return False
    
    @database_sync_to_async
    def create_message(self, content):
        """Create a new message in the database"""
        conversation = Conversation.objects.get(id=self.conversation_id)
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            content=content
        )
        
        # Update the conversation's updated_at field
        conversation.updated_at = timezone.now()
        conversation.save(update_fields=['updated_at'])
        
        return {
            "id": message.id,
            "timestamp": message.created_at.isoformat()
        }
    
    @database_sync_to_async
    def mark_messages_as_read(self):
        """Mark all unread messages in this conversation as read for current user"""
        conversation = Conversation.objects.get(id=self.conversation_id)
        Message.objects.filter(
            conversation=conversation,
            sender__id__ne=self.user.id,
            is_read=False
        ).update(is_read=True)
