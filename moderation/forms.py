
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Report, ReportCategory

class ReportForm(forms.ModelForm):
    """Form for reporting content"""
    class Meta:
        model = Report
        fields = ['category', 'description']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Please describe the issue in detail...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = ReportCategory.objects.filter(is_active=True)
        self.fields['category'].empty_label = "Select a category"

class UserComplaintForm(forms.Form):
    """Form for users to submit general complaints"""
    COMPLAINT_TYPES = [
        ('billing', _('Billing Issue')),
        ('booking', _('Booking Problem')),
        ('host_behavior', _('Host Behavior')),
        ('guest_behavior', _('Guest Behavior')),
        ('property_issue', _('Property Issue')),
        ('platform_bug', _('Platform Bug')),
        ('safety_concern', _('Safety Concern')),
        ('other', _('Other')),
    ]
    
    PRIORITY_CHOICES = [
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('urgent', _('Urgent')),
    ]
    
    complaint_type = forms.ChoiceField(
        choices=COMPLAINT_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_("Complaint Type")
    )
    
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Brief description of the issue'
        }),
        label=_("Subject")
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Please provide detailed information about your complaint...'
        }),
        label=_("Description")
    )
    
    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        initial='medium',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_("Priority")
    )
    
    contact_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Alternative email for contact (optional)'
        }),
        label=_("Contact Email (optional)")
    )
    
    def clean_description(self):
        description = self.cleaned_data.get('description')
        if len(description) < 20:
            raise forms.ValidationError(_("Please provide more details (at least 20 characters)."))
        return description

class ComplaintResponseForm(forms.Form):
    """Form for moderators to respond to complaints"""
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('in_progress', _('In Progress')),
        ('resolved', _('Resolved')),
        ('rejected', _('Rejected')),
        ('escalated', _('Escalated')),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label=_("Status")
    )
    
    response = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Response to the complaint...'
        }),
        label=_("Response")
    )
    
    internal_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Internal notes (not visible to user)...'
        }),
        label=_("Internal Notes")
    )
