from django import template
from django.utils.safestring import mark_safe
import json
from datetime import datetime, date

register = template.Library()

@register.filter
def currency(value):
    """Format a number as currency"""
    try:
        value = float(value)
        return f"{value:,.0f} ₽"
    except (ValueError, TypeError):
        return "0 ₽"

@register.filter
def star_rating(value):
    """Convert a numeric rating to star icons"""
    if value is None:
        return mark_safe('<span class="text-muted">Пока нет оценок</span>')

    try:
        rating = float(value)
        full_stars = int(rating)
        half_star = rating - full_stars >= 0.5
        empty_stars = 5 - full_stars - (1 if half_star else 0)

        stars_html = ''
        # Full stars
        for _ in range(full_stars):
            stars_html += '<i class="fas fa-star text-warning"></i>'

        # Half star
        if half_star:
            stars_html += '<i class="fas fa-star-half-alt text-warning"></i>'

        # Empty stars
        for _ in range(empty_stars):
            stars_html += '<i class="far fa-star text-warning"></i>'

        return mark_safe(stars_html)
    except (ValueError, TypeError):
        return mark_safe('<span class="text-muted">Некорректная оценка</span>')

@register.filter
def date_range(start_date, end_date):
    """Format a date range"""
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    nights = (end_date - start_date).days

    return f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')} · {nights} night{'s' if nights != 1 else ''}"

@register.filter
def jsonify(obj):
    """Convert an object to JSON string"""
    if isinstance(obj, date):
        return json.dumps(obj.isoformat())
    return json.dumps(obj)

@register.filter
def get_listing_status_badge(listing):
    """Return a Bootstrap badge class based on listing status"""
    if not listing.is_active:
        return mark_safe('<span class="badge bg-secondary">Неактивно</span>')
    elif not listing.is_approved:
        return mark_safe('<span class="badge bg-warning text-dark">Ожидает одобрения</span>')
    else:
        return mark_safe('<span class="badge bg-success">Активно</span>')

@register.filter
def get_booking_status_badge(status):
    """Return a Bootstrap badge class based on booking status"""
    status_translations = {
        'pending': 'Ожидает',
        'confirmed': 'Подтверждено',
        'canceled': 'Отменено',
        'completed': 'Завершено'
    }

    badge_classes = {
        'pending': 'bg-warning text-dark',
        'confirmed': 'bg-success',
        'canceled': 'bg-danger',
        'completed': 'bg-info'
    }

    badge_class = badge_classes.get(status, 'bg-secondary')
    status_text = status_translations.get(status, status.title())
    return mark_safe(f'<span class="badge {badge_class}">{status_text}</span>')

@register.filter
def amenity_icon(amenity):
    """Return appropriate icon for amenity"""
    icons = {
        'wifi': 'fas fa-wifi',
        'kitchen': 'fas fa-utensils',
        'washer': 'fas fa-tshirt',
        'dryer': 'fas fa-wind',
        'air_conditioning': 'fas fa-snowflake',
        'heating': 'fas fa-fire',
        'tv': 'fas fa-tv',
        'iron': 'fas fa-iron',
        'hairdryer': 'fas fa-hairdryer',
        'pool': 'fas fa-swimming-pool',
        'free_parking': 'fas fa-parking',
        'crib': 'fas fa-baby',
        'workspace': 'fas fa-desk',
        'hot_tub': 'fas fa-hot-tub',
        'bbq': 'fas fa-drumstick-bite',
        'indoor_fireplace': 'fas fa-fireplace',
        'gym': 'fas fa-dumbbell',
        'breakfast': 'fas fa-coffee',
        'smoking_allowed': 'fas fa-smoking',
        'pets_allowed': 'fas fa-paw',
        'wheelchair_accessible': 'fas fa-wheelchair',
    }

    icon_class = icons.get(amenity.lower().replace(' ', '_'), 'fas fa-check')
    return mark_safe(f'<i class="{icon_class}"></i>')

@register.simple_tag
def display_amenities(amenities, max_display=6):
    """Display amenities with icons"""
    if not amenities:
        return mark_safe('<p>Удобства не указаны</p>')

    html = '<div class="row">'

    # Show only first few amenities
    for i, amenity in enumerate(amenities[:max_display]):
        html += f'''
        <div class="col-md-6 mb-2">
            <div class="d-flex align-items-center">
                <span class="me-2">{amenity_icon(amenity)}</span>
                <span>{amenity}</span>
            </div>
        </div>
        '''

    # Add a "more" button if there are additional amenities
    if len(amenities) > max_display:
        html += f'''
        <div class="col-12 mt-2">
            <button class="btn btn-sm btn-outline-primary" 
                    data-bs-toggle="modal" 
                    data-bs-target="#amenitiesModal">
                Показать все {len(amenities)} удобств
            </button>
        </div>
        '''

    html += '</div>'
    return mark_safe(html)

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary or queryset by key"""
    try:
        if hasattr(dictionary, 'filter'):
            # It's a QuerySet or Manager
            return dictionary.filter(listing_id=key).exists()
        elif hasattr(dictionary, 'get'):
            # It's a dictionary-like object
            return dictionary.get(key)
        else:
            # Try to access it like a list/tuple
            return dictionary[key]
    except (KeyError, IndexError, TypeError, AttributeError):
        return None

@register.filter
def star_rating(rating):
    """Convert numeric rating to star display"""
    if not rating:
        return ""

    full_stars = int(rating)
    half_star = 1 if rating - full_stars >= 0.5 else 0
    empty_stars = 5 - full_stars - half_star

    stars = "★" * full_stars + "☆" * half_star + "☆" * empty_stars
    return mark_safe(stars)

@register.filter
def currency(value):
    """Format currency value"""
    try:
        return f"{int(float(value)):,}".replace(",", " ")
    except (ValueError, TypeError):
        return value