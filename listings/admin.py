from django.contrib import admin
from .models import Listing, Booking, Review

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    """Admin interface for listings"""
    list_display = ('title', 'host', 'city', 'country', 'price_per_night', 'is_active', 'is_approved')
    list_filter = ('is_active', 'is_approved', 'property_type', 'country', 'city')
    search_fields = ('title', 'description', 'address', 'city', 'host__username')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_listings', 'unapprove_listings', 'activate_listings', 'deactivate_listings']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'host')
        }),
        ('Location', {
            'fields': ('address', 'city', 'state', 'country', 'zip_code')
        }),
        ('Pricing', {
            'fields': ('price_per_night', 'cleaning_fee', 'service_fee')
        }),
        ('Property Details', {
            'fields': ('bedrooms', 'bathrooms', 'accommodates', 'property_type', 'image_urls', 'amenities')
        }),
        ('Rules and Settings', {
            'fields': ('house_rules', 'check_in_time', 'check_out_time', 'minimum_nights', 'maximum_nights')
        }),
        ('Status', {
            'fields': ('is_active', 'is_approved')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def approve_listings(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"{queryset.count()} listings have been approved.")
    approve_listings.short_description = "Mark selected listings as approved"
    
    def unapprove_listings(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f"{queryset.count()} listings have been unapproved.")
    unapprove_listings.short_description = "Mark selected listings as unapproved"
    
    def activate_listings(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} listings have been activated.")
    activate_listings.short_description = "Activate selected listings"
    
    def deactivate_listings(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} listings have been deactivated.")
    deactivate_listings.short_description = "Deactivate selected listings"

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Admin interface for bookings"""
    list_display = ('booking_reference', 'listing', 'guest', 'start_date', 'end_date', 'status', 'total_price')
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('booking_reference', 'listing__title', 'guest__username', 'guest__email')
    readonly_fields = ('booking_reference', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('booking_reference', 'listing', 'guest')
        }),
        ('Dates and Guests', {
            'fields': ('start_date', 'end_date', 'guests')
        }),
        ('Pricing', {
            'fields': ('base_price', 'cleaning_fee', 'service_fee', 'total_price')
        }),
        ('Status and Requests', {
            'fields': ('status', 'special_requests')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_confirmed', 'mark_as_canceled', 'mark_as_completed']
    
    def mark_as_confirmed(self, request, queryset):
        queryset.update(status='confirmed')
        self.message_user(request, f"{queryset.count()} bookings have been marked as confirmed.")
    mark_as_confirmed.short_description = "Mark selected bookings as confirmed"
    
    def mark_as_canceled(self, request, queryset):
        queryset.update(status='canceled')
        self.message_user(request, f"{queryset.count()} bookings have been marked as canceled.")
    mark_as_canceled.short_description = "Mark selected bookings as canceled"
    
    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
        self.message_user(request, f"{queryset.count()} bookings have been marked as completed.")
    mark_as_completed.short_description = "Mark selected bookings as completed"

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Admin interface for reviews"""
    list_display = ('id', 'listing', 'reviewer', 'rating', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('comment', 'listing__title', 'reviewer__username')
    readonly_fields = ('created_at', 'updated_at')
    
    actions = ['approve_reviews', 'unapprove_reviews']
    
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"{queryset.count()} reviews have been approved.")
    approve_reviews.short_description = "Approve selected reviews"
    
    def unapprove_reviews(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f"{queryset.count()} reviews have been unapproved.")
    unapprove_reviews.short_description = "Unapprove selected reviews"
