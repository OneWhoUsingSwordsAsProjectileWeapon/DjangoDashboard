from django.urls import path
from . import views

app_name = 'moderation'

urlpatterns = [
    path('dashboard/', views.moderation_dashboard, name='dashboard'),
    path('reports/', views.report_list, name='reports'),
    path('reports/<int:report_id>/', views.report_detail, name='report_detail'),
    path('approvals/', views.listing_approval_list, name='approvals'),
    path('approvals/<int:approval_id>/', views.listing_approval_detail, name='approval_detail'),
    path('complaints/', views.complaint_list, name='complaints'),
    path('complaints/<int:complaint_id>/', views.complaint_detail, name='complaint_detail'),
    path('file-complaint/', views.file_complaint, name='file_complaint'),
    path('my-complaints/', views.my_complaints, name='my_complaints'),
    path('logs/', views.moderation_logs, name='logs'),
]