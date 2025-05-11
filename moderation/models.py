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
