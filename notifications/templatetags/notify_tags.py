from django import template
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string

register = template.Library()

@register.simple_tag(takes_context=True)
def notification_count(context):
    """Return the number of unread notifications"""
    user = context['request'].user
    if user.is_authenticated:
        count = user.notifications.filter(is_read=False).count()
        return count
    return 0

@register.simple_tag(takes_context=True)
def notification_badge(context):
    """Return a badge with the number of unread notifications"""
    count = notification_count(context)
    if count > 0:
        return mark_safe(f'<span class="badge bg-danger rounded-pill">{count}</span>')
    return ''

@register.simple_tag(takes_context=True)
def recent_notifications(context, limit=5):
    """Return recent notifications for display in dropdown"""
    user = context['request'].user
    if user.is_authenticated:
        notifications = user.notifications.all().order_by('-created_at')[:limit]
        return notifications
    return []

@register.filter
def notification_icon(notification_type):
    """Return appropriate icon for notification type"""
    icons = {
        'booking_request': 'fas fa-calendar-plus',
        'booking_confirmed': 'fas fa-calendar-check',
        'booking_canceled': 'fas fa-calendar-times',
        'message_received': 'fas fa-envelope',
        'review_received': 'fas fa-star',
        'listing_approved': 'fas fa-check-circle',
        'payment_received': 'fas fa-dollar-sign',
        'system': 'fas fa-bell',
    }

    icon_class = icons.get(notification_type, 'fas fa-bell')
    return mark_safe(f'<i class="{icon_class}"></i>')

@register.filter
def notification_target_url(notification):
    """Return URL to redirect to when notification is clicked"""
    if notification.booking:
        return f"/listings/bookings/{notification.booking.booking_reference}/"
    elif notification.conversation:
        return f"/chat/{notification.conversation.id}/"
    elif notification.listing:
        return f"/listings/{notification.listing.id}/"
    elif notification.review:
        return f"/listings/{notification.review.listing.id}/"
    return "/notifications/"