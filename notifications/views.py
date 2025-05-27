from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages

from .models import Notification

@login_required
def notification_list(request):
    """View for listing user notifications"""
    # Get user's notifications, newest first
    notifications = request.user.notifications.all().order_by('-created_at')
    
    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications
    })

@login_required
def mark_notification_read(request, pk):
    """Mark a single notification as read"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.mark_as_read()
    
    # If AJAX request, return JSON response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    # Otherwise redirect to notification list
    return redirect('notifications:notification_list')

@login_required
def mark_all_read(request):
    """Mark all notifications as read"""
    request.user.notifications.filter(is_read=False).update(is_read=True)
    
    # If AJAX request, return JSON response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    messages.success(request, "All notifications marked as read.")
    return redirect('notifications:notification_list')

@login_required
def get_unread_count(request):
    """API to get unread notification count"""
    count = request.user.notifications.filter(is_read=False).count()
    if request.headers.get('HX-Request'):
        # Return HTML for HTMX
        if count > 0:
            return render(request, 'notifications/partials/notification_badge.html', {'count': count})
        else:
            return render(request, 'notifications/partials/notification_badge.html', {'count': 0})
    return JsonResponse({'count': count})

@login_required
def recent_notifications(request):
    """API to get recent notifications for dropdown"""
    notifications = request.user.notifications.all().order_by('-created_at')[:5]
    return render(request, 'notifications/partials/recent_notifications.html', {
        'notifications': notifications
    })
