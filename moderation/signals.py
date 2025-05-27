
from django.db.models.signals import post_save
from django.dispatch import receiver
from listings.models import Listing
from .models import ListingApproval

@receiver(post_save, sender=Listing)
def create_listing_approval(sender, instance, created, **kwargs):
    """
    Create a ListingApproval record when a new listing is created
    """
    if created:
        ListingApproval.objects.create(
            listing=instance,
            status='pending'
        )

@receiver(post_save, sender=Listing)
def save_listing_approval(sender, instance, **kwargs):
    """
    Update the listing approval status when listing is saved
    """
    try:
        approval = instance.approval_record
        # Auto-check some basic criteria
        approval.has_valid_title = bool(instance.title and len(instance.title.strip()) > 5)
        approval.has_valid_description = bool(instance.description and len(instance.description.strip()) > 20)
        approval.has_valid_images = bool(instance.image_urls and len(instance.image_urls) > 0)
        approval.has_valid_address = bool(instance.address and instance.city and instance.country)
        approval.has_appropriate_pricing = bool(instance.price_per_night and instance.price_per_night > 0)
        approval.save()
    except ListingApproval.DoesNotExist:
        pass
