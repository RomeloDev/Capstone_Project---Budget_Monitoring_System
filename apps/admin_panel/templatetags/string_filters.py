from django import template

register = template.Library()

@register.filter
def mask_id(value, show_chars=5):
    """
    Masks the middle of a string, showing first and last N characters.
    Usage: {{ value|mask_id:5 }}
    """
    if not value:
        return value
    
    value = str(value)
    if len(value) <= show_chars * 2:
        return value  # Don't mask if too short
    
    first_part = value[:show_chars]
    last_part = value[-show_chars:]
    return f"{first_part}...{last_part}"