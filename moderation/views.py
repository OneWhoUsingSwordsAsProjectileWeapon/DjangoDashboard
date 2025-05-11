from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
import re

from .models import Report, ReportCategory, BannedUser, ForbiddenKeyword
from listings.models import Listing, Review
from chat.models import Message
from users.models import User

def is_moderator(user):
    """Check if user is a moderator"""
    return user.is_staff or user.is_superuser

@login_required
def report_content(request, content_type, content_id):
    """View for reporting inappropriate content"""
    if content_type not in ['listing', 'review', 'user', 'message']:
        messages.error(request, "Invalid content type for reporting.")
        return redirect('listings:listing_list')
    
    # Get the reported content
    content_object = None
    if content_type == 'listing':
        content_object = get_object_or_404(Listing, id=content_id)
    elif content_type == 'review':
        content_object = get_object_or_404(Review, id=content_id)
    elif content_type == 'user':
        content_object = get_object_or_404(User, id=content_id)
    elif content_type == 'message':
        content_object = get_object_or_404(Message, id=content_id)
    
    # Get report categories
    categories = ReportCategory.objects.filter(is_active=True)
    
    if request.method == 'POST':
        description = request.POST.get('description', '').strip()
        category_id = request.POST.get('category')
        
        if not description:
            messages.error(request, "Please provide a description of the issue.")
            return render(request, 'moderation/report_form.html', {
                'content_type': content_type,
                'content_object': content_object,
                'categories': categories,
            })
        
        # Create the report
        report = Report(
            reporter=request.user,
            content_type=content_type,
            description=description
        )
        
        # Set the related object based on content type
        if content_type == 'listing':
            report.listing = content_object
        elif content_type == 'review':
            report.review = content_object
        elif content_type == 'user':
            report.reported_user = content_object
        elif content_type == 'message':
            report.message = content_object
        
        # Set category if provided
        if category_id:
            try:
                report.category = ReportCategory.objects.get(id=int(category_id))
            except (ReportCategory.DoesNotExist, ValueError):
                pass
        
        report.save()
        
        messages.success(request, "Thank you for your report. Our moderation team will review it shortly.")
        
        # Redirect back to appropriate page
        if content_type == 'listing':
            return redirect('listings:listing_detail', pk=content_object.id)
        elif content_type == 'review':
            return redirect('listings:listing_detail', pk=content_object.listing.id)
        elif content_type == 'user':
            return redirect('listings:listing_list')
        elif content_type == 'message':
            return redirect('chat:conversation_detail', pk=content_object.conversation.id)
    
    return render(request, 'moderation/report_form.html', {
        'content_type': content_type,
        'content_object': content_object,
        'categories': categories,
    })

@login_required
@user_passes_test(is_moderator)
def report_list(request):
    """View for listing all reports (moderators only)"""
    # Get all reports, filter by status if provided
    status = request.GET.get('status')
    reports = Report.objects.all()
    
    if status and status in [choice[0] for choice in Report.STATUS_CHOICES]:
        reports = reports.filter(status=status)
    
    # Filter by content type if provided
    content_type = request.GET.get('content_type')
    if content_type and content_type in [choice[0] for choice in Report.CONTENT_TYPES]:
        reports = reports.filter(content_type=content_type)
    
    return render(request, 'moderation/report_list.html', {
        'reports': reports,
        'status_choices': Report.STATUS_CHOICES,
        'content_type_choices': Report.CONTENT_TYPES,
        'current_status': status,
        'current_content_type': content_type
    })

@login_required
@user_passes_test(is_moderator)
def report_detail(request, pk):
    """View for viewing and processing a report (moderators only)"""
    report = get_object_or_404(Report, pk=pk)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        notes = request.POST.get('moderator_notes', '').strip()
        action = request.POST.get('action_taken', '').strip()
        
        # Update report
        if status and status in [choice[0] for choice in Report.STATUS_CHOICES]:
            report.status = status
            report.moderator = request.user
            report.moderator_notes = notes
            report.action_taken = action
            
            # Set resolved_at if status is resolved or rejected
            if status in ['resolved', 'rejected']:
                report.resolved_at = timezone.now()
            else:
                report.resolved_at = None
                
            report.save()
            
            messages.success(request, f"Report #{report.id} has been updated.")
        
        # Handle any additional actions (ban user, remove content, etc.)
        action_type = request.POST.get('action_type')
        
        if action_type == 'ban_user':
            ban_days = request.POST.get('ban_days')
            ban_reason = request.POST.get('ban_reason', '').strip()
            is_permanent = request.POST.get('is_permanent') == 'on'
            
            # Determine which user to ban
            user_to_ban = None
            if report.content_type == 'user':
                user_to_ban = report.reported_user
            elif report.content_type == 'review':
                user_to_ban = report.review.reviewer
            elif report.content_type == 'listing':
                user_to_ban = report.listing.host
            elif report.content_type == 'message':
                user_to_ban = report.message.sender
            
            if user_to_ban:
                # Calculate ban duration
                banned_until = None
                if not is_permanent and ban_days:
                    try:
                        days = int(ban_days)
                        banned_until = timezone.now() + timezone.timedelta(days=days)
                    except ValueError:
                        pass
                
                # Create or update ban record
                ban, created = BannedUser.objects.update_or_create(
                    user=user_to_ban,
                    defaults={
                        'reason': ban_reason,
                        'banned_until': banned_until,
                        'is_permanent': is_permanent,
                        'banned_by': request.user,
                        'notes': f"Ban issued from report #{report.id}"
                    }
                )
                
                # Log the action
                if not report.action_taken:
                    report.action_taken = ""
                report.action_taken += f"\nBanned user {user_to_ban.username} "
                report.action_taken += "permanently" if is_permanent else f"for {ban_days} days"
                report.save(update_fields=['action_taken'])
                
                messages.success(request, f"User {user_to_ban.username} has been banned.")
        
        elif action_type == 'remove_content':
            # Remove the reported content
            if report.content_type == 'review' and report.review:
                review = report.review
                listing_id = review.listing.id
                review.delete()
                messages.success(request, "The review has been removed.")
                
                # Log the action
                if not report.action_taken:
                    report.action_taken = ""
                report.action_taken += "\nRemoved the reported review"
                report.save(update_fields=['action_taken'])
                
                return redirect('listings:listing_detail', pk=listing_id)
            
            elif report.content_type == 'message' and report.message:
                message = report.message
                conversation_id = message.conversation.id
                message.content = "[This message has been removed by a moderator]"
                message.save(update_fields=['content'])
                
                messages.success(request, "The message has been moderated.")
                
                # Log the action
                if not report.action_taken:
                    report.action_taken = ""
                report.action_taken += "\nModerated the reported message"
                report.save(update_fields=['action_taken'])
                
                return redirect('chat:conversation_detail', pk=conversation_id)
            
            elif report.content_type == 'listing' and report.listing:
                listing = report.listing
                listing.is_active = False
                listing.is_approved = False
                listing.save(update_fields=['is_active', 'is_approved'])
                
                messages.success(request, "The listing has been deactivated.")
                
                # Log the action
                if not report.action_taken:
                    report.action_taken = ""
                report.action_taken += "\nDeactivated the reported listing"
                report.save(update_fields=['action_taken'])
    
    return render(request, 'moderation/report_detail.html', {
        'report': report,
        'status_choices': Report.STATUS_CHOICES
    })

@login_required
@user_passes_test(is_moderator)
def moderation_dashboard(request):
    """Dashboard for moderators with overview of reports and banned users"""
    # Get report statistics
    total_reports = Report.objects.count()
    pending_reports = Report.objects.filter(status='pending').count()
    in_progress_reports = Report.objects.filter(status='in_progress').count()
    resolved_reports = Report.objects.filter(status='resolved').count()
    rejected_reports = Report.objects.filter(status='rejected').count()
    
    # Recent reports
    recent_reports = Report.objects.all().order_by('-created_at')[:10]
    
    # Banned users
    active_bans = BannedUser.objects.filter(
        is_permanent=True
    ).count() + BannedUser.objects.filter(
        is_permanent=False,
        banned_until__gt=timezone.now()
    ).count()
    
    recent_bans = BannedUser.objects.all().order_by('-created_at')[:5]
    
    # Forbidden keywords
    keywords_count = ForbiddenKeyword.objects.filter(is_active=True).count()
    
    return render(request, 'moderation/dashboard.html', {
        'total_reports': total_reports,
        'pending_reports': pending_reports,
        'in_progress_reports': in_progress_reports,
        'resolved_reports': resolved_reports,
        'rejected_reports': rejected_reports,
        'recent_reports': recent_reports,
        'active_bans': active_bans,
        'recent_bans': recent_bans,
        'keywords_count': keywords_count
    })

def filter_content(request):
    """API endpoint to filter content for forbidden keywords"""
    if request.method == 'POST':
        content = request.POST.get('content', '')
        
        # Get all active forbidden keywords
        keywords = ForbiddenKeyword.objects.filter(is_active=True)
        
        # Apply filtering
        filtered_content = content
        for keyword in keywords:
            if keyword.is_regex:
                try:
                    pattern = re.compile(keyword.keyword, re.IGNORECASE)
                    replacement = keyword.replacement or '***'
                    filtered_content = pattern.sub(replacement, filtered_content)
                except re.error:
                    # Skip invalid regex patterns
                    continue
            else:
                replacement = keyword.replacement or '*' * len(keyword.keyword)
                filtered_content = re.sub(
                    r'\b' + re.escape(keyword.keyword) + r'\b', 
                    replacement, 
                    filtered_content, 
                    flags=re.IGNORECASE
                )
        
        return JsonResponse({
            'filtered_content': filtered_content,
            'is_modified': filtered_content != content
        })
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
