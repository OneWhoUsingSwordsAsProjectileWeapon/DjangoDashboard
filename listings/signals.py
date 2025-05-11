"""
Signal handlers for the listings app.

This module contains signal handlers for listings-related events,
such as handling booking updates, review notifications, etc.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

try:
    from .models import Listing, Booking, Review
    # We'll use this to check if models are available
    LISTING_MODELS_AVAILABLE = True
except ImportError:
    # During initial app loading, models might not be available yet
    LISTING_MODELS_AVAILABLE = False

# Only register signals if the models are available
if LISTING_MODELS_AVAILABLE:
    @receiver(post_save, sender=Booking)
    def booking_created_handler(sender, instance, created, **kwargs):
        """
        Handler for when a booking is created or updated.
        """
        if created:
            # Logic for new booking
            print(f"New booking created: {instance.booking_reference}")
            
            # You could implement notification logic, availability updates, etc. here
        else:
            # Logic for booking updates
            print(f"Booking updated: {instance.booking_reference}")
            
    @receiver(post_save, sender=Review)
    def review_created_handler(sender, instance, created, **kwargs):
        """
        Handler for when a review is created.
        """
        if created:
            # Logic for new review
            print(f"New review for listing {instance.listing.id} created")
            
            # You could implement notification logic, rating updates, etc. here