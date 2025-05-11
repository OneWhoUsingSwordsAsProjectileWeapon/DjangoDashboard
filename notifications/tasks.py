"""
Async tasks for sending notifications
"""
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

# In a real project, this would use Celery or a similar task queue
# For simplicity in this project, we're implementing it as synchronous functions

def send_email_notification(recipient_email, subject, message):
    """
    Send an email notification
    In a real app with Celery, this would be a @task-decorated function
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@rentalapp.com',
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def create_notification(user, notification_type, title, message, **kwargs):
    """
    Create a notification in the database
    In a real app with Celery, this would be a @task-decorated function
    """
    from notifications.models import Notification
    
    try:
        notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            **kwargs
        )
        return notification
    except Exception as e:
        print(f"Error creating notification: {e}")
        return None

def send_booking_request_notification(booking):
    """Send notification for new booking request"""
    # Notify host
    host = booking.listing.host
    guest = booking.guest
    listing = booking.listing
    
    # Email notification
    subject = f"New booking request for {listing.title}"
    message = f"""
    Hello {host.first_name or host.username},
    
    You have received a new booking request:
    
    Listing: {listing.title}
    Guest: {guest.get_full_name() or guest.username}
    Check-in: {booking.start_date}
    Check-out: {booking.end_date}
    Guests: {booking.guests}
    Total price: ${booking.total_price}
    
    Please log in to your account to accept or decline this booking.
    
    Best regards,
    The Rental App Team
    """
    
    send_email_notification(host.email, subject, message)
    
    # In-app notification
    create_notification(
        user=host,
        notification_type='booking_request',
        title=f"New booking request for {listing.title}",
        message=f"From {guest.get_full_name() or guest.username} for {booking.start_date} to {booking.end_date}",
        booking=booking,
        listing=listing
    )

def send_booking_confirmed_notification(booking):
    """Send notification when booking is confirmed"""
    # Notify guest
    guest = booking.guest
    listing = booking.listing
    
    # Email notification
    subject = f"Your booking for {listing.title} has been confirmed"
    message = f"""
    Hello {guest.first_name or guest.username},
    
    Your booking has been confirmed:
    
    Listing: {listing.title}
    Check-in: {booking.start_date}
    Check-out: {booking.end_date}
    Guests: {booking.guests}
    Total price: ${booking.total_price}
    
    Host: {listing.host.get_full_name() or listing.host.username}
    
    Please log in to your account to view booking details and message the host.
    
    Best regards,
    The Rental App Team
    """
    
    send_email_notification(guest.email, subject, message)
    
    # In-app notification
    create_notification(
        user=guest,
        notification_type='booking_confirmed',
        title=f"Booking confirmed for {listing.title}",
        message=f"Your stay from {booking.start_date} to {booking.end_date} has been confirmed by the host.",
        booking=booking,
        listing=listing
    )

def send_booking_canceled_notification(booking, canceled_by):
    """Send notification when booking is canceled"""
    listing = booking.listing
    host = listing.host
    guest = booking.guest
    
    # Determine who to notify (the other party)
    if canceled_by == host:
        # Host canceled, notify guest
        recipient = guest
        by_text = "by the host"
    else:
        # Guest canceled, notify host
        recipient = host
        by_text = "by the guest"
    
    # Email notification
    subject = f"Booking for {listing.title} has been canceled"
    message = f"""
    Hello {recipient.first_name or recipient.username},
    
    A booking has been canceled {by_text}:
    
    Listing: {listing.title}
    Check-in: {booking.start_date}
    Check-out: {booking.end_date}
    Guests: {booking.guests}
    Total price: ${booking.total_price}
    
    Please log in to your account for more details.
    
    Best regards,
    The Rental App Team
    """
    
    send_email_notification(recipient.email, subject, message)
    
    # In-app notification
    create_notification(
        user=recipient,
        notification_type='booking_canceled',
        title=f"Booking canceled for {listing.title}",
        message=f"The booking from {booking.start_date} to {booking.end_date} has been canceled {by_text}.",
        booking=booking,
        listing=listing
    )

def send_new_message_notification(message):
    """Send notification for new message"""
    conversation = message.conversation
    sender = message.sender
    
    # Notify all other participants
    for recipient in conversation.participants.exclude(id=sender.id):
        # Don't send email for every message, just in-app notification
        # But you could uncomment this for email notifications as well
        """
        # Email notification
        context = conversation.title or "a conversation"
        subject = f"New message from {sender.get_full_name() or sender.username}"
        email_message = (
            f"Hello {recipient.first_name or recipient.username},\n\n"
            f"You have received a new message in {context}:\n\n"
            f"{message.content[:100]}{'...' if len(message.content) > 100 else ''}\n\n"
            f"Please log in to your account to view and reply to this message.\n\n"
            f"Best regards,\n"
            f"The Rental App Team"
        )
        
        send_email_notification(recipient.email, subject, email_message)
        """
        
        # In-app notification
        context = ""
        if conversation.listing:
            context = f" about {conversation.listing.title}"
        elif conversation.booking:
            context = f" regarding booking for {conversation.booking.listing.title}"
            
        create_notification(
            user=recipient,
            notification_type='message_received',
            title=f"New message from {sender.get_full_name() or sender.username}",
            message=f"You have a new message{context}.",
            conversation=conversation,
            listing=conversation.listing,
            booking=conversation.booking
        )

def send_new_review_notification(review):
    """Send notification for new review"""
    listing = review.listing
    host = listing.host
    reviewer = review.reviewer
    
    # Email notification
    subject = f"New review for {listing.title}"
    message = f"""
    Hello {host.first_name or host.username},
    
    Your listing "{listing.title}" has received a new {review.rating}-star review:
    
    "{review.comment[:100]}{"..." if len(review.comment) > 100 else ""}"
    
    - {reviewer.get_full_name() or reviewer.username}
    
    Please log in to your account to view the full review.
    
    Best regards,
    The Rental App Team
    """
    
    send_email_notification(host.email, subject, message)
    
    # In-app notification
    create_notification(
        user=host,
        notification_type='review_received',
        title=f"New {review.rating}-star review for {listing.title}",
        message=f"From {reviewer.get_full_name() or reviewer.username}: \"{review.comment[:50]}...\"",
        review=review,
        listing=listing
    )

def send_listing_approved_notification(listing):
    """Send notification when listing is approved"""
    host = listing.host
    
    # Email notification
    subject = f"Your listing '{listing.title}' has been approved"
    message = f"""
    Hello {host.first_name or host.username},
    
    Great news! Your listing "{listing.title}" has been reviewed and approved. 
    It is now visible to potential guests on our platform.
    
    You can manage your listing, including updating details and managing bookings, 
    from your host dashboard.
    
    Best regards,
    The Rental App Team
    """
    
    send_email_notification(host.email, subject, message)
    
    # In-app notification
    create_notification(
        user=host,
        notification_type='listing_approved',
        title=f"Listing '{listing.title}' approved",
        message="Your listing is now live and visible to potential guests.",
        listing=listing
    )
