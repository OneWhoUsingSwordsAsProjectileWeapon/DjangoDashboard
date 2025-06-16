from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    path('terms/', views.terms_agreement_view, name='terms_agreement'),
    path('register/', views.register_view, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Profile routes
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    # Public profile route
    path('profile/<int:user_id>/', views.public_profile_view, name='public_profile'),

    # Verification
    path('verify/email/<str:token>/', views.verify_email, name='verify_email'),
    path('verify/phone/', views.verify_phone, name='verify_phone'),
    path('verify/send-code/', views.send_verification_code, name='send_verification_code'),

    # Password reset
    path('password-reset/', views.password_reset_view, name='password_reset'),
    path('password-reset/done/', 
        auth_views.PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'), 
        name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
        auth_views.PasswordResetConfirmView.as_view(template_name='users/password_reset_confirm.html'), 
        name='password_reset_confirm'),
    path('password-reset-complete/', 
        auth_views.PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'), 
        name='password_reset_complete'),
]