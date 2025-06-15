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

    # Image management
    path('listing/<int:pk>/images/', views.manage_listing_images, name='listing_images'),
    path('listing/<int:pk>/add-image/', views.add_listing_image, name='add_listing_image'),
    path('listing/<int:pk>/remove-image/<int:index>/', views.remove_listing_image, name='remove_listing_image'),
    path('listing/<int:pk>/remove-image-file/<int:image_id>/', views.remove_image_file, name='remove_image_file'),
    path('listing/<int:pk>/set-main-image/<int:image_id>/', views.set_main_image, name='set_main_image'),

    # Dashboard export
    path('host-dashboard/export/', views.export_dashboard_excel, name='export_dashboard'),

    # Booking views
    path('<int:pk>/book/', views.create_booking, name='create_booking'),
    path('bookings/<uuid:reference>/', views.booking_detail, name='booking_detail'),
    path('booking/<uuid:reference>/', views.booking_detail, name='booking_detail_alt'),
    path('my-bookings/', views.user_bookings, name='user_bookings'),
    path('my-reviews/', views.user_reviews, name='user_reviews'),
    path('host-bookings/', views.host_bookings, name='host_bookings'),
    path('bookings/<uuid:reference>/status/<str:status>/', views.update_booking_status, name='update_booking_status'),

    # Review views
    path('listing/<int:listing_id>/review/', views.create_review, name='create_review'),
    path('reviews/<int:review_id>/edit/', views.edit_review, name='edit_review'),
    path('reviews/<int:review_id>/delete/', views.delete_review, name='delete_review'),
    path('reviews/<int:review_id>/admin-delete/', views.admin_delete_review, name='admin_delete_review'),
    path('reviews/create-host-review/<int:host_id>/', views.create_host_review, name='create_host_review'),

    # API endpoints for HTMX
    path('api/<int:pk>/calendar-data/', views.get_listing_calendar_data, name='calendar_data'),
    path('api/<int:pk>/calculate-price/', views.calculate_booking_price, name='calculate_price'),
    path('api/<int:pk>/toggle-status/', views.toggle_listing_status, name='toggle_listing_status'),
]