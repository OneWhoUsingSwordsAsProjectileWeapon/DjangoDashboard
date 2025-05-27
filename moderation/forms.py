
from django import forms
from django.contrib.auth import get_user_model
from .models import UserComplaint
from listings.models import Listing, Booking

User = get_user_model()


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = UserComplaint
        fields = ['complaint_type', 'subject', 'description', 'target_user', 'target_listing', 'target_booking']
        widgets = {
            'complaint_type': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief summary of the issue'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Detailed description of the complaint'}),
            'target_user': forms.Select(attrs={'class': 'form-select'}),
            'target_listing': forms.Select(attrs={'class': 'form-select'}),
            'target_booking': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Make target fields not required - user will choose one
        self.fields['target_user'].required = False
        self.fields['target_listing'].required = False
        self.fields['target_booking'].required = False
        
        # Add empty option
        self.fields['target_user'].empty_label = "Select a user (optional)"
        self.fields['target_listing'].empty_label = "Select a listing (optional)"
        self.fields['target_booking'].empty_label = "Select a booking (optional)"
        
        if user:
            # Limit bookings to user's bookings
            self.fields['target_booking'].queryset = Booking.objects.filter(guest=user)
    
    def clean(self):
        cleaned_data = super().clean()
        target_user = cleaned_data.get('target_user')
        target_listing = cleaned_data.get('target_listing')
        target_booking = cleaned_data.get('target_booking')
        
        # At least one target must be specified
        if not any([target_user, target_listing, target_booking]):
            raise forms.ValidationError("Please specify what this complaint is about (user, listing, or booking).")
        
        return cleaned_data


class ComplaintResponseForm(forms.ModelForm):
    class Meta:
        model = UserComplaint
        fields = ['status', 'priority', 'assigned_moderator', 'moderator_notes', 'resolution_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'assigned_moderator': forms.Select(attrs={'class': 'form-select'}),
            'moderator_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'resolution_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_moderator'].queryset = User.objects.filter(role='moderator')
        self.fields['assigned_moderator'].empty_label = "Assign to moderator"
