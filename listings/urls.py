from django.urls import path
from . import views

app_name = 'listings'

urlpatterns = [
    # Listing views
    path('', views.ListingListView.as_view(), name='listing_list'),
    path('<int:pk>/', views.ListingDetailView.as_view(), name='listing_detail'),
    path('create/', views.ListingCreateView.as_view(), name='listing_create'),
    path('<int:pk>/edit/', views.ListingUpdateView.as_view(), name='listing_update'),
    path('<int:pk>/delete/', views.ListingDeleteView.as_view(), name='listing_delete'),
    path('host-dashboard/', views.HostDashboardView.as_view(), name='host_dashboard'),
    path('my-listings/', views.HostListingListView.as_view(), name='host_listings'),
    
    # Listing images
    path('<int:pk>/images/', views.manage_listing_images, name='listing_images'),
    path('<int:pk>/images/add/', views.add_listing_image, name='add_listing_image'),
    path('<int:pk>/images/remove/<int:index>/', views.remove_listing_image, name='remove_listing_image'),
    
    # Booking views
    path('<int:pk>/book/', views.create_booking, name='create_booking'),
    path('bookings/<uuid:reference>/', views.booking_detail, name='booking_detail'),
    path('my-bookings/', views.user_bookings, name='user_bookings'),
    path('host-bookings/', views.host_bookings, name='host_bookings'),
    path('bookings/<uuid:reference>/status/<str:status>/', views.update_booking_status, name='update_booking_status'),
    
    # Review views
    path('bookings/<int:booking_id>/review/', views.create_review, name='create_review'),
    
    # API endpoints for HTMX
    path('api/<int:pk>/calendar-data/', views.get_listing_calendar_data, name='calendar_data'),
    path('api/<int:pk>/calculate-price/', views.calculate_booking_price, name='calculate_price'),
]
