from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    # Main subscription page
    path('', views.subscription_plans_view, name='plan_list'),
    
    # User subscription management
    path('my-subscriptions/', views.UserSubscriptionListView.as_view(), name='user_subscriptions'),

    # Admin endpoints
    path('admin/stats/', views.subscription_stats, name='admin_stats'),
    path('admin/create/<int:user_id>/', views.admin_create_subscription, name='admin_create'),
    path('admin/extend/<int:subscription_id>/', views.admin_extend_subscription, name='admin_extend'),
]