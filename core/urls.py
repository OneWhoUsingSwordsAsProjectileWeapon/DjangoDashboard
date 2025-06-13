"""
URL configuration for the rental project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from subscriptions import views
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(pattern_name='listings:listing_list'), name='home'),
    path('listings/', include('listings.urls')),
    path('users/', include('users.urls')),
    path('chat/', include('chat.urls')),
    path('notifications/', include('notifications.urls')),
    path('moderation/', include('moderation.urls')),
    path('subscriptions/', include('subscriptions.urls', namespace='subscriptions')),
    
    # Subscription API endpoints
    path('api/subscriptions/plans/', views.SubscriptionPlanListView.as_view(), name='api_subscription_plans'),
    path('api/subscriptions/status/', views.subscription_status, name='api_subscription_status'),
    path('api/subscriptions/create/', views.create_subscription, name='api_subscription_create'),
    path('api/subscriptions/qr-payment/', views.process_qr_payment, name='api_subscription_qr_payment'),
    path('api/subscriptions/cancel/', views.cancel_subscription, name='api_subscription_cancel'),
    path('api/subscriptions/toggle-auto-renew/', views.toggle_auto_renew, name='api_subscription_toggle_auto_renew'),
    path('api/subscriptions/usage/', views.subscription_usage, name='api_subscription_usage'),
    path('api/subscriptions/check-ad-creation/', views.check_ad_creation, name='api_subscription_check_ad_creation'),
    path('api/subscriptions/', include('subscriptions.urls')),
    path('api/', include('subscriptions.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)