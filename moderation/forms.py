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

class BookingComplaintForm(forms.Form):
    """Form for users to submit complaints about bookings"""
    COMPLAINT_TYPES = [
        ('booking_issue', 'Проблема с бронированием'),
        ('listing_issue', 'Проблема с объявлением'),
        ('host_behavior', 'Поведение хоста'),
        ('guest_behavior', 'Поведение гостя'),
        ('safety_concern', 'Вопросы безопасности'),
        ('false_listing', 'Ложная информация в объявлении'),
        ('discrimination', 'Дискриминация'),
        ('payment_issue', 'Проблемы с оплатой'),
        ('cleanliness', 'Чистота'),
        ('other', 'Другое'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('urgent', 'Срочный - требуется немедленное вмешательство'),
    ]

    complaint_type = forms.ChoiceField(
        choices=COMPLAINT_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Тип жалобы"
    )

    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Краткое описание проблемы'
        }),
        label="Тема жалобы",
        required=False
    )

    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Опишите проблему как можно подробнее...'
        }),
        label="Описание жалобы"
    )

    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        initial='medium',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Приоритет"
    )

    contact_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Альтернативный email для связи (необязательно)'
        }),
        label="Контактный email"
    )

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if len(description) < 20:
            raise forms.ValidationError("Пожалуйста, опишите проблему более подробно (минимум 20 символов).")
        return description

class ListingComplaintForm(forms.Form):
    """Form for users to submit complaints about listings"""
    COMPLAINT_TYPES = [
        ('listing_issue', 'Проблема с объявлением'),
        ('false_listing', 'Ложная информация в объявлении'),
        ('host_behavior', 'Поведение хоста'),
        ('safety_concern', 'Вопросы безопасности'),
        ('discrimination', 'Дискриминация'),
        ('inappropriate_content', 'Неподходящий контент'),
        ('pricing_issue', 'Проблемы с ценообразованием'),
        ('other', 'Другое'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('urgent', 'Срочный - требуется немедленное вмешательство'),
    ]

    complaint_type = forms.ChoiceField(
        choices=COMPLAINT_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Тип жалобы"
    )

    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Краткое описание проблемы'
        }),
        label="Тема жалобы",
        required=False
    )

    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Опишите проблему как можно подробнее...'
        }),
        label="Описание жалобы"
    )

    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        initial='medium',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Приоритет"
    )

    contact_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Альтернативный email для связи (необязательно)'
        }),
        label="Контактный email"
    )

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if len(description) < 20:
            raise forms.ValidationError("Пожалуйста, опишите проблему более подробно (минимум 20 символов).")
        return description

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
        ('pending', 'В ожидании'),
        ('in_progress', 'В обработке'),
        ('investigating', 'Расследуется'),
        ('awaiting_response', 'Ожидает ответа'),
        ('resolved', 'Решено'),
        ('dismissed', 'Отклонено'),
        ('escalated', 'Эскалировано'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('urgent', 'Срочный'),
    ]

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Статус"
    )

    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Приоритет",
        required=False
    )

    response = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Ответ пользователю...'
        }),
        label="Ответ пользователю",
        help_text="Этот ответ увидит пользователь, подавший жалобу"
    )

    internal_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Внутренние заметки (не видны пользователю)...'
        }),
        label="Внутренние заметки"
    )

    # Action options
    action_type = forms.ChoiceField(
        choices=[
            ('', 'Без дополнительных действий'),
            ('warn_user', 'Предупредить пользователя'),
            ('temporary_ban', 'Временная блокировка'),
            ('permanent_ban', 'Постоянная блокировка'),
            ('deactivate_listing', 'Деактивировать объявление'),
            ('cancel_booking', 'Отменить бронирование'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Дополнительные действия"
    )

    ban_duration_days = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=365,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Количество дней'
        }),
        label="Длительность блокировки (дни)"
    )

    action_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Причина действия...'
        }),
        label="Причина действия"
    )