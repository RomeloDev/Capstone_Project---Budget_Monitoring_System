import os
from django import template
from django.conf import settings

register = template.Library()

@register.filter(name='file_exists')
def file_exists(file_field):
    """
    Check if a file exists on the filesystem.
    Usage: {% if document|file_exists %}
    """
    if not file_field:
        return False

    try:
        # Get the full path to the file
        file_path = file_field.path
        # Check if the file exists
        return os.path.exists(file_path)
    except (ValueError, AttributeError):
        # ValueError: The file doesn't have a path
        # AttributeError: file_field doesn't have a path attribute
        return False
