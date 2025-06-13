
from django import template

register = template.Library()

@register.filter
def underscore_to_space(value):
    """Convert underscore_separated_string to space separated string"""
    if not value:
        return value
    
    # Replace underscores with spaces and capitalize words
    return value.replace('_', ' ').replace('-', ' ').title()

@register.filter
def format_features(features):
    """Format premium features list for display"""
    if not features:
        return []
    
    feature_names = {
        'basic_support': 'Базовая поддержка',
        'priority_support': 'Приоритетная поддержка',
        '24_7_support': 'Поддержка 24/7',
        'dedicated_support': 'Персональная поддержка',
        'standard_analytics': 'Стандартная аналитика',
        'advanced_analytics': 'Расширенная аналитика',
        'detailed_analytics': 'Детальная аналитика',
        'custom_analytics': 'Персональная аналитика',
        'featured_placement': 'Размещение в рекомендуемых',
        'priority_placement': 'Приоритетное размещение',
        'bulk_operations': 'Массовые операции',
        'api_access': 'Доступ к API',
        'white_label': 'Белый лейбл'
    }
    
    return [feature_names.get(feature, feature.replace('_', ' ').title()) for feature in features]
