from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

class Conversation(models.Model):
    """
    Conversation between users
    """
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations',
        verbose_name=_("Participants")
    )
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    # Optional reference to a listing/booking
    listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.SET_NULL,
        related_name='conversations',
        null=True,
        blank=True,
        verbose_name=_("Related Listing")
    )
    booking = models.ForeignKey(
        'listings.Booking',
        on_delete=models.SET_NULL,
        related_name='conversations',
        null=True,
        blank=True,
        verbose_name=_("Related Booking")
    )

    class Meta:
        verbose_name = _("Conversation")
        verbose_name_plural = _("Conversations")
        ordering = ['-updated_at']

    def __str__(self):
        participant_names = ", ".join(
            str(user) for user in self.participants.all()
        )
        return f"Conversation between {participant_names}"

    def get_absolute_url(self):
        return reverse('chat:conversation_detail', kwargs={'pk': self.pk})

    @property
    def last_message(self):
        """Get the last message in the conversation"""
        return self.messages.order_by('-created_at').first()

    @property
    def title(self):
        """Generate a title for the conversation"""
        if self.listing:
            return f"Chat about: {self.listing.title}"
        elif self.booking:
            return f"Booking: {self.booking.listing.title}"
        else:
            return "Chat"

    def get_other_participant(self, user=None):
        """Get the other participant in the conversation (not the current user)"""
        if user:
            return self.participants.exclude(id=user.id).first()
        return self.participants.first()

    def get_unread_count(self, user):
        """Get count of unread messages for a specific user"""
        return self.messages.filter(is_read=False).exclude(sender=user).count()

    def get_other_participant(self, user):
        """Get the other participant in the conversation (not the current user)"""
        return self.participants.exclude(id=user.id).first()

class Message(models.Model):
    """
    Message in a conversation
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_("Conversation")
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name=_("Sender")
    )
    content = models.TextField(_("Message"))
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    is_read = models.BooleanField(_("Is read"), default=False)

    class Meta:
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender.username} at {self.created_at}"

    def mark_as_read(self):
        """Mark the message as read"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])