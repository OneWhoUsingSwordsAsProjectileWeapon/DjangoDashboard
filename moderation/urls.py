from django.urls import path
from . import views

app_name = 'moderation'

urlpatterns = [
    path('report/<str:content_type>/<int:content_id>/', views.report_content, name='report_content'),
    path('reports/', views.report_list, name='report_list'),
    path('reports/<int:pk>/', views.report_detail, name='report_detail'),
    path('dashboard/', views.moderation_dashboard, name='dashboard'),
    path('api/filter-content/', views.filter_content, name='filter_content'),
]
