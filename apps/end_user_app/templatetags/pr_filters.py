# bb_budget_monitoring_system/apps/end_user_app/templatetags/pr_filters.py
from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def filter_status(queryset, status):
    """Filter queryset by status"""
    return [item for item in queryset if item.status == status]

@register.filter
def get_quarter_remaining(line_item, quarter_and_amount):
    """Calculate remaining for a quarter after deducting amount"""
    try:
        quarter, amount = quarter_and_amount.split('|')
        quarter_amount = getattr(line_item, f'{quarter.lower()}_amount', Decimal('0'))
        consumed = line_item.get_quarter_consumed(quarter)
        return quarter_amount - consumed - Decimal(amount)
    except:
        return 0

@register.filter
def subtract(value, arg):
    """Subtract arg from value"""
    try:
        return Decimal(str(value)) - Decimal(str(arg))
    except:
        return 0
    
@register.filter
def get_quarter_remaining(line_item, quarter):
    """Get available amount for a specific quarter"""
    try:
        return line_item.get_quarter_available(quarter)
    except Exception as e:
        print(f"Error calculating quarter remaining: {e}")
        return Decimal('0')