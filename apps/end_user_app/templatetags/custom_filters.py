from django import template
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