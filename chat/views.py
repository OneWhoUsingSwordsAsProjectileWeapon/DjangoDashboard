from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.db.models import Q
from django.contrib import messages

from .models import Conversation, Message
from users.models import User
from listings.models import Listing, Booking

@login_required
def conversation_list(request):
    """View for listing all conversations for the current user"""
    # Get all conversations where the user is a participant
    conversations = Conversation.objects.filter(
        participants=request.user
    ).select_related('listing', 'booking').prefetch_related('participants')
    
    return render(request, 'chat/conversation_list.html', {
        'conversations': conversations
    })

@login_required
def conversation_detail(request, pk):
    """View for displaying a conversation"""
    conversation = get_object_or_404(Conversation, pk=pk)
    
    # Check if user is a participant
    if request.user not in conversation.participants.all():
        raise Http404("Conversation not found")
    
    # Get messages in conversation
    messages_list = conversation.messages.select_related('sender').order_by('created_at')
    
    # Mark unread messages as read
    unread_messages = messages_list.filter(is_read=False).exclude(sender=request.user)
    for msg in unread_messages:
        msg.is_read = True
        msg.save(update_fields=['is_read'])
    
    # Get other participant(s)
    other_participants = conversation.participants.exclude(id=request.user.id)
    
    return render(request, 'chat/chat_room.html', {
        'conversation': conversation,
        'messages': messages_list,
        'other_participants': other_participants
    })

@login_required
def start_conversation(request, user_id=None, listing_id=None, booking_id=None):
    """Start a new conversation or redirect to existing one"""
    # Determine who to chat with
    other_user = None
    listing = None
    booking = None
    
    # If user_id is provided, get the user
    if user_id:
        other_user = get_object_or_404(User, id=user_id)
        
        # Users can't chat with themselves
        if other_user == request.user:
            messages.error(request, "You can't start a conversation with yourself.")
            return redirect('chat:conversation_list')
    
    # If listing_id is provided, get the listing and set other_user to host
    if listing_id:
        listing = get_object_or_404(Listing, id=listing_id)
        other_user = listing.host
        
        # Users can't chat with themselves
        if other_user == request.user:
            messages.error(request, "You can't start a conversation about your own listing.")
            return redirect('listings:listing_detail', pk=listing.pk)
    
    # If booking_id is provided, get the booking
    if booking_id:
        booking = get_object_or_404(Booking, id=booking_id)
        
        # Determine the other user based on who's viewing
        if request.user == booking.guest:
            other_user = booking.listing.host
        elif request.user == booking.listing.host:
            other_user = booking.guest
        else:
            raise Http404("Booking not found")
        
        # Set the listing for reference
        listing = booking.listing
    
    # If we don't have another user by now, we can't start a conversation
    if not other_user:
        messages.error(request, "Couldn't determine who to start a conversation with.")
        return redirect('listings:listing_list')
    
    # Check if a conversation already exists with these parameters
    existing_conversation = None
    
    # First check if there's a specific conversation for this booking
    if booking:
        try:
            existing_conversation = Conversation.objects.filter(
                booking=booking,
                participants=request.user
            ).distinct().get()
        except (Conversation.DoesNotExist, Conversation.MultipleObjectsReturned):
            pass
    
    # Then check if there's a conversation about this listing
    if not existing_conversation and listing:
        try:
            existing_conversation = Conversation.objects.filter(
                listing=listing,
                participants=request.user
            ).filter(
                participants=other_user,
                booking__isnull=True
            ).distinct().get()
        except (Conversation.DoesNotExist, Conversation.MultipleObjectsReturned):
            pass
    
    # Finally check if there's any conversation with this user
    if not existing_conversation:
        try:
            existing_conversation = Conversation.objects.filter(
                participants=request.user
            ).filter(
                participants=other_user,
                listing__isnull=True,
                booking__isnull=True
            ).distinct().get()
        except (Conversation.DoesNotExist, Conversation.MultipleObjectsReturned):
            pass
    
    # If a conversation exists, redirect to it
    if existing_conversation:
        return redirect('chat:conversation_detail', pk=existing_conversation.pk)
    
    # Create a new conversation
    conversation = Conversation.objects.create(
        listing=listing,
        booking=booking
    )
    conversation.participants.add(request.user, other_user)
    
    # If this was started in the context of a booking or listing, add initial message
    if request.method == 'POST' and 'initial_message' in request.POST:
        initial_message = request.POST.get('initial_message').strip()
        if initial_message:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=initial_message
            )
    
    return redirect('chat:conversation_detail', pk=conversation.pk)

@login_required
def get_unread_count(request):
    """API to get unread message count for current user"""
    count = Message.objects.filter(
        conversation__participants=request.user,
        sender__id__ne=request.user.id,
        is_read=False
    ).count()
    
    return JsonResponse({'unread_count': count})
