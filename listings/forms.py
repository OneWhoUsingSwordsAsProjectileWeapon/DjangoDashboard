from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Listing, Booking, Review, ListingImage
#23s
class ListingForm(forms.ModelForm):
    """Form for creating and editing listings"""
    class Meta:
        model = Listing
        fields = [
            'title', 'description', 'address', 'city', 'state', 'country', 
            'zip_code', 'latitude', 'longitude',
            'price_per_night', 'cleaning_fee', 'service_fee',
            'bedrooms', 'bathrooms', 'accommodates', 'property_type',
            'amenities', 'house_rules', 'check_in_time', 'check_out_time',
            'minimum_nights', 'maximum_nights', 'verification_video'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'house_rules': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'check_in_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'check_out_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'amenities': forms.HiddenInput(),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'verification_video': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'video/*',
                'data-max-size': '262144000',  # 250MB in bytes
                'help_text': _("Please provide a continuous video from the street address to entering the apartment, showcasing all mentioned amenities and rooms.")
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add bootstrap classes
        for field_name, field in self.fields.items():
            if field_name not in ['amenities'] and 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

    def clean_amenities(self):
        """Convert amenities string to list if needed"""
        amenities = self.cleaned_data.get('amenities')
        if isinstance(amenities, str):
            try:
                import json
                return json.loads(amenities)
            except json.JSONDecodeError:
                return []
        return amenities or []

    def clean_image_urls(self):
        """Convert image_urls string to list if needed"""
        image_urls = self.cleaned_data.get('image_urls')
        if isinstance(image_urls, str):
            try:
                import json
                return json.loads(image_urls)
            except json.JSONDecodeError:
                return []
        return image_urls or []

    def clean_verification_video(self):
        """Validate verification video file"""
        video = self.cleaned_data.get('verification_video')
        
        # Make video mandatory
        if not video:
            raise forms.ValidationError(
                _("Видео подтверждения является обязательным для отправки объявления на модерацию.")
            )
        
        # Check file size (250MB max)
        max_size = 250 * 1024 * 1024  # 250MB in bytes
        if video.size > max_size:
            raise forms.ValidationError(
                _("Video file size cannot exceed 250MB. Current size: %(size).1fMB"),
                params={'size': video.size / (1024 * 1024)}
            )

        # Check file extension
        allowed_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv']
        file_extension = video.name.lower().split('.')[-1]
        if f'.{file_extension}' not in allowed_extensions:
            raise forms.ValidationError(
                _("Invalid video format. Allowed formats: %(formats)s"),
                params={'formats': ', '.join(allowed_extensions)}
            )

        return video

class ListingImageForm(forms.ModelForm):
    """Form for managing listing images"""
    class Meta:
        model = ListingImage
        fields = ['image', 'is_main']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_main': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

class BookingForm(forms.ModelForm):
    """Form for creating bookings"""
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label=_("Check-in date")
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label=_("Check-out date")
    )

    class Meta:
        model = Booking
        fields = ['start_date', 'end_date', 'guests', 'special_requests']
        widgets = {
            'guests': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'special_requests': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, listing=None, *args, **kwargs):
        self.listing = listing
        super().__init__(*args, **kwargs)

        if listing:
            self.fields['guests'].widget.attrs['max'] = listing.accommodates

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        guests = cleaned_data.get('guests')

        if start_date and end_date:
            # Check if end date is after start date
            if end_date <= start_date:
                raise forms.ValidationError(_("Check-out date must be after check-in date"))

            # Check minimum and maximum nights
            duration = (end_date - start_date).days
            if self.listing:
                if duration < self.listing.minimum_nights:
                    raise forms.ValidationError(
                        _("Minimum stay is %(min_nights)s nights"),
                        params={'min_nights': self.listing.minimum_nights}
                    )
                if duration > self.listing.maximum_nights:
                    raise forms.ValidationError(
                        _("Maximum stay is %(max_nights)s nights"),
                        params={'max_nights': self.listing.maximum_nights}
                    )

                # Check if listing is available for these dates
                if not self.listing.is_available(start_date, end_date):
                    raise forms.ValidationError(_("The property is not available for the selected dates"))

        # Check if guests count is valid
        if guests and self.listing and guests > self.listing.accommodates:
            raise forms.ValidationError(
                _("Maximum guests allowed is %(max_guests)s"),
                params={'max_guests': self.listing.accommodates}
            )

        return cleaned_data

class ReviewForm(forms.ModelForm):
    """Form for submitting reviews"""
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 5,
                'step': 1
            }),
            'comment': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class ListingSearchForm(forms.Form):
    """Form for searching listings"""
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Where are you going?'})
    )
    check_in = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    check_out = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    guests = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1})
    )
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min price'})
    )
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max price'})
    )
    property_type = forms.ChoiceField(
        required=False,
        choices=[('', 'Any')] + [
            ('apartment', 'Apartment'),
            ('house', 'House'),
            ('villa', 'Villa'),
            ('cabin', 'Cabin'),
            ('condo', 'Condominium'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    bedrooms = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0})
    )
    bathrooms = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': 0.5})
    )