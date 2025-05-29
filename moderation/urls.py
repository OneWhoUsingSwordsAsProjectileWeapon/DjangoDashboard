from django.urls import path
from . import views

app_name = 'moderation'

urlpatterns = [
    path('report/<str:content_type>/<int:content_id>/', views.report_content, name='report_content'),
    path('reports/', views.report_list, name='report_list'),
    path('reports/<int:pk>/', views.report_detail, name='report_detail'),
    path('dashboard/', views.moderation_dashboard, name='dashboard'),
    path('approvals/', views.listing_approval_list, name='listing_approval_list'),
    path('approvals/<int:pk>/', views.listing_approval_detail, name='listing_approval_detail'),
    path('logs/', views.moderation_logs, name='logs'),
    path('api/filter-content/', views.filter_content, name='filter_content'),

    # User complaints
    path('complaints/file/', views.file_complaint, name='file_complaint'),
    path('complaints/my/', views.my_complaints, name='my_complaints'),
    path('complaints/', views.complaint_list, name='complaint_list'),
    path('complaints/<int:pk>/', views.complaint_detail, name='complaint_detail'),
    path('complaint/<int:listing_id>/', views.file_complaint, name='file_complaint'),
    path('complaint/booking/<int:booking_id>/', views.file_booking_complaint, name='file_booking_complaint'),
]