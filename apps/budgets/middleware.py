# bb_budget_monitoring_system/apps/budgets/middleware.py
from django.shortcuts import redirect
from django.contrib import messages
from apps.budgets.models import (
    ApprovedBudget,
    BudgetAllocation,
    DepartmentPRE,
    PurchaseRequest,
    ActivityDesign,
)


class ArchivedRecordMiddleware:
    """
    Middleware to handle archived record access and prevent edits.

    - End users can view archived records (read-only)
    - End users cannot edit or submit forms for archived records
    - Admins can view and manage archived records
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process request
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Check if the request is trying to modify an archived record.
        """
        # Only check for authenticated users
        if not request.user.is_authenticated:
            return None

        # Skip for admins (they can manage archived records)
        if getattr(request.user, 'is_admin', False):
            return None

        # Only check POST requests (modifications)
        if request.method not in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return None

        # Check if the view is modifying archived records
        # This is a basic check - you can expand it based on your URL patterns
        if 'pre_id' in view_kwargs or 'pr_id' in view_kwargs or 'ad_id' in view_kwargs:
            record_id = view_kwargs.get('pre_id') or view_kwargs.get('pr_id') or view_kwargs.get('ad_id')

            # Determine model type
            if 'pre_id' in view_kwargs:
                model_class = DepartmentPRE
            elif 'pr_id' in view_kwargs:
                model_class = PurchaseRequest
            elif 'ad_id' in view_kwargs:
                model_class = ActivityDesign
            else:
                return None

            try:
                record = model_class.all_objects.get(id=record_id)
                if record.is_archived:
                    messages.error(
                        request,
                        'This record is archived and cannot be modified. Please contact your administrator if you need to restore it.'
                    )
                    return redirect(request.META.get('HTTP_REFERER', '/'))
            except model_class.DoesNotExist:
                pass

        return None
