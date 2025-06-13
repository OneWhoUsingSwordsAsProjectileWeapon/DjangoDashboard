from django.urls import path, include
from . import views

app_name = 'subscriptions'

urlpatterns = [
    # Main subscription page
    path('', views.subscription_plans_view, name='plan_list'),

    # User subscription management
    path('my-subscriptions/', views.UserSubscriptionListView.as_view(), name='user_subscriptions'),

    # Admin endpoints
    path('admin/', views.admin_dashboard, name='admin_dashboard'),

    # API endpoints
    path('api/subscriptions/plans/', views.SubscriptionPlanListView.as_view(), name='api_plans'),
    path('api/subscriptions/', views.UserSubscriptionListView.as_view(), name='api_subscriptions'),
    path('api/subscriptions/status/', views.subscription_status, name='api_status'),
    path('api/subscriptions/admin/stats/', views.subscription_stats, name='admin_stats'),
    path('api/subscriptions/admin/create/<int:user_id>/', views.admin_create_subscription, name='admin_create'),
    path('api/subscriptions/admin/extend/<int:subscription_id>/', views.admin_extend_subscription, name='admin_extend'),

    # Analytics endpoints (accessed via main URLs)
    # Analytics URLs are handled in core/urls.py to avoid namespace conflicts
]