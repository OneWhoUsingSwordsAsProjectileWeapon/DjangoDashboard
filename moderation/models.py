from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from listings.models import Listing, Review

class ReportCategory(models.Model):
    """
    Categories for reported content
    """
    name = models.CharField(_("Category Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Is Active"), default=True)
    
    class Meta:
        verbose_name = _("Report Category")
        verbose_name_plural = _("Report Categories")
        
    def __str__(self):
        return self.name

class Report(models.Model):
    """
    Model for users to report inappropriate content
    """
    STATUS_CHOICES = [
        ('pending', _('Pending Review')),
        ('in_progress', _('In Progress')),
        ('resolved', _('Resolved')),
        ('rejected', _('Rejected')),
    ]
    
    CONTENT_TYPES = [
        ('listing', _('Listing')),
        ('review', _('Review')),
        ('user', _('User')),
        ('message', _('Message')),
    ]
    
    # Reporter information
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports_filed',
        verbose_name=_("Reporter")
    )
    
    # Report details
    content_type = models.CharField(_("Content Type"), max_length=20, choices=CONTENT_TYPES)
    category = models.ForeignKey(
        ReportCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reports',
        verbose_name=_("Category")
    )
    description = models.TextField(_("Description"))
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Related objects (optional)
    listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports',
        verbose_name=_("Reported Listing")
    )
    review = models.ForeignKey(
        'listings.Review',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports',
        verbose_name=_("Reported Review")
    )
    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports_against',
        verbose_name=_("Reported User")
    )
    message = models.ForeignKey(
        'chat.Message',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reports',
        verbose_name=_("Reported Message")
    )
    
    # Moderator notes and actions
    moderator_notes = models.TextField(_("Moderator Notes"), blank=True)
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_reports',
        verbose_name=_("Moderator")
    )
    action_taken = models.CharField(_("Action Taken"), max_length=255, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    resolved_at = models.DateTimeField(_("Resolved At"), null=True, blank=True)
    
    class Meta:
        verbose_name = _("Report")
        verbose_name_plural = _("Reports")
        ordering = ['-created_at']
    
    def __str__(self):
        content_info = ""
        if self.content_type == 'listing' and self.listing:
            content_info = f"Listing: {self.listing.title}"
        elif self.content_type == 'review' and self.review:
            content_info = f"Review by {self.review.reviewer.username}"
        elif self.content_type == 'user' and self.reported_user:
            content_info = f"User: {self.reported_user.username}"
        elif self.content_type == 'message' and self.message:
            content_info = f"Message by {self.message.sender.username}"
            
        return f"Report #{self.id}: {self.content_type} - {content_info}"

class BannedUser(models.Model):
    """
    Model for managing banned users
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ban_record',
        verbose_name=_("User")
    )
    reason = models.TextField(_("Reason for Ban"))
    banned_until = models.DateTimeField(_("Banned Until"), null=True, blank=True)
    is_permanent = models.BooleanField(_("Permanent Ban"), default=False)
    banned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='banned_users',
        verbose_name=_("Banned By")
    )
    notes = models.TextField(_("Notes"), blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Banned User")
        verbose_name_plural = _("Banned Users")
        
    def __str__(self):
        return f"Ban: {self.user.username} - {'Permanent' if self.is_permanent else 'Until ' + str(self.banned_until)}"
    
    @property
    def is_active(self):
        """Check if the ban is currently active"""
        from django.utils import timezone
        if self.is_permanent:
            return True
        if self.banned_until and self.banned_until > timezone.now():
            return True
        return False

class ListingApproval(models.Model):
    """
    Model for tracking listing approval process
    """
    STATUS_CHOICES = [
        ('pending', _('Pending Review')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('requires_changes', _('Requires Changes')),
    ]
    
    listing = models.OneToOneField(
        'listings.Listing',
        on_delete=models.CASCADE,
        related_name='approval_record',
        verbose_name=_("Listing")
    )
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='pending')
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_listings',
        verbose_name=_("Moderator")
    )
    moderator_notes = models.TextField(_("Moderator Notes"), blank=True)
    rejection_reason = models.TextField(_("Rejection Reason"), blank=True)
    required_changes = models.TextField(_("Required Changes"), blank=True)
    
    # Approval criteria checklist
    has_valid_title = models.BooleanField(_("Has Valid Title"), default=False)
    has_valid_description = models.BooleanField(_("Has Valid Description"), default=False)
    has_valid_images = models.BooleanField(_("Has Valid Images"), default=False)
    has_valid_address = models.BooleanField(_("Has Valid Address"), default=False)
    has_appropriate_pricing = models.BooleanField(_("Has Appropriate Pricing"), default=False)
    follows_content_policy = models.BooleanField(_("Follows Content Policy"), default=False)
    
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    reviewed_at = models.DateTimeField(_("Reviewed At"), null=True, blank=True)
    
    class Meta:
        verbose_name = _("Listing Approval")
        verbose_name_plural = _("Listing Approvals")
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Approval for {self.listing.title} - {self.get_status_display()}"
    
    @property
    def approval_score(self):
        """Calculate approval score based on criteria"""
        criteria = [
            self.has_valid_title,
            self.has_valid_description,
            self.has_valid_images,
            self.has_valid_address,
            self.has_appropriate_pricing,
            self.follows_content_policy
        ]
        return sum(criteria) / len(criteria) * 100

class ModerationLog(models.Model):
    """
    Model for logging all moderation actions
    """
    ACTION_TYPES = [
        ('report_resolved', _('Report Resolved')),
        ('report_rejected', _('Report Rejected')),
        ('user_banned', _('User Banned')),
        ('user_unbanned', _('User Unbanned')),
        ('listing_approved', _('Listing Approved')),
        ('listing_rejected', _('Listing Rejected')),
        ('content_removed', _('Content Removed')),
        ('content_edited', _('Content Edited')),
    ]
    
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='moderation_actions',
        verbose_name=_("Moderator")
    )
    action_type = models.CharField(_("Action Type"), max_length=30, choices=ACTION_TYPES)
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderation_actions_received',
        verbose_name=_("Target User")
    )
    target_listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderation_actions',
        verbose_name=_("Target Listing")
    )
    report = models.ForeignKey(
        Report,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderation_logs',
        verbose_name=_("Related Report")
    )
    description = models.TextField(_("Description"))
    notes = models.TextField(_("Notes"), blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Moderation Log")
        verbose_name_plural = _("Moderation Logs")
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.get_action_type_display()} by {self.moderator.username} at {self.created_at}"

class UserComplaint(models.Model):
    """
    Model for user complaints about various issues
    """
    COMPLAINT_TYPES = [
        ('billing', _('Billing Issue')),
        ('booking', _('Booking Problem')),
        ('host_behavior', _('Host Behavior')),
        ('guest_behavior', _('Guest Behavior')),
        ('property_issue', _('Property Issue')),
        ('platform_bug', _('Platform Bug')),
        ('safety_concern', _('Safety Concern')),
        ('other', _('Other')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('in_progress', _('In Progress')),
        ('resolved', _('Resolved')),
        ('rejected', _('Rejected')),
        ('escalated', _('Escalated')),
    ]
    
    PRIORITY_CHOICES = [
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('urgent', _('Urgent')),
    ]
    
    # User information
    complainant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='complaints_filed',
        verbose_name=_("Complainant")
    )
    
    # Complaint details
    complaint_type = models.CharField(_("Complaint Type"), max_length=20, choices=COMPLAINT_TYPES)
    subject = models.CharField(_("Subject"), max_length=200)
    description = models.TextField(_("Description"))
    priority = models.CharField(_("Priority"), max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(_("Status"), max_length=15, choices=STATUS_CHOICES, default='pending')
    
    # Optional contact information
    contact_email = models.EmailField(_("Contact Email"), blank=True)
    
    # Related objects (optional)
    related_listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='complaints',
        verbose_name=_("Related Listing")
    )
    
    # Moderator response
    assigned_moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_complaints',
        verbose_name=_("Assigned Moderator")
    )
    moderator_response = models.TextField(_("Moderator Response"), blank=True)
    internal_notes = models.TextField(_("Internal Notes"), blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    resolved_at = models.DateTimeField(_("Resolved At"), null=True, blank=True)
    
    class Meta:
        verbose_name = _("User Complaint")
        verbose_name_plural = _("User Complaints")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Complaint #{self.id}: {self.subject} - {self.get_status_display()}"
    
    @property
    def is_urgent(self):
        """Check if complaint is marked as urgent"""
        return self.priority == 'urgent'
    
    @property
    def days_open(self):
        """Calculate how many days the complaint has been open"""
        from django.utils import timezone
        if self.resolved_at:
            return (self.resolved_at - self.created_at).days
        return (timezone.now() - self.created_at).days

class ForbiddenKeyword(models.Model):
    """
    Model for storing forbidden keywords to be filtered in content
    """
    keyword = models.CharField(_("Keyword"), max_length=100, unique=True)
    replacement = models.CharField(_("Replacement"), max_length=100, blank=True)
    is_regex = models.BooleanField(_("Is Regular Expression"), default=False)
    is_active = models.BooleanField(_("Is Active"), default=True)
    severity = models.PositiveSmallIntegerField(
        _("Severity"), 
        choices=[
            (1, _('Low')),
            (2, _('Medium')),
            (3, _('High')),
        ],
        default=2
    )
    notes = models.TextField(_("Notes"), blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    
    class Meta:
        verbose_name = _("Forbidden Keyword")
        verbose_name_plural = _("Forbidden Keywords")
        
    def __str__(self):
        return f"{self.keyword} ({self.get_severity_display()})"
