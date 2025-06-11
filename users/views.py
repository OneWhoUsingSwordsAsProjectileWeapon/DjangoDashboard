from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.urls import reverse
from django.conf import settings
import uuid
import json
from django.contrib.auth import logout

from .forms import UserRegisterForm, UserLoginForm, UserProfileForm
from .models import User
from notifications.tasks import send_email_notification

def register_view(request):
    """Handle user registration"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            
            # Set all new users as guests by default
            user.is_host = False
            user.is_guest = True
            
            # Save the user with default guest role
            user.save()
            
            # Send verification email
            token = uuid.uuid4().hex
            verification_url = request.build_absolute_uri(
                reverse('users:verify_email', kwargs={'token': token})
            )
            # In a real app, store token with user, here simplified
            send_email_notification(
                user.email,
                'Verify your email address',
                f'Please click the link to verify your email: {verification_url}'
            )
            
            login(request, user)
            messages.success(request, 'Your account has been created! A verification email has been sent.')
            return redirect('users:profile')
    else:
        form = UserRegisterForm()
    
    return render(request, 'users/register.html', {'form': form})

class CustomLoginView(LoginView):
    """Custom login view with custom form"""
    template_name = 'users/login.html'
    authentication_form = UserLoginForm
    redirect_authenticated_user = True

@login_required
def profile_view(request):
    """Display user profile"""
    # Get user bookings and listings
    return render(request, 'users/profile.html', {
        'user': request.user,
    })

@login_required
def edit_profile_view(request):
    """Edit user profile"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('users:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'users/edit_profile.html', {'form': form})

def verify_email(request, token):
    """Verify user's email with token"""
    # In real app, retrieve user by token from database
    # This is a simplified version
    if request.user.is_authenticated:
        user = request.user
        user.is_active = True
        user.save()
        messages.success(request, 'Your email has been verified!')
    else:
        messages.error(request, 'Verification link is invalid or expired.')
    
    return redirect('users:profile')

@login_required
def verify_phone(request):
    """Phone verification page"""
    return render(request, 'users/verification.html')

@login_required
def send_verification_code(request):
    """Send phone verification code"""
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        if phone_number:
            # In real app, generate and send SMS code
            # For demo, just mark as verified
            user = request.user
            user.phone_number = phone_number
            user.is_phone_verified = True
            user.save()
            messages.success(request, 'Your phone number has been verified!')
            return redirect('users:profile')
        else:
            messages.error(request, 'Please provide a valid phone number.')
    
    return redirect('users:verify_phone')

def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('listings:listing_list')
