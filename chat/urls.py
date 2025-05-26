from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.conversation_list, name='conversation_list'),
    path('<int:pk>/', views.conversation_detail, name='conversation_detail'),
    path('start/', views.start_conversation, name='start_conversation'),
    path('start/user/<int:user_id>/', views.start_conversation, name='start_conversation_with_user'),
    path('start/listing/<int:listing_id>/', views.start_conversation, name='start_conversation_about_listing'),
    path('start/booking/<int:booking_id>/', views.start_conversation, name='start_conversation_about_booking'),
    path('api/unread-count/', views.get_unread_count, name='get_unread_count'),
    
]
