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
    has_verification_video = models.BooleanField(_("Has Verification Video"), default=False)

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
            self.follows_content_policy,
            self.has_verification_video
        ]
        return sum(criteria) / len(criteria) * 100

    def save(self, *args, **kwargs):
        """Override save to log status changes"""
        from django.utils import timezone
        
        # Track if this is a status change
        old_status = None
        if self.pk:
            try:
                old_instance = ListingApproval.objects.get(pk=self.pk)
                old_status = old_instance.status
            except ListingApproval.DoesNotExist:
                pass
        
        # Set reviewed_at if status is changing from pending
        if old_status == 'pending' and self.status != 'pending' and not self.reviewed_at:
            self.reviewed_at = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Log status change if it occurred
        if old_status and old_status != self.status:
            try:
                action_map = {
                    'approved': 'listing_approved',
                    'rejected': 'listing_rejected',
                    'requires_changes': 'listing_requires_changes',
                    'pending': 'listing_pending'
                }
                
                action_type = action_map.get(self.status, 'listing_status_changed')
                
                ModerationLog.objects.create(
                    moderator=self.moderator or self.listing.host,  # Fallback to host if no moderator
                    action_type=action_type,
                    target_listing=self.listing,
                    target_user=self.listing.host,
                    description=f"Статус модерации изменен с '{old_status}' на '{self.status}' для объявления: {self.listing.title}",
                    notes=f"Автоматическое логирование изменения статуса"
                )
            except Exception:
                # Don't fail the save if logging fails
                pass

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
        ('listing_requires_changes', _('Listing Requires Changes')),
        ('listing_pending', _('Listing Pending Review')),
        ('listing_status_changed', _('Listing Status Changed')),
        ('content_removed', _('Content Removed')),
        ('content_edited', _('Content Edited')),
        ('subscription_created', _('Subscription Created')),
        ('subscription_renewed', _('Subscription Renewed')),
        ('subscription_canceled', _('Subscription Canceled')),
        ('subscription_expired', _('Subscription Expired')),
        ('complaint_handled', _('Complaint Handled')),
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
    Model for user complaints about bookings, listings or hosts
    """
    COMPLAINT_TYPES = [
        ('booking_issue', 'Проблема с бронированием'),
        ('listing_issue', 'Проблема с объявлением'),
        ('host_behavior', 'Поведение хоста'),
        ('guest_behavior', 'Поведение гостя'),
        ('safety_concern', 'Вопросы безопасности'),
        ('false_listing', 'Ложная информация в объявлении'),
        ('discrimination', 'Дискриминация'),
        ('payment_issue', 'Проблемы с оплатой'),
        ('cleanliness', 'Чистота'),
        ('other', 'Другое'),
    ]

    STATUS_CHOICES = [
        ('pending', 'В ожидании'),
        ('in_progress', 'В обработке'),
        ('investigating', 'Расследуется'),
        ('awaiting_response', 'Ожидает ответа'),
        ('resolved', 'Решено'),
        ('dismissed', 'Отклонено'),
        ('escalated', 'Эскалировано'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('urgent', 'Срочный'),
    ]

    complainant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='complaints_made',
        verbose_name='Заявитель'
    )

    # Booking is now the primary reference point
    booking = models.ForeignKey(
        'listings.Booking',
        on_delete=models.CASCADE,
        related_name='complaints',
        null=True,
        blank=True,
        verbose_name='Бронирование'
    )

    # Listing can be optional now, since we can get it from booking
    listing = models.ForeignKey(
        'listings.Listing',
        on_delete=models.CASCADE,
        related_name='complaints',
        null=True,
        blank=True,
        verbose_name='Объявление'
    )

    # The person being complained about
    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='complaints_received',
        null=True,
        blank=True,
        verbose_name='Пользователь, на которого жалуются'
    )

    complaint_type = models.CharField(
        'Тип жалобы',
        max_length=20,
        choices=COMPLAINT_TYPES,
        default='booking_issue'
    )

    subject = models.CharField(
        'Тема жалобы',
        max_length=200,
        default='Жалоба'
    )

    description = models.TextField('Описание жалобы')

    priority = models.CharField(
        'Приоритет',
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )

    status = models.CharField(
        'Статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # Moderator handling
    assigned_moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_complaints',
        verbose_name='Назначенный модератор'
    )

    moderator_response = models.TextField(
        'Ответ модератора',
        blank=True,
        help_text='Ответ, который увидит пользователь'
    )

    internal_notes = models.TextField(
        'Внутренние заметки',
        blank=True,
        help_text='Заметки для внутреннего использования'
    )

    # Contact info
    contact_email = models.EmailField(
        'Контактный email',
        blank=True,
        help_text='Альтернативный email для связи'
    )

    # Evidence video
    evidence_video = models.FileField(
        'Видео-доказательство',
        upload_to='complaint_videos/',
        null=True,
        blank=True,
        help_text='Загрузите видео в качестве доказательства (макс. 100МБ)'
    )

    # Timestamps
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    resolved_at = models.DateTimeField('Решено', null=True, blank=True)
    first_response_at = models.DateTimeField('Первый ответ', null=True, blank=True)

    class Meta:
        verbose_name = 'Жалоба пользователя'
        verbose_name_plural = 'Жалобы пользователей'
        ordering = ['-created_at']

    def __str__(self):
        if self.booking:
            return f"Жалоба #{self.id} от {self.complainant.username} на бронирование {self.booking.booking_reference}"
        elif self.listing:
            return f"Жалоба #{self.id} от {self.complainant.username} на объявление {self.listing.title}"
        else:
            return f"Жалоба #{self.id} от {self.complainant.username}"

    @property
    def days_open(self):
        """Calculate how many days the complaint has been open"""
        from django.utils import timezone
        if self.resolved_at:
            return (self.resolved_at - self.created_at).days
        return (timezone.now() - self.created_at).days

    @property
    def is_overdue(self):
        """Check if complaint is overdue based on priority"""
        priority_days = {
            'urgent': 1,
            'high': 3,
            'medium': 7,
            'low': 14
        }
        max_days = priority_days.get(self.priority, 7)
        return self.days_open > max_days and self.status not in ['resolved', 'dismissed']

    def get_related_object_url(self):
        """Get URL to the related object (booking or listing)"""
        from django.urls import reverse
        if self.booking:
            return reverse('listings:booking_detail', kwargs={'reference': self.booking.booking_reference})
        elif self.listing:
            return reverse('listings:listing_detail', kwargs={'pk': self.listing.id})
        return None

    def get_related_object_display(self):
        """Get display name for the related object"""
        if self.booking:
            return f"Бронирование {self.booking.booking_reference}"
        elif self.listing:
            return f"Объявление: {self.listing.title}"
        return "Нет связанного объекта"

    def save(self, *args, **kwargs):
        from django.utils import timezone

        # Auto-populate listing from booking if not set
        if self.booking and not self.listing:
            self.listing = self.booking.listing

        # Auto-populate reported_user if not set
        if not self.reported_user:
            if self.booking:
                # If complainant is guest, reported user is host
                if self.complainant == self.booking.guest:
                    self.reported_user = self.booking.listing.host
                # If complainant is host, reported user is guest
                elif self.complainant == self.booking.listing.host:
                    self.reported_user = self.booking.guest
            elif self.listing:
                # For listing complaints, reported user is the host
                if self.complainant != self.listing.host:
                    self.reported_user = self.listing.host

        # Auto-generate subject if not provided
        if not self.subject or self.subject == 'Жалоба':
            if self.booking:
                self.subject = f"Жалоба на бронирование {self.booking.booking_reference}"
            elif self.listing:
                self.subject = f"Жалоба на объявление: {self.listing.title[:50]}"
            else:
                self.subject = f"Жалоба от {self.complainant.username}"

        # Set resolved timestamp
        if self.status in ['resolved', 'dismissed'] and not self.resolved_at:
            self.resolved_at = timezone.now()
        elif self.status not in ['resolved', 'dismissed']:
            self.resolved_at = None

        # Set first response timestamp
        if self.moderator_response and not self.first_response_at:
            self.first_response_at = timezone.now()

        super().save(*args, **kwargs)

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