from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom User Admin"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_host', 'is_staff', 'verification_status')
    list_filter = ('is_host', 'is_guest', 'is_phone_verified', 'is_id_verified', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Profile Information', {
            'fields': ('phone_number', 'profile_picture', 'bio')
        }),
        ('Verification', {
            'fields': ('is_phone_verified', 'is_id_verified', 'is_host', 'is_guest')
        }),
        ('Notification Settings', {
            'fields': ('email_notifications', 'sms_notifications')
        }),
    )
    
    def verification_status(self, obj):
        return obj.verification_status
    verification_status.short_description = "Verification"
