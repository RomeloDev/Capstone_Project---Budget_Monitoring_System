# bb_budget_monitoring_system/apps/admin_panel/templatetags/pagination_tags.py
from django import template

register = template.Library()

@register.simple_tag
def get_page_range(page_obj, max_pages=7):
    """
    Returns a smart page range for pagination
    """
    current_page = page_obj.number
    total_pages = page_obj.paginator.num_pages
    
    if total_pages <= max_pages:
        return list(range(1, total_pages + 1))
    
    # Calculate the range
    half_range = max_pages // 2
    
    if current_page <= half_range:
        # Show first pages
        return list(range(1, max_pages + 1))
    elif current_page >= total_pages - half_range:
        # Show last pages
        return list(range(total_pages - max_pages + 1, total_pages + 1))
    else:
        # Show middle pages
        return list(range(current_page - half_range, current_page + half_range + 1))

@register.simple_tag
def should_show_first_ellipsis(page_obj, page_range):
    """Check if we should show ellipsis before the page range"""
    return page_range[0] > 1

@register.simple_tag
def should_show_last_ellipsis(page_obj, page_range):
    """Check if we should show ellipsis after the page range"""
    return page_range[-1] < page_obj.paginator.num_pages