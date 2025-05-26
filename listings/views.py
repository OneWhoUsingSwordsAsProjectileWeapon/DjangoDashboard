from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Count, Sum
from django.db import models
from django.http import JsonResponse, Http404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from datetime import datetime, timedelta
import json

from .models import Listing, Booking, Review
from .forms import ListingForm, BookingForm, ReviewForm, ListingSearchForm, ListingImageForm
from notifications.tasks import send_email_notification

class ListingListView(ListView):
    """View for displaying list of listings with search and filtering"""
    model = Listing
    template_name = 'listings/listing_list.html'
    context_object_name = 'listings'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Listing.objects.filter(is_active=True, is_approved=True)
        
        # Apply search and filters if form is submitted
        form = ListingSearchForm(self.request.GET)
        if form.is_valid():
            # Location search
            location = form.cleaned_data.get('location')
            if location:
                queryset = queryset.filter(
                    Q(city__icontains=location) | 
                    Q(state__icontains=location) |
                    Q(country__icontains=location)
                )
            
            # Date availability
            check_in = form.cleaned_data.get('check_in')
            check_out = form.cleaned_data.get('check_out')
            if check_in and check_out:
                # Get all bookings that overlap with requested dates
                overlapping_bookings = Booking.objects.filter(
                    Q(start_date__lte=check_out, end_date__gte=check_in),
                    status__in=['confirmed', 'pending']
                ).values_list('listing_id', flat=True)
                
                # Exclude listings with overlapping bookings
                queryset = queryset.exclude(id__in=overlapping_bookings)
            
            # Guest capacity
            guests = form.cleaned_data.get('guests')
            if guests:
                queryset = queryset.filter(accommodates__gte=guests)
            
            # Price range
            min_price = form.cleaned_data.get('min_price')
            if min_price:
                queryset = queryset.filter(price_per_night__gte=min_price)
                
            max_price = form.cleaned_data.get('max_price')
            if max_price:
                queryset = queryset.filter(price_per_night__lte=max_price)
            
            # Property type
            property_type = form.cleaned_data.get('property_type')
            if property_type:
                queryset = queryset.filter(property_type=property_type)
            
            # Bedrooms
            bedrooms = form.cleaned_data.get('bedrooms')
            if bedrooms:
                queryset = queryset.filter(bedrooms__gte=bedrooms)
            
            # Bathrooms
            bathrooms = form.cleaned_data.get('bathrooms')
            if bathrooms:
                queryset = queryset.filter(bathrooms__gte=bathrooms)
        
        # Annotate with average rating
        queryset = queryset.annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add search form to context
        context['form'] = ListingSearchForm(self.request.GET)
        return context

class ListingDetailView(DetailView):
    """View for displaying listing details"""
    model = Listing
    template_name = 'listings/listing_detail.html'
    context_object_name = 'listing'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        listing = self.get_object()
        
        # Add booking form
        context['booking_form'] = BookingForm(listing=listing)
        
        # Get reviews
        reviews = listing.reviews.filter(is_approved=True).select_related('reviewer')
        context['reviews'] = reviews
        
        # Check if user can leave a review
        user = self.request.user
        can_review = False
        if user.is_authenticated:
            # User can review if they have completed a booking and haven't reviewed yet
            completed_bookings = Booking.objects.filter(
                guest=user,
                listing=listing,
                status='completed'
            )
            if completed_bookings.exists() and not Review.objects.filter(
                reviewer=user, 
                listing=listing, 
                booking__in=completed_bookings
            ).exists():
                context['review_form'] = ReviewForm()
                context['can_review'] = True
                context['booking_for_review'] = completed_bookings.first()
        
        # Unavailable dates for calendar
        context['unavailable_dates_json'] = json.dumps(listing.get_unavailable_dates())
        
        return context

class HostDashboardView(LoginRequiredMixin, ListView):
    """Comprehensive host dashboard view"""
    template_name = 'listings/host_dashboard.html'
    
    def get(self, request, *args, **kwargs):
        # Check if user is a host
        if not request.user.is_host:
            messages.error(request, "You are not registered as a host.")
            return redirect('listings:listing_create')
        
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get host's listings
        host_listings = Listing.objects.filter(host=user)
        
        # Get host's bookings
        host_bookings = Booking.objects.filter(listing__host=user)
        
        # Calculate statistics
        stats = {
            'total_listings': host_listings.count(),
            'active_bookings': host_bookings.filter(status__in=['confirmed', 'pending']).count(),
            'pending_bookings': host_bookings.filter(status='pending').count(),
            'total_revenue': host_bookings.filter(status='completed').aggregate(
                total=Sum('total_price')
            )['total'] or 0,
        }
        
        # Get recent bookings (last 5)
        recent_bookings = host_bookings.select_related(
            'listing', 'guest'
        ).order_by('-created_at')[:5]
        
        # Get top performing listings
        top_listings = host_listings.annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews'),
            bookings_count=Count('bookings')
        ).order_by('-avg_rating', '-review_count')[:5]
        
        context.update({
            'stats': stats,
            'recent_bookings': recent_bookings,
            'top_listings': top_listings,
        })
        
        return context

class HostListingListView(LoginRequiredMixin, ListView):
    """View for host to see their own listings"""
    model = Listing
    template_name = 'listings/host_listings.html'
    context_object_name = 'listings'
    
    def get_queryset(self):
        # Only show listings owned by current user
        return Listing.objects.filter(host=self.request.user)

class ListingCreateView(LoginRequiredMixin, CreateView):
    """View for creating a new listing"""
    model = Listing
    form_class = ListingForm
    template_name = 'listings/listing_form.html'
    
    def form_valid(self, form):
        # Set the host to current user
        form.instance.host = self.request.user
        
        # Make sure user is marked as a host
        user = self.request.user
        if not user.is_host:
            user.is_host = True
            user.save(update_fields=['is_host'])
        
        # Save the listing
        response = super().form_valid(form)
        
        # Add success message
        messages.success(self.request, 'Your listing has been created and is pending approval.')
        
        return response

class ListingUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View for updating an existing listing"""
    model = Listing
    form_class = ListingForm
    template_name = 'listings/listing_form.html'
    
    def test_func(self):
        # Check if current user is the host
        listing = self.get_object()
        return self.request.user == listing.host
    
    def form_valid(self, form):
        # Reset approval status if significant fields changed
        significant_fields = ['price_per_night', 'title', 'description', 'address']
        if any(form.cleaned_data.get(field) != getattr(self.get_object(), field) for field in significant_fields):
            form.instance.is_approved = False
        
        response = super().form_valid(form)
        messages.success(self.request, 'Your listing has been updated.')
        return response

class ListingDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """View for deleting a listing"""
    model = Listing
    template_name = 'listings/listing_confirm_delete.html'
    success_url = reverse_lazy('listings:host_listings')
    
    def test_func(self):
        # Check if current user is the host
        listing = self.get_object()
        return self.request.user == listing.host
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Your listing has been deleted.')
        return super().delete(request, *args, **kwargs)

@login_required
def add_listing_image(request, pk):
    """View for adding an image to a listing"""
    listing = get_object_or_404(Listing, pk=pk, host=request.user)
    
    if request.method == 'POST':
        form = ListingImageForm(request.POST)
        if form.is_valid():
            image_url = form.cleaned_data['image_url']
            # Add the image URL to the listing's image_urls array
            image_urls = listing.image_urls
            image_urls.append(image_url)
            listing.image_urls = image_urls
            listing.save(update_fields=['image_urls'])
            
            messages.success(request, 'Image added successfully.')
            return redirect('listings:listing_images', pk=listing.pk)
    else:
        form = ListingImageForm()
    
    return render(request, 'listings/add_image.html', {
        'form': form,
        'listing': listing
    })

@login_required
def manage_listing_images(request, pk):
    """View for managing listing images"""
    listing = get_object_or_404(Listing, pk=pk, host=request.user)
    
    return render(request, 'listings/manage_images.html', {
        'listing': listing
    })

@login_required
def remove_listing_image(request, pk, index):
    """View for removing an image from a listing"""
    listing = get_object_or_404(Listing, pk=pk, host=request.user)
    
    try:
        image_urls = listing.image_urls
        if 0 <= index < len(image_urls):
            # Remove the image at the specified index
            del image_urls[index]
            listing.image_urls = image_urls
            listing.save(update_fields=['image_urls'])
            messages.success(request, 'Image removed successfully.')
        else:
            messages.error(request, 'Invalid image index.')
    except (TypeError, IndexError):
        messages.error(request, 'Error removing image.')
    
    return redirect('listings:listing_images', pk=listing.pk)

@login_required
def create_booking(request, pk):
    """View for creating a booking"""
    listing = get_object_or_404(Listing, pk=pk, is_active=True, is_approved=True)
    
    # Check if user is trying to book their own listing
    if request.user == listing.host:
        messages.error(request, "You cannot book your own listing.")
        return redirect('listings:listing_detail', pk=listing.pk)
    
    if request.method == 'POST':
        form = BookingForm(listing, request.POST)
        if form.is_valid():
            # Create booking but don't save yet
            booking = form.save(commit=False)
            booking.listing = listing
            booking.guest = request.user
            
            # Calculate the price
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            price_data = listing.calculate_price(start_date, end_date)
            
            booking.base_price = price_data['base_price']
            booking.cleaning_fee = price_data['cleaning_fee']
            booking.service_fee = price_data['service_fee']
            booking.total_price = price_data['total_price']
            
            # Save the booking
            booking.save()
            
            # Send notifications
            guest_message = f"Your booking for {listing.title} has been created. " \
                           f"Check-in: {start_date}, Check-out: {end_date}. " \
                           f"Total price: ${booking.total_price}"
            
            host_message = f"New booking request for your listing '{listing.title}'. " \
                          f"Guest: {request.user.get_full_name() or request.user.username}, " \
                          f"Check-in: {start_date}, Check-out: {end_date}."
            
            # Send email notifications
            send_email_notification(
                request.user.email,
                "Booking Confirmation",
                guest_message
            )
            
            send_email_notification(
                listing.host.email,
                "New Booking Request",
                host_message
            )
            
            messages.success(request, "Booking created successfully. Awaiting host confirmation.")
            return redirect('listings:booking_detail', reference=booking.booking_reference)
    else:
        # Pre-fill form with query parameters if provided
        initial = {}
        if 'check_in' in request.GET:
            try:
                initial['start_date'] = datetime.strptime(request.GET['check_in'], '%Y-%m-%d').date()
            except ValueError:
                pass
        
        if 'check_out' in request.GET:
            try:
                initial['end_date'] = datetime.strptime(request.GET['check_out'], '%Y-%m-%d').date()
            except ValueError:
                pass
                
        if 'guests' in request.GET:
            try:
                initial['guests'] = int(request.GET['guests'])
            except ValueError:
                pass
                
        form = BookingForm(listing, initial=initial)
    
    return render(request, 'listings/booking_form.html', {
        'form': form,
        'listing': listing
    })

@login_required
def booking_detail(request, reference):
    """View for displaying booking details"""
    try:
        # Get booking and check permissions
        booking = Booking.objects.select_related('listing', 'guest', 'listing__host').get(
            booking_reference=reference
        )
        
        # Only allow access to guest or host
        if request.user != booking.guest and request.user != booking.listing.host:
            raise Http404("Booking not found")
            
        return render(request, 'listings/booking_detail.html', {
            'booking': booking
        })
    except Booking.DoesNotExist:
        raise Http404("Booking not found")

@login_required
def user_bookings(request):
    """View for displaying user's bookings"""
    # Get all bookings for the user
    bookings = Booking.objects.filter(guest=request.user).select_related('listing')
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status and status in [choice[0] for choice in Booking.STATUS_CHOICES]:
        bookings = bookings.filter(status=status)
    
    return render(request, 'listings/user_bookings.html', {
        'bookings': bookings,
        'status_choices': Booking.STATUS_CHOICES,
        'current_status': status
    })

@login_required
def host_bookings(request):
    """View for displaying host's bookings"""
    # Check if user is a host
    if not request.user.is_host:
        messages.error(request, "You are not registered as a host.")
        return redirect('listings:listing_list')
    
    # Get all bookings for the host's listings
    bookings = Booking.objects.filter(
        listing__host=request.user
    ).select_related('listing', 'guest')
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status and status in [choice[0] for choice in Booking.STATUS_CHOICES]:
        bookings = bookings.filter(status=status)
    
    return render(request, 'listings/host_bookings.html', {
        'bookings': bookings,
        'status_choices': Booking.STATUS_CHOICES,
        'current_status': status
    })

@login_required
def update_booking_status(request, reference, status):
    """View for updating booking status"""
    if status not in [choice[0] for choice in Booking.STATUS_CHOICES]:
        messages.error(request, "Invalid booking status.")
        return redirect('listings:host_bookings')
    
    try:
        booking = Booking.objects.select_related('listing').get(booking_reference=reference)
        
        # Verify permissions
        if request.user != booking.listing.host and not (request.user == booking.guest and status == 'canceled'):
            messages.error(request, "You don't have permission to perform this action.")
            return redirect('listings:listing_list')
        
        # Prevent certain status changes
        if booking.status == 'completed' and status != 'completed':
            messages.error(request, "Cannot change status of a completed booking.")
            return redirect('listings:booking_detail', reference=reference)
        
        # Update booking status
        booking.status = status
        booking.save(update_fields=['status'])
        
        # Send notification
        if status == 'confirmed':
            message = f"Your booking for {booking.listing.title} has been confirmed by the host. " \
                     f"Check-in: {booking.start_date}, Check-out: {booking.end_date}."
            
            send_email_notification(
                booking.guest.email,
                "Booking Confirmed",
                message
            )
        elif status == 'canceled':
            # Determine who canceled
            canceler = "host" if request.user == booking.listing.host else "you"
            
            # Send to guest
            if request.user == booking.listing.host:
                message = f"Your booking for {booking.listing.title} has been canceled by the host. " \
                         f"Check-in: {booking.start_date}, Check-out: {booking.end_date}."
                
                send_email_notification(
                    booking.guest.email,
                    "Booking Canceled",
                    message
                )
            
            # Send to host
            if request.user == booking.guest:
                message = f"Booking for {booking.listing.title} has been canceled by the guest. " \
                         f"Guest: {booking.guest.get_full_name() or booking.guest.username}, " \
                         f"Check-in: {booking.start_date}, Check-out: {booking.end_date}."
                
                send_email_notification(
                    booking.listing.host.email,
                    "Booking Canceled",
                    message
                )
        
        messages.success(request, f"Booking status updated to {status}.")
        return redirect('listings:booking_detail', reference=reference)
    
    except Booking.DoesNotExist:
        raise Http404("Booking not found")

@login_required
def create_review(request, booking_id):
    """View for creating a review for a booking"""
    booking = get_object_or_404(
        Booking, 
        id=booking_id, 
        guest=request.user, 
        status='completed'
    )
    
    # Check if review already exists
    if Review.objects.filter(booking=booking).exists():
        messages.error(request, "You have already reviewed this booking.")
        return redirect('listings:listing_detail', pk=booking.listing.pk)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.listing = booking.listing
            review.reviewer = request.user
            review.booking = booking
            review.save()
            
            messages.success(request, "Your review has been submitted!")
            return redirect('listings:listing_detail', pk=booking.listing.pk)
    else:
        form = ReviewForm()
    
    return render(request, 'listings/review_form.html', {
        'form': form,
        'booking': booking,
        'listing': booking.listing
    })

def get_listing_calendar_data(request, pk):
    """API view for getting listing calendar data"""
    try:
        listing = Listing.objects.get(pk=pk)
        
        # Get unavailable dates
        unavailable_dates = listing.get_unavailable_dates()
        
        # Return as JSON
        return JsonResponse({
            'unavailable_dates': unavailable_dates
        })
    except Listing.DoesNotExist:
        return JsonResponse({'error': 'Listing not found'}, status=404)

def calculate_booking_price(request, pk):
    """API view for calculating booking price"""
    try:
        listing = Listing.objects.get(pk=pk)
        
        # Get dates from request
        start_date = request.GET.get('start_date') or request.GET.get('check_in')
        end_date = request.GET.get('end_date') or request.GET.get('check_out')
        
        if not start_date or not end_date:
            return JsonResponse({
                'error': 'Пожалуйста, укажите даты заезда и выезда'
            }, status=400)
        
        # Calculate price
        try:
            price_data = listing.calculate_price(start_date, end_date)
            
            # Check availability
            is_available = listing.is_available(start_date, end_date)
            
            return JsonResponse({
                'base_price': float(price_data['base_price']),
                'cleaning_fee': float(price_data['cleaning_fee']),
                'service_fee': float(price_data['service_fee']),
                'total_price': float(price_data['total_price']),
                'nights': price_data['nights'],
                'is_available': is_available
            })
        except (ValueError, TypeError):
            return JsonResponse({
                'error': 'Неверный формат даты. Используйте ГГГГ-ММ-ДД.'
            }, status=400)
            
    except Listing.DoesNotExist:
        return JsonResponse({'error': 'Listing not found'}, status=404)
