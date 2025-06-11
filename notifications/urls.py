from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='notification_list'),
    path('<int:pk>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('get-unread-count/', views.get_unread_count, name='get_unread_count'),
    path('api/unread-count/', views.get_unread_count_json, name='get_unread_count_json'),
    path('api/recent/', views.recent_notifications, name='recent_notifications'),
]
