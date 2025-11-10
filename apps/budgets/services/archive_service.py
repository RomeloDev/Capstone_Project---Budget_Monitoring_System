# bb_budget_monitoring_system/apps/budgets/services/archive_service.py
from django.db import transaction
from django.utils import timezone
from apps.budgets.models import (
    ApprovedBudget,
    BudgetAllocation,
    DepartmentPRE,
    PurchaseRequest,
    ActivityDesign,
)
from apps.users.models import User
from apps.admin_panel.models import AuditTrail
from typing import Dict, Optional, List


def archive_fiscal_year(
    fiscal_year: str,
    archived_by: Optional[User] = None,
    reason: str = "",
    archive_type: str = "FISCAL_YEAR"
) -> Dict[str, int]:
    """
    Archive an entire fiscal year with cascading to all related records.

    Args:
        fiscal_year: The fiscal year to archive (e.g., "2023")
        archived_by: User performing the archive (None for system/automatic)
        reason: Reason for archiving
        archive_type: Type of archive ('FISCAL_YEAR' or 'MANUAL')

    Returns:
        Dictionary with counts of archived records

    Raises:
        ApprovedBudget.DoesNotExist: If fiscal year not found
        Exception: If any error occurs during archiving
    """
    archived_counts = {
        'approved_budgets': 0,
        'budget_allocations': 0,
        'department_pres': 0,
        'purchase_requests': 0,
        'activity_designs': 0,
    }

    try:
        with transaction.atomic():
            # Get the approved budget for this fiscal year
            try:
                budget = ApprovedBudget.all_objects.get(
                    fiscal_year=fiscal_year,
                    is_archived=False
                )
            except ApprovedBudget.DoesNotExist:
                raise ValueError(f"No active budget found for fiscal year {fiscal_year}")

            # Archive the approved budget
            budget.is_archived = True
            budget.archived_at = timezone.now()
            budget.archived_by = archived_by
            budget.archive_reason = reason or f"Fiscal year {fiscal_year} archived"
            budget.archive_type = archive_type
            budget.save()
            archived_counts['approved_budgets'] = 1

            # Get all related budget allocations
            allocations = BudgetAllocation.all_objects.filter(
                approved_budget=budget,
                is_archived=False
            )

            # Archive each allocation and its related documents
            for allocation in allocations:
                # Archive the allocation
                allocation.is_archived = True
                allocation.archived_at = timezone.now()
                allocation.archived_by = archived_by
                allocation.archive_reason = f"Cascaded from fiscal year {fiscal_year}"
                allocation.archive_type = archive_type
                allocation.save()
                archived_counts['budget_allocations'] += 1

                # Archive all DepartmentPREs for this allocation
                pres = DepartmentPRE.all_objects.filter(
                    budget_allocation=allocation,
                    is_archived=False
                )
                for pre in pres:
                    pre.is_archived = True
                    pre.archived_at = timezone.now()
                    pre.archived_by = archived_by
                    pre.archive_reason = f"Cascaded from fiscal year {fiscal_year}"
                    pre.archive_type = archive_type
                    pre.save()
                    archived_counts['department_pres'] += 1

                # Archive all PurchaseRequests for this allocation
                prs = PurchaseRequest.all_objects.filter(
                    budget_allocation=allocation,
                    is_archived=False
                )
                for pr in prs:
                    pr.is_archived = True
                    pr.archived_at = timezone.now()
                    pr.archived_by = archived_by
                    pr.archive_reason = f"Cascaded from fiscal year {fiscal_year}"
                    pr.archive_type = archive_type
                    pr.save()
                    archived_counts['purchase_requests'] += 1

                # Archive all ActivityDesigns for this allocation
                ads = ActivityDesign.all_objects.filter(
                    budget_allocation=allocation,
                    is_archived=False
                )
                for ad in ads:
                    ad.is_archived = True
                    ad.archived_at = timezone.now()
                    ad.archived_by = archived_by
                    ad.archive_reason = f"Cascaded from fiscal year {fiscal_year}"
                    ad.archive_type = archive_type
                    ad.save()
                    archived_counts['activity_designs'] += 1

            # Log to AuditTrail
            if archived_by:
                AuditTrail.objects.create(
                    user=archived_by,
                    action='ARCHIVE',
                    model_name='ApprovedBudget',
                    record_id=str(budget.id),
                    detail=f"Archived fiscal year {fiscal_year}. " +
                           f"Budgets: {archived_counts['approved_budgets']}, " +
                           f"Allocations: {archived_counts['budget_allocations']}, " +
                           f"PREs: {archived_counts['department_pres']}, " +
                           f"PRs: {archived_counts['purchase_requests']}, " +
                           f"ADs: {archived_counts['activity_designs']}. " +
                           f"Reason: {reason}"
                )

            return archived_counts

    except Exception as e:
        # Re-raise the exception to trigger transaction rollback
        raise Exception(f"Error archiving fiscal year {fiscal_year}: {str(e)}")


def unarchive_fiscal_year(
    fiscal_year: str,
    unarchived_by: User,
    reason: str = ""
) -> Dict[str, int]:
    """
    Unarchive (restore) an entire fiscal year with cascading to all related records.

    Args:
        fiscal_year: The fiscal year to unarchive (e.g., "2023")
        unarchived_by: User performing the unarchive
        reason: Reason for unarchiving (required)

    Returns:
        Dictionary with counts of unarchived records

    Raises:
        ApprovedBudget.DoesNotExist: If fiscal year not found
        ValueError: If reason is not provided
        Exception: If any error occurs during unarchiving
    """
    if not reason or not reason.strip():
        raise ValueError("Unarchive reason is required")

    unarchived_counts = {
        'approved_budgets': 0,
        'budget_allocations': 0,
        'department_pres': 0,
        'purchase_requests': 0,
        'activity_designs': 0,
    }

    try:
        with transaction.atomic():
            # Get the archived budget for this fiscal year
            try:
                budget = ApprovedBudget.all_objects.get(
                    fiscal_year=fiscal_year,
                    is_archived=True
                )
            except ApprovedBudget.DoesNotExist:
                raise ValueError(f"No archived budget found for fiscal year {fiscal_year}")

            # Unarchive the approved budget
            budget.is_archived = False
            budget.archived_at = None
            budget.archived_by = None
            budget.archive_reason = ""
            budget.save()
            unarchived_counts['approved_budgets'] = 1

            # Get all related budget allocations (including archived ones)
            allocations = BudgetAllocation.all_objects.filter(
                approved_budget=budget,
                is_archived=True
            )

            # Unarchive each allocation and its related documents
            for allocation in allocations:
                # Unarchive the allocation
                allocation.is_archived = False
                allocation.archived_at = None
                allocation.archived_by = None
                allocation.archive_reason = ""
                allocation.save()
                unarchived_counts['budget_allocations'] += 1

                # Unarchive all DepartmentPREs for this allocation
                pres = DepartmentPRE.all_objects.filter(
                    budget_allocation=allocation,
                    is_archived=True
                )
                for pre in pres:
                    pre.is_archived = False
                    pre.archived_at = None
                    pre.archived_by = None
                    pre.archive_reason = ""
                    pre.save()
                    unarchived_counts['department_pres'] += 1

                # Unarchive all PurchaseRequests for this allocation
                prs = PurchaseRequest.all_objects.filter(
                    budget_allocation=allocation,
                    is_archived=True
                )
                for pr in prs:
                    pr.is_archived = False
                    pr.archived_at = None
                    pr.archived_by = None
                    pr.archive_reason = ""
                    pr.save()
                    unarchived_counts['purchase_requests'] += 1

                # Unarchive all ActivityDesigns for this allocation
                ads = ActivityDesign.all_objects.filter(
                    budget_allocation=allocation,
                    is_archived=True
                )
                for ad in ads:
                    ad.is_archived = False
                    ad.archived_at = None
                    ad.archived_by = None
                    ad.archive_reason = ""
                    ad.save()
                    unarchived_counts['activity_designs'] += 1

            # Log to AuditTrail
            AuditTrail.objects.create(
                user=unarchived_by,
                action='UNARCHIVE',
                model_name='ApprovedBudget',
                record_id=str(budget.id),
                detail=f"Unarchived fiscal year {fiscal_year}. " +
                       f"Budgets: {unarchived_counts['approved_budgets']}, " +
                       f"Allocations: {unarchived_counts['budget_allocations']}, " +
                       f"PREs: {unarchived_counts['department_pres']}, " +
                       f"PRs: {unarchived_counts['purchase_requests']}, " +
                       f"ADs: {unarchived_counts['activity_designs']}. " +
                       f"Reason: {reason}"
            )

            return unarchived_counts

    except Exception as e:
        raise Exception(f"Error unarchiving fiscal year {fiscal_year}: {str(e)}")


def archive_record(
    model_class,
    record_id,
    archived_by: User,
    reason: str = "",
    archive_type: str = "MANUAL"
) -> bool:
    """
    Archive a single record (for selective archiving/delete replacement).

    Args:
        model_class: The model class (e.g., User, DepartmentPRE)
        record_id: ID of the record to archive
        archived_by: User performing the archive
        reason: Reason for archiving
        archive_type: Type of archive (default 'MANUAL')

    Returns:
        True if successful

    Raises:
        Exception: If record not found or error occurs
    """
    try:
        with transaction.atomic():
            # Get the record using all_objects to include non-archived only
            record = model_class.all_objects.get(id=record_id, is_archived=False)

            # Archive the record
            record.is_archived = True
            record.archived_at = timezone.now()
            record.archived_by = archived_by
            record.archive_reason = reason or "Manually archived"
            record.archive_type = archive_type
            record.save()

            # Log to AuditTrail
            AuditTrail.objects.create(
                user=archived_by,
                action='ARCHIVE',
                model_name=model_class.__name__,
                record_id=str(record_id),
                detail=f"Archived {model_class.__name__} record. Reason: {reason}"
            )

            return True

    except model_class.DoesNotExist:
        raise ValueError(f"{model_class.__name__} with ID {record_id} not found or already archived")
    except Exception as e:
        raise Exception(f"Error archiving {model_class.__name__} record: {str(e)}")


def unarchive_record(
    model_class,
    record_id,
    unarchived_by: User,
    reason: str = ""
) -> bool:
    """
    Unarchive (restore) a single record.

    Args:
        model_class: The model class (e.g., User, DepartmentPRE)
        record_id: ID of the record to unarchive
        unarchived_by: User performing the unarchive
        reason: Reason for unarchiving (required)

    Returns:
        True if successful

    Raises:
        ValueError: If reason is not provided
        Exception: If record not found or error occurs
    """
    if not reason or not reason.strip():
        raise ValueError("Unarchive reason is required")

    try:
        with transaction.atomic():
            # Get the archived record
            record = model_class.all_objects.get(id=record_id, is_archived=True)

            # Unarchive the record
            record.is_archived = False
            record.archived_at = None
            record.archived_by = None
            record.archive_reason = ""
            record.save()

            # Log to AuditTrail
            AuditTrail.objects.create(
                user=unarchived_by,
                action='UNARCHIVE',
                model_name=model_class.__name__,
                record_id=str(record_id),
                detail=f"Unarchived {model_class.__name__} record. Reason: {reason}"
            )

            return True

    except model_class.DoesNotExist:
        raise ValueError(f"{model_class.__name__} with ID {record_id} not found or not archived")
    except Exception as e:
        raise Exception(f"Error unarchiving {model_class.__name__} record: {str(e)}")


def get_archive_statistics() -> Dict[str, Dict[str, int]]:
    """
    Get statistics about archived records.

    Returns:
        Dictionary containing active and archived counts for each model
    """
    stats = {
        'ApprovedBudget': {
            'active': ApprovedBudget.objects.count(),
            'archived': ApprovedBudget.objects.archived().count(),
            'total': ApprovedBudget.all_objects.count(),
        },
        'BudgetAllocation': {
            'active': BudgetAllocation.objects.count(),
            'archived': BudgetAllocation.objects.archived().count(),
            'total': BudgetAllocation.all_objects.count(),
        },
        'DepartmentPRE': {
            'active': DepartmentPRE.objects.count(),
            'archived': DepartmentPRE.objects.archived().count(),
            'total': DepartmentPRE.all_objects.count(),
        },
        'PurchaseRequest': {
            'active': PurchaseRequest.objects.count(),
            'archived': PurchaseRequest.objects.archived().count(),
            'total': PurchaseRequest.all_objects.count(),
        },
        'ActivityDesign': {
            'active': ActivityDesign.objects.count(),
            'archived': ActivityDesign.objects.archived().count(),
            'total': ActivityDesign.all_objects.count(),
        },
        'User': {
            'active': User.objects.filter(is_archived=False).count(),
            'archived': User.objects.filter(is_archived=True).count(),
            'total': User.objects.all().count(),
        },
    }

    return stats


def get_fiscal_years_list(include_archived: bool = False) -> List[Dict[str, any]]:
    """
    Get list of fiscal years with their archive status.

    Args:
        include_archived: Whether to include archived fiscal years

    Returns:
        List of dictionaries with fiscal year info
    """
    if include_archived:
        budgets = ApprovedBudget.all_objects.all()
    else:
        budgets = ApprovedBudget.objects.all()

    fiscal_years = []
    for budget in budgets.order_by('-fiscal_year'):
        # Get counts for this fiscal year
        allocations_count = BudgetAllocation.all_objects.filter(
            approved_budget=budget
        ).count()

        pres_count = DepartmentPRE.all_objects.filter(
            budget_allocation__approved_budget=budget
        ).count()

        prs_count = PurchaseRequest.all_objects.filter(
            budget_allocation__approved_budget=budget
        ).count()

        ads_count = ActivityDesign.all_objects.filter(
            budget_allocation__approved_budget=budget
        ).count()

        fiscal_years.append({
            'fiscal_year': budget.fiscal_year,
            'title': budget.title,
            'amount': budget.amount,
            'is_archived': budget.is_archived,
            'archived_at': budget.archived_at,
            'archived_by': budget.archived_by.get_full_name() if budget.archived_by else None,
            'archive_reason': budget.archive_reason,
            'allocations_count': allocations_count,
            'pres_count': pres_count,
            'prs_count': prs_count,
            'ads_count': ads_count,
            'total_documents': pres_count + prs_count + ads_count,
        })

    return fiscal_years
