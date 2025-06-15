from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """
    Custom user model with additional fields for rental platform
    """
    # Basic profile information
    phone_number = models.CharField(_("Phone number"), max_length=20, blank=True)
    profile_picture = models.ImageField(_("Profile picture"), upload_to='profile_pictures/', blank=True, null=True)
    bio = models.TextField(_("Bio"), blank=True)
    
    # Verification fields
    is_phone_verified = models.BooleanField(_("Phone verified"), default=False)
    is_id_verified = models.BooleanField(_("ID verified"), default=False)
    
    # User type
    is_host = models.BooleanField(_("Is host"), default=False)
    is_guest = models.BooleanField(_("Is guest"), default=True)
    
    # User role
    ROLE_CHOICES = [
        ('user', _('Regular User')),
        ('host', _('Host')),
        ('moderator', _('Moderator')),
        ('admin', _('Administrator')),
    ]
    role = models.CharField(_("Role"), max_length=20, choices=ROLE_CHOICES, default='user')
    
    # Notification preferences
    email_notifications = models.BooleanField(_("Email notifications"), default=True)
    sms_notifications = models.BooleanField(_("SMS notifications"), default=False)
    
    # Timestamp fields
    date_joined = models.DateTimeField(_("Date joined"), auto_now_add=True)
    last_updated = models.DateTimeField(_("Last updated"), auto_now=True)
    
    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        
    def __str__(self):
        return self.username
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def verification_status(self):
        """Returns user's verification level"""
        if self.is_id_verified:
            return "ID Verified"
        elif self.is_phone_verified:
            return "Phone Verified"
        return "Unverified"
    
    def toggle_host_status(self):
        """Toggle user's host status"""
        self.is_host = not self.is_host
        self.save(update_fields=['is_host'])
        return self.is_host
