
from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    # Web views
    path('', views.subscription_plans_view, name='plan_list'),
    
    # API endpoints
    path('api/plans/', views.SubscriptionPlanListView.as_view(), name='api_plan_list'),
    
    # User endpoints
    path('my-subscriptions/', views.UserSubscriptionListView.as_view(), name='user_subscriptions'),
    path('status/', views.subscription_status, name='status'),
    path('usage/', views.subscription_usage, name='usage'),
    path('create/', views.create_subscription, name='create'),
    path('toggle-auto-renew/', views.toggle_auto_renew, name='toggle_auto_renew'),
    path('cancel/', views.cancel_subscription, name='cancel'),
    path('check-ad-creation/', views.check_ad_creation, name='check_ad_creation'),
    
    # Admin endpoints
    path('admin/stats/', views.subscription_stats, name='admin_stats'),
    path('admin/create/<int:user_id>/', views.admin_create_subscription, name='admin_create'),
    path('admin/extend/<int:subscription_id>/', views.admin_extend_subscription, name='admin_extend'),
]
