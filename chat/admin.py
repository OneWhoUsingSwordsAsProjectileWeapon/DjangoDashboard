from django.contrib import admin
from .models import Conversation, Message

class MessageInline(admin.StackedInline):
    model = Message
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('sender', 'content', 'is_read', 'created_at')

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_participants', 'listing', 'booking', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('participants__username', 'listing__title', 'messages__content')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [MessageInline]
    
    def get_participants(self, obj):
        return ", ".join([user.username for user in obj.participants.all()])
    get_participants.short_description = "Participants"

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'get_conversation_id', 'short_content', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('content', 'sender__username', 'conversation__id')
    readonly_fields = ('created_at',)
    
    def get_conversation_id(self, obj):
        return obj.conversation.id
    get_conversation_id.short_description = "Conversation ID"
    
    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = "Content"
