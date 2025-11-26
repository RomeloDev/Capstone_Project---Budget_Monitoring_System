# bb_budget_monitoring_system/apps/budgets/managers.py
from django.db import models
from django.db.models import Q


class ArchiveManager(models.Manager):
    """
    Custom manager that excludes archived records by default.

    Usage:
        - Model.objects.all()  # Returns only non-archived records
        - Model.objects.archived()  # Returns only archived records
        - Model.objects.with_archived()  # Returns all records (including archived)
    """

    def get_queryset(self):
        """Override to exclude archived records by default"""
        return super().get_queryset().filter(is_archived=False)

    def archived(self):
        """Return only archived records"""
        return super().get_queryset().filter(is_archived=True)

    def with_archived(self):
        """Return all records including archived ones"""
        return super().get_queryset()

    def fiscal_year_archived(self, fiscal_year):
        """
        Return archived records for a specific fiscal year.

        This method intelligently determines which filter to apply based on
        the model's fields to avoid FieldError exceptions.
        """
        queryset = self.archived()
        model = self.model

        # Check which fields exist on this model and use the appropriate filter
        if hasattr(model, 'fiscal_year'):
            # For ApprovedBudget model
            return queryset.filter(fiscal_year=fiscal_year)
        elif hasattr(model, 'approved_budget'):
            # For BudgetAllocation model
            return queryset.filter(approved_budget__fiscal_year=fiscal_year)
        elif hasattr(model, 'budget_allocation'):
            # For DepartmentPRE, PurchaseRequest, ActivityDesign models
            return queryset.filter(budget_allocation__approved_budget__fiscal_year=fiscal_year)
        else:
            # Fallback: return empty queryset if model structure is unexpected
            return queryset.none()
