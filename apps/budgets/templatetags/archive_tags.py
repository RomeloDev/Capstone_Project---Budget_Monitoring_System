# bb_budget_monitoring_system/apps/budgets/templatetags/archive_tags.py
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def archive_badge(record, show_icon=True):
    """
    Display an archive badge if the record is archived.

    Usage:
        {% load archive_tags %}
        {% archive_badge pre_record %}
        {% archive_badge pre_record show_icon=False %}
    """
    if not hasattr(record, 'is_archived') or not record.is_archived:
        return ''

    icon_html = ''
    if show_icon:
        icon_html = '''
        <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"></path>
        </svg>
        '''

    badge_html = f'''
    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 border border-purple-200">
        {icon_html}
        ARCHIVED
    </span>
    '''

    return mark_safe(badge_html)


@register.simple_tag
def archive_status_badge(record):
    """
    Display a status badge (Active or Archived).

    Usage:
        {% load archive_tags %}
        {% archive_status_badge budget_allocation %}
    """
    if not hasattr(record, 'is_archived'):
        return ''

    if record.is_archived:
        badge_html = '''
        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
            <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"></path>
            </svg>
            Archived
        </span>
        '''
    else:
        badge_html = '''
        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            Active
        </span>
        '''

    return mark_safe(badge_html)


@register.simple_tag
def archive_banner(record, user=None):
    """
    Display a prominent banner at the top of a page for archived records.
    Includes archive date and reason.

    Usage:
        {% load archive_tags %}
        {% archive_banner pre_record user %}
    """
    if not hasattr(record, 'is_archived') or not record.is_archived:
        return ''

    # Determine user type for messaging
    is_admin = user and (hasattr(user, 'is_admin') and user.is_admin)

    if is_admin:
        message = "This record is archived. You can view and restore it from the Archive Center."
    else:
        message = "This record is archived and is read-only. You cannot edit or submit new documents for archived records."

    archived_date = ''
    if hasattr(record, 'archived_at') and record.archived_at:
        archived_date = f'<div class="text-sm">Archived on: {record.archived_at.strftime("%B %d, %Y at %I:%M %p")}</div>'

    archived_by = ''
    if hasattr(record, 'archived_by') and record.archived_by:
        archived_by = f'<div class="text-sm">Archived by: {record.archived_by.get_full_name()}</div>'

    archive_reason = ''
    if hasattr(record, 'archive_reason') and record.archive_reason:
        archive_reason = f'<div class="text-sm mt-2"><strong>Reason:</strong> {record.archive_reason}</div>'

    banner_html = f'''
    <div class="bg-purple-50 border-l-4 border-purple-500 p-4 mb-6 rounded-lg shadow-sm">
        <div class="flex">
            <div class="flex-shrink-0">
                <svg class="h-6 w-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"></path>
                </svg>
            </div>
            <div class="ml-3 flex-1">
                <h3 class="text-sm font-medium text-purple-800">Archived Record - Read Only</h3>
                <div class="mt-2 text-sm text-purple-700">
                    <p>{message}</p>
                    {archived_date}
                    {archived_by}
                    {archive_reason}
                </div>
            </div>
        </div>
    </div>
    '''

    return mark_safe(banner_html)


@register.filter
def is_archived(record):
    """
    Check if a record is archived.

    Usage:
        {% load archive_tags %}
        {% if record|is_archived %}
            <!-- Show read-only view -->
        {% endif %}
    """
    return hasattr(record, 'is_archived') and record.is_archived


@register.simple_tag
def disable_if_archived(record, classes=''):
    """
    Returns disabled attribute and CSS classes if record is archived.

    Usage:
        {% load archive_tags %}
        <button {% disable_if_archived pre_record %}>Submit</button>
        <input type="text" {% disable_if_archived allocation "opacity-50 cursor-not-allowed" %}>
    """
    if hasattr(record, 'is_archived') and record.is_archived:
        disabled_classes = f'disabled opacity-50 cursor-not-allowed pointer-events-none {classes}'
        return mark_safe(f'disabled class="{disabled_classes.strip()}"')
    return mark_safe(f'class="{classes}"' if classes else '')
