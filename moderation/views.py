from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
import re

from .models import Report, ReportCategory, BannedUser, ForbiddenKeyword, UserComplaint, ModerationLog
from .forms import UserComplaintForm, ComplaintResponseForm, BookingComplaintForm, ListingComplaintForm
from listings.models import Listing, Review, Booking
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
    from .models import ListingApproval, ModerationLog

    # Get report statistics
    total_reports = Report.objects.count()
    pending_reports = Report.objects.filter(status='pending').count()
    in_progress_reports = Report.objects.filter(status='in_progress').count()
    resolved_reports = Report.objects.filter(status='resolved').count()
    rejected_reports = Report.objects.filter(status='rejected').count()

    # Recent reports
    recent_reports = Report.objects.all().order_by('-created_at')[:10]

    # Get user complaints statistics
    total_complaints = UserComplaint.objects.count()
    pending_complaints = UserComplaint.objects.filter(status='pending').count()
    in_progress_complaints = UserComplaint.objects.filter(status='in_progress').count()
    resolved_complaints = UserComplaint.objects.filter(status='resolved').count()
    escalated_complaints = UserComplaint.objects.filter(status='escalated').count()

    # Recent complaints
    recent_complaints = UserComplaint.objects.all().order_by('-created_at')[:10]

    # Listing approval statistics
    pending_listings = ListingApproval.objects.filter(status='pending').count()
    approved_listings = ListingApproval.objects.filter(status='approved').count()
    rejected_listings = ListingApproval.objects.filter(status='rejected').count()
    changes_required_listings = ListingApproval.objects.filter(status='requires_changes').count()

    # Recent listing approvals
    recent_approvals = ListingApproval.objects.all().order_by('-created_at')[:5]

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

    # Recent moderation logs
    recent_logs = ModerationLog.objects.all().order_by('-created_at')[:10]

    return render(request, 'moderation/dashboard.html', {
        'total_reports': total_reports,
        'pending_reports': pending_reports,
        'in_progress_reports': in_progress_reports,
        'resolved_reports': resolved_reports,
        'rejected_reports': rejected_reports,
        'recent_reports': recent_reports,
        'total_complaints': total_complaints,
        'pending_complaints': pending_complaints,
        'in_progress_complaints': in_progress_complaints,
        'resolved_complaints': resolved_complaints,
        'escalated_complaints': escalated_complaints,
        'recent_complaints': recent_complaints,
        'pending_listings': pending_listings,
        'approved_listings': approved_listings,
        'rejected_listings': rejected_listings,
        'changes_required_listings': changes_required_listings,
        'recent_approvals': recent_approvals,
        'active_bans': active_bans,
        'recent_bans': recent_bans,
        'keywords_count': keywords_count,
        'recent_logs': recent_logs
    })

@login_required
@user_passes_test(is_moderator)
def listing_approval_list(request):
    """View for listing all pending listing approvals"""
    from .models import ListingApproval

    # Handle bulk actions
    if request.method == 'POST':
        action = request.POST.get('bulk_action')
        selected_ids = request.POST.getlist('selected_approvals')
        
        if action and selected_ids:
            selected_approvals = ListingApproval.objects.filter(id__in=selected_ids)
            
            if action == 'bulk_approve':
                count = 0
                for approval in selected_approvals.filter(status='pending'):
                    approval.status = 'approved'
                    approval.moderator = request.user
                    approval.reviewed_at = timezone.now()
                    approval.listing.is_approved = True
                    approval.listing.is_active = True
                    approval.listing.save(update_fields=['is_approved', 'is_active'])
                    approval.save()
                    
                    # Log the action
                    ModerationLog.objects.create(
                        moderator=request.user,
                        action_type='listing_approved',
                        target_listing=approval.listing,
                        target_user=approval.listing.host,
                        description=f"Bulk approved listing: {approval.listing.title}",
                        notes="Bulk approval action"
                    )
                    count += 1
                
                messages.success(request, f"Одобрено {count} объявлений.")
                
            elif action == 'bulk_reject':
                rejection_reason = request.POST.get('bulk_rejection_reason', 'Отклонено при массовой модерации')
                count = 0
                for approval in selected_approvals.filter(status='pending'):
                    approval.status = 'rejected'
                    approval.moderator = request.user
                    approval.reviewed_at = timezone.now()
                    approval.rejection_reason = rejection_reason
                    approval.listing.is_approved = False
                    approval.listing.is_active = False
                    approval.listing.save(update_fields=['is_approved', 'is_active'])
                    approval.save()
                    
                    # Log the action
                    ModerationLog.objects.create(
                        moderator=request.user,
                        action_type='listing_rejected',
                        target_listing=approval.listing,
                        target_user=approval.listing.host,
                        description=f"Bulk rejected listing: {approval.listing.title}",
                        notes=f"Bulk rejection: {rejection_reason}"
                    )
                    count += 1
                
                messages.success(request, f"Отклонено {count} объявлений.")
                
            elif action == 'bulk_require_changes':
                required_changes = request.POST.get('bulk_required_changes', 'Требуются изменения')
                count = 0
                for approval in selected_approvals.filter(status='pending'):
                    approval.status = 'requires_changes'
                    approval.moderator = request.user
                    approval.reviewed_at = timezone.now()
                    approval.required_changes = required_changes
                    approval.listing.is_approved = False
                    approval.listing.save(update_fields=['is_approved'])
                    approval.save()
                    count += 1
                
                messages.success(request, f"Для {count} объявлений установлено 'Требуют изменений'.")
                
            elif action == 'bulk_assign':
                moderator_id = request.POST.get('bulk_assign_moderator')
                if moderator_id:
                    try:
                        moderator = User.objects.get(id=int(moderator_id), is_staff=True)
                        count = selected_approvals.filter(status='pending').update(moderator=moderator)
                        messages.success(request, f"{count} объявлений назначено модератору {moderator.username}.")
                    except (User.DoesNotExist, ValueError):
                        messages.error(request, "Неверный модератор.")
        
        return redirect('moderation:listing_approval_list')

    # Get all listing approvals, filter by status if provided
    status = request.GET.get('status')
    approvals = ListingApproval.objects.select_related('listing', 'moderator').all()

    if status and status in [choice[0] for choice in ListingApproval.STATUS_CHOICES]:
        approvals = approvals.filter(status=status)

    # Filter by moderator if provided
    moderator_id = request.GET.get('moderator')
    if moderator_id:
        try:
            approvals = approvals.filter(moderator_id=int(moderator_id))
        except ValueError:
            pass

    # Get moderators for bulk assignment
    moderators = User.objects.filter(is_staff=True)

    return render(request, 'moderation/listing_approval_list.html', {
        'approvals': approvals,
        'status_choices': ListingApproval.STATUS_CHOICES,
        'current_status': status,
        'current_moderator': moderator_id,
        'moderators': moderators
    })

@login_required
@user_passes_test(is_moderator)
def listing_approval_detail(request, pk):
    """View for reviewing a listing approval"""
    from .models import ListingApproval, ModerationLog

    approval = get_object_or_404(ListingApproval, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        moderator_notes = request.POST.get('moderator_notes', '').strip()

        if action in ['approve', 'reject', 'require_changes']:
            approval.moderator = request.user
            approval.moderator_notes = moderator_notes
            approval.reviewed_at = timezone.now()

            # Update checklist items
            approval.has_valid_title = request.POST.get('has_valid_title') == 'on'
            approval.has_valid_description = request.POST.get('has_valid_description') == 'on'
            approval.has_valid_images = request.POST.get('has_valid_images') == 'on'
            approval.has_valid_address = request.POST.get('has_valid_address') == 'on'
            approval.has_appropriate_pricing = request.POST.get('has_appropriate_pricing') == 'on'
            approval.follows_content_policy = request.POST.get('follows_content_policy') == 'on'
            approval.has_verification_video = request.POST.get('has_verification_video') == 'on'

            if action == 'approve':
                approval.status = 'approved'
                approval.listing.is_approved = True
                approval.listing.is_active = True
                approval.listing.save(update_fields=['is_approved', 'is_active'])

                # Log the action
                ModerationLog.objects.create(
                    moderator=request.user,
                    action_type='listing_approved',
                    target_listing=approval.listing,
                    target_user=approval.listing.host,
                    description=f"Approved listing: {approval.listing.title}",
                    notes=moderator_notes
                )

                messages.success(request, f"Listing '{approval.listing.title}' has been approved.")

            elif action == 'reject':
                approval.status = 'rejected'
                approval.rejection_reason = request.POST.get('rejection_reason', '').strip()
                approval.listing.is_approved = False
                approval.listing.is_active = False
                approval.listing.save(update_fields=['is_approved', 'is_active'])

                # Log the action
                ModerationLog.objects.create(
                    moderator=request.user,
                    action_type='listing_rejected',
                    target_listing=approval.listing,
                    target_user=approval.listing.host,
                    description=f"Rejected listing: {approval.listing.title}",
                    notes=f"Reason: {approval.rejection_reason}"
                )

                messages.success(request, f"Listing '{approval.listing.title}' has been rejected.")

            elif action == 'require_changes':
                approval.status = 'requires_changes'
                approval.required_changes = request.POST.get('required_changes', '').strip()
                approval.listing.is_approved = False
                approval.listing.save(update_fields=['is_approved'])

                messages.success(request, f"Changes required for listing '{approval.listing.title}'.")

            approval.save()

            return redirect('moderation:listing_approval_list')

    return render(request, 'moderation/listing_approval_detail.html', {
        'approval': approval,
        'listing': approval.listing
    })

@login_required
@user_passes_test(is_moderator)
def moderation_logs(request):
    """View for displaying moderation activity logs"""
    from .models import ModerationLog

    # Get all logs, filter by action type if provided
    action_type = request.GET.get('action_type')
    logs = ModerationLog.objects.select_related('moderator', 'target_user', 'target_listing').all()

    if action_type and action_type in [choice[0] for choice in ModerationLog.ACTION_TYPES]:
        logs = logs.filter(action_type=action_type)

    # Filter by moderator if provided
    moderator_id = request.GET.get('moderator')
    if moderator_id:
        try:
            logs = logs.filter(moderator_id=int(moderator_id))
        except ValueError:
            pass

    return render(request, 'moderation/logs.html', {
        'logs': logs,
        'action_type_choices': ModerationLog.ACTION_TYPES,
        'current_action_type': action_type,
        'current_moderator': moderator_id
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

@login_required
def file_complaint(request, listing_id):
    """File a complaint about a listing"""
    listing = get_object_or_404(Listing, id=listing_id)

    if request.method == 'POST':
        form = ListingComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            # Create complaint from form data
            complaint = UserComplaint.objects.create(
                complainant=request.user,
                listing=listing,
                complaint_type=form.cleaned_data['complaint_type'],
                subject=form.cleaned_data.get('subject') or f"Жалоба на объявление: {listing.title}",
                description=form.cleaned_data['description'],
                priority=form.cleaned_data['priority'],
                contact_email=form.cleaned_data.get('contact_email', ''),
                evidence_video=form.cleaned_data.get('evidence_video')
            )

            messages.success(request, 'Ваша жалоба была отправлена и будет рассмотрена.')
            return redirect('listings:listing_detail', pk=listing.pk)
    else:
        form = ListingComplaintForm()

    return render(request, 'moderation/file_complaint.html', {
        'form': form,
        'listing': listing,
        'complaint_type': 'listing'
    })

@login_required
def file_booking_complaint(request, booking_id):
    """File a complaint about a booking"""
    booking = get_object_or_404(Booking, id=booking_id)

    # Only allow guest or host to file complaints about their own bookings
    if request.user not in [booking.guest, booking.listing.host]:
        messages.error(request, 'У вас нет прав для подачи жалобы на это бронирование.')
        return redirect('listings:booking_detail', reference=booking.booking_reference)

    if request.method == 'POST':
        form = BookingComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            # Create complaint from form data
            complaint = UserComplaint.objects.create(
                complainant=request.user,
                booking=booking,
                listing=booking.listing,
                complaint_type=form.cleaned_data['complaint_type'],
                subject=form.cleaned_data.get('subject') or f"Жалоба на бронирование {booking.booking_reference}",
                description=form.cleaned_data['description'],
                priority=form.cleaned_data['priority'],
                contact_email=form.cleaned_data.get('contact_email', ''),
                evidence_video=form.cleaned_data.get('evidence_video')
            )

            messages.success(request, 'Ваша жалоба была отправлена и будет рассмотрена.')
            return redirect('listings:booking_detail', reference=booking.booking_reference)
    else:
        form = BookingComplaintForm()

    return render(request, 'moderation/file_complaint.html', {
        'form': form,
        'booking': booking,
        'listing': booking.listing,
        'complaint_type': 'booking'
    })

@login_required
def my_complaints(request):
    """View for users to see their own complaints"""
    complaints = UserComplaint.objects.filter(complainant=request.user).order_by('-created_at')

    # Pagination
    paginator = Paginator(complaints, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'moderation/my_complaints.html', {
        'complaints': page_obj
    })

@login_required
@user_passes_test(is_moderator)
def complaint_list(request):
    """View for moderators to see all complaints"""
    # Get filter parameters
    status = request.GET.get('status')
    complaint_type = request.GET.get('complaint_type')
    priority = request.GET.get('priority')
    assigned_moderator = request.GET.get('assigned_moderator')

    # Start with all complaints
    complaints = UserComplaint.objects.select_related('complainant', 'assigned_moderator').all()

    # Apply filters
    if status and status in [choice[0] for choice in UserComplaint.STATUS_CHOICES]:
        complaints = complaints.filter(status=status)

    if complaint_type and complaint_type in [choice[0] for choice in UserComplaint.COMPLAINT_TYPES]:
        complaints = complaints.filter(complaint_type=complaint_type)

    if priority and priority in [choice[0] for choice in UserComplaint.PRIORITY_CHOICES]:
        complaints = complaints.filter(priority=priority)

    if assigned_moderator:
        try:
            complaints = complaints.filter(assigned_moderator_id=int(assigned_moderator))
        except ValueError:
            pass

    # Order by priority and creation date
    priority_order = {'urgent': 1, 'high': 2, 'medium': 3, 'low': 4}
    complaints = sorted(complaints, key=lambda x: (priority_order.get(x.priority, 5), -x.created_at.timestamp()))

    # Pagination
    paginator = Paginator(complaints, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get moderators for filter dropdown
    moderators = User.objects.filter(is_staff=True)

    return render(request, 'moderation/complaint_list.html', {
        'complaints': page_obj,
        'status_choices': UserComplaint.STATUS_CHOICES,
        'complaint_type_choices': UserComplaint.COMPLAINT_TYPES,
        'priority_choices': UserComplaint.PRIORITY_CHOICES,
        'moderators': moderators,
        'current_status': status,
        'current_complaint_type': complaint_type,
        'current_priority': priority,
        'current_assigned_moderator': assigned_moderator
    })

@login_required
@user_passes_test(is_moderator)
def complaint_detail(request, pk):
    """View for moderators to handle a specific complaint"""
    complaint = get_object_or_404(UserComplaint, pk=pk)

    if request.method == 'POST':
        form = ComplaintResponseForm(request.POST)
        if form.is_valid():
            # Store original status for notifications
            original_status = complaint.status

            # Update complaint
            complaint.status = form.cleaned_data['status']
            complaint.moderator_response = form.cleaned_data['response']
            complaint.internal_notes = form.cleaned_data['internal_notes']
            complaint.assigned_moderator = request.user

            # Update priority if provided
            if form.cleaned_data.get('priority'):
                complaint.priority = form.cleaned_data['priority']

            complaint.save()

            # Handle additional actions
            action_type = form.cleaned_data.get('action_type')
            if action_type and complaint.reported_user:
                if action_type in ['temporary_ban', 'permanent_ban']:
                    ban_reason = form.cleaned_data.get('action_reason', 'Жалоба пользователя')
                    ban_days = form.cleaned_data.get('ban_duration_days') if action_type == 'temporary_ban' else None
                    is_permanent = action_type == 'permanent_ban'

                    # Calculate ban duration
                    banned_until = None
                    if not is_permanent and ban_days:
                        banned_until = timezone.now() + timezone.timedelta(days=ban_days)

                    # Create or update ban record
                    ban, created = BannedUser.objects.update_or_create(
                        user=complaint.reported_user,
                        defaults={
                            'reason': ban_reason,
                            'banned_until': banned_until,
                            'is_permanent': is_permanent,
                            'banned_by': request.user,
                            'notes': f"Ban issued from complaint #{complaint.id}"
                        }
                    )

                    messages.success(request, f"Пользователь {complaint.reported_user.username} был заблокирован.")

                elif action_type == 'deactivate_listing' and complaint.listing:
                    complaint.listing.is_active = False
                    complaint.listing.is_approved = False
                    complaint.listing.save(update_fields=['is_active', 'is_approved'])
                    
                    # Обновляем статус модерации объявления на "отклонено" вместо "требует изменений"
                    try:
                        approval_record = complaint.listing.approval_record
                        approval_record.status = 'rejected'
                        approval_record.moderator = request.user
                        approval_record.rejection_reason = f"Деактивировано по жалобе #{complaint.id}: {complaint.description[:100]}"
                        approval_record.reviewed_at = timezone.now()
                        approval_record.save()
                    except:
                        # Если записи модерации нет, создаем новую
                        from .models import ListingApproval
                        ListingApproval.objects.create(
                            listing=complaint.listing,
                            status='rejected',
                            moderator=request.user,
                            rejection_reason=f"Деактивировано по жалобе #{complaint.id}: {complaint.description[:100]}"
                        )
                    
                    messages.success(request, f"Объявление '{complaint.listing.title}' было деактивировано.")

                elif action_type == 'cancel_booking' and complaint.booking:
                    complaint.booking.status = 'canceled'
                    complaint.booking.save(update_fields=['status'])
                    messages.success(request, f"Бронирование {complaint.booking.booking_reference} было отменено.")

            # Create notification for complainant if status changed
            if original_status != complaint.status:
                from notifications.models import Notification
                status_display = complaint.get_status_display()

                Notification.objects.create(
                    user=complaint.complainant,
                    notification_type='system',
                    title=f"Обновление жалобы #{complaint.id}",
                    message=f"Статус вашей жалобы изменен на: {status_display}",
                )

            # Create a moderation log entry
            ModerationLog.objects.create(
                moderator=request.user,
                action_type='complaint_handled',
                target_user=complaint.complainant,
                description=f"Обработана жалоба #{complaint.id}: {complaint.subject}",
                notes=f"Статус: {complaint.get_status_display()}, Ответ: {complaint.moderator_response[:100]}..."
            )

            messages.success(request, f"Жалоба #{complaint.id} была обновлена.")
            return redirect('moderation:complaint_list')
    else:
        # Pre-fill form with current values
        initial_data = {
            'status': complaint.status,
            'priority': complaint.priority,
            'response': complaint.moderator_response,
            'internal_notes': complaint.internal_notes
        }
        form = ComplaintResponseForm(initial=initial_data)

    return render(request, 'moderation/complaint_detail.html', {
        'complaint': complaint,
        'form': form
    })