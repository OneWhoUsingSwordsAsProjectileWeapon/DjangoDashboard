from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from datetime import date

class Listing(models.Model):
    """
    Property listing model
    """
    # Basic information
    title = models.CharField(_("Title"), max_length=100)
    description = models.TextField(_("Description"))
    address = models.CharField(_("Address"), max_length=255)
    city = models.CharField(_("City"), max_length=100)
    state = models.CharField(_("State/Province"), max_length=100)
    country = models.CharField(_("Country"), max_length=100)
    zip_code = models.CharField(_("ZIP/Postal Code"), max_length=20)
    
    # Pricing
    price_per_night = models.DecimalField(_("Price per night"), max_digits=10, decimal_places=2)
    cleaning_fee = models.DecimalField(_("Cleaning fee"), max_digits=10, decimal_places=2, default=0)
    service_fee = models.DecimalField(_("Service fee"), max_digits=10, decimal_places=2, default=0)
    
    # Property details
    bedrooms = models.PositiveSmallIntegerField(_("Bedrooms"))
    bathrooms = models.DecimalField(_("Bathrooms"), max_digits=3, decimal_places=1)
    accommodates = models.PositiveSmallIntegerField(_("Accommodates"))
    property_type = models.CharField(_("Property type"), max_length=50)
    
    # Images
    image_urls = models.JSONField(_("Image URLs"), default=list, null=True, blank=True)
    
    # Features/amenities
    amenities = models.JSONField(_("Amenities"), default=list)
    
    # Rules
    house_rules = models.TextField(_("House rules"), blank=True)
    check_in_time = models.TimeField(_("Check-in time"), null=True, blank=True)
    check_out_time = models.TimeField(_("Check-out time"), null=True, blank=True)
    minimum_nights = models.PositiveSmallIntegerField(_("Minimum nights"), default=1)
    maximum_nights = models.PositiveSmallIntegerField(_("Maximum nights"), default=30)
    
    # Status
    is_active = models.BooleanField(_("Is active"), default=True)
    is_approved = models.BooleanField(_("Is approved"), default=False)
    
    # Relationships
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='listings'
    )
    
    # Timestamps
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    
    class Meta:
        verbose_name = _("Listing")
        verbose_name_plural = _("Listings")
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse("listings:listing_detail", kwargs={"pk": self.pk})
    
    @property
    def main_image_url(self):
        """Return the first image URL or a placeholder"""
        if self.image_urls and len(self.image_urls) > 0:
            return self.image_urls[0]
        return "https://via.placeholder.com/800x600.png?text=No+Image+Available"
    
    @property
    def average_rating(self):
        """Calculate the average rating for this listing"""
        reviews = self.reviews.all()
        if not reviews:
            return None
        return sum(review.rating for review in reviews) / len(reviews)
    
    @property
    def total_reviews(self):
        """Count the total number of reviews"""
        return self.reviews.count()
    
    def is_available(self, start_date, end_date):
        """Check if listing is available for given dates"""
        # Convert string dates to date objects if needed
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)
            
        # Check for any conflicting bookings
        conflicting_bookings = self.bookings.filter(
            models.Q(start_date__lte=end_date, end_date__gte=start_date),
            status__in=['confirmed', 'pending']
        )
        
        # If there are any conflicting bookings, the listing is not available
        return not conflicting_bookings.exists()
    
    def get_unavailable_dates(self):
        """Get a list of dates that are booked"""
        from datetime import timedelta
        
        unavailable_dates = []
        confirmed_bookings = self.bookings.filter(status__in=['confirmed', 'pending'])
        
        for booking in confirmed_bookings:
            current_date = booking.start_date
            while current_date <= booking.end_date:
                unavailable_dates.append(current_date.isoformat())
                current_date += timedelta(days=1)
                
        return unavailable_dates
    
    def calculate_price(self, start_date, end_date):
        """Calculate the total price for a booking"""
        # Convert string dates to date objects if needed
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)
            
        # Calculate number of nights
        nights = (end_date - start_date).days
        
        # Calculate the base price
        base_price = self.price_per_night * nights
        
        # Add fees
        total_price = base_price + self.cleaning_fee + self.service_fee
        
        return {
            'base_price': base_price,
            'cleaning_fee': self.cleaning_fee,
            'service_fee': self.service_fee,
            'total_price': total_price,
            'nights': nights
        }

class Booking(models.Model):
    """
    Booking model for reservations
    """
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('confirmed', _('Confirmed')),
        ('canceled', _('Canceled')),
        ('completed', _('Completed')),
    ]
    
    # Booking details
    start_date = models.DateField(_("Check-in date"))
    end_date = models.DateField(_("Check-out date"))
    guests = models.PositiveSmallIntegerField(_("Number of guests"))
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Pricing
    base_price = models.DecimalField(_("Base price"), max_digits=10, decimal_places=2)
    cleaning_fee = models.DecimalField(_("Cleaning fee"), max_digits=10, decimal_places=2)
    service_fee = models.DecimalField(_("Service fee"), max_digits=10, decimal_places=2)
    total_price = models.DecimalField(_("Total price"), max_digits=10, decimal_places=2)
    
    # Additional information
    special_requests = models.TextField(_("Special requests"), blank=True)
    
    # Relationships
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    guest = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    
    # Unique booking reference
    booking_reference = models.UUIDField(_("Booking reference"), default=uuid.uuid4, editable=False, unique=True)
    
    # Timestamps
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    
    class Meta:
        verbose_name = _("Booking")
        verbose_name_plural = _("Bookings")
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Booking {self.booking_reference} - {self.listing.title}"
    
    def get_absolute_url(self):
        return reverse("listings:booking_detail", kwargs={"reference": self.booking_reference})
    
    @property
    def duration_nights(self):
        """Calculate the duration of the stay in nights"""
        return (self.end_date - self.start_date).days
    
    def can_be_canceled(self):
        """Check if booking can be canceled"""
        return self.status in ['pending', 'confirmed']
    
    def cancel(self):
        """Cancel the booking"""
        if self.can_be_canceled():
            self.status = 'canceled'
            self.save(update_fields=['status'])
            return True
        return False

class Review(models.Model):
    """
    Review model for listing reviews
    """
    # Review content
    rating = models.PositiveSmallIntegerField(
        _("Rating"), 
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(_("Comment"))
    
    # Relationships
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    booking = models.OneToOneField(
        Booking,
        on_delete=models.SET_NULL,
        related_name='review',
        null=True,
        blank=True
    )
    
    # Moderation
    is_approved = models.BooleanField(_("Is approved"), default=True)
    
    # Timestamps
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    
    class Meta:
        verbose_name = _("Review")
        verbose_name_plural = _("Reviews")
        ordering = ['-created_at']
        # Ensure one review per booking
        constraints = [
            models.UniqueConstraint(
                fields=['listing', 'reviewer', 'booking'],
                name='unique_booking_review'
            )
        ]
        
    def __str__(self):
        return f"Review by {self.reviewer.username} for {self.listing.title}"
