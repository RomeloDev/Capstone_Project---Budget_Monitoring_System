# bb_budget_monitoring_system/apps/budgets/context_processors.py
from apps.budgets.models import ApprovedBudget


def archive_context(request):
    """
    Add archive-related context variables to all templates.
    """
    # Get available fiscal years (active only for end users, all for admins)
    if request.user.is_authenticated:
        is_admin = getattr(request.user, 'is_admin', False)

        if is_admin:
            # Admins can see all years (active and archived)
            all_fiscal_years = ApprovedBudget.all_objects.values_list('fiscal_year', flat=True).distinct().order_by('-fiscal_year')
        else:
            # End users see only active years
            all_fiscal_years = ApprovedBudget.objects.values_list('fiscal_year', flat=True).distinct().order_by('-fiscal_year')

        return {
            'available_fiscal_years': list(all_fiscal_years),
            'user_can_view_archived': is_admin,
        }

    return {
        'available_fiscal_years': [],
        'user_can_view_archived': False,
    }
