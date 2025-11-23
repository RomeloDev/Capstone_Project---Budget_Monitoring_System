from django import template
from decimal import Decimal
import os

register = template.Library()

@register.filter
def basename(value):
    """
    Returns the filename from a file path
    Example: '/path/to/document.pdf' -> 'document.pdf'
    """
    if not value:
        return ''
    return os.path.basename(str(value))


@register.filter(name='calculate_percentage')
def calculate_percentage(value, total):
    """
    Calculate percentage with decimal precision.
    Usage: {{ numerator|calculate_percentage:denominator }}
    Returns: Float percentage (e.g., 3.7 for 3.7%)
    """
    try:
        value = Decimal(str(value))
        total = Decimal(str(total))

        if total == 0:
            return 0

        percentage = (value / total) * 100
        return float(percentage)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0