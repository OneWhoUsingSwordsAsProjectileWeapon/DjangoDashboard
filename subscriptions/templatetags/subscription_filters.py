
from django import template

register = template.Library()

@register.filter
def replace(value, arg):
    """
    Replace all occurrences of arg[0] with arg[1] in value
    Usage: {{ value|replace:"_| " }}
    """
    if not arg or '|' not in arg:
        return value
    
    old, new = arg.split('|', 1)
    return str(value).replace(old, new)

@register.filter  
def underscore_to_space(value):
    """
    Replace underscores with spaces and title case
    Usage: {{ value|underscore_to_space }}
    """
    return str(value).replace('_', ' ').title()
