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

            # Get current timestamp for consistent archiving
            now = timezone.now()
            cascade_reason = f"Cascaded from fiscal year {fiscal_year}"

            # OPTIMIZED: Bulk archive all budget allocations
            allocations_queryset = BudgetAllocation.all_objects.filter(
                approved_budget=budget,
                is_archived=False
            )
            archived_counts['budget_allocations'] = allocations_queryset.update(
                is_archived=True,
                archived_at=now,
                archived_by=archived_by,
                archive_reason=cascade_reason,
                archive_type=archive_type
            )

            # OPTIMIZED: Bulk archive all DepartmentPREs for this budget
            pres_queryset = DepartmentPRE.all_objects.filter(
                budget_allocation__approved_budget=budget,
                is_archived=False
            )
            archived_counts['department_pres'] = pres_queryset.update(
                is_archived=True,
                archived_at=now,
                archived_by=archived_by,
                archive_reason=cascade_reason,
                archive_type=archive_type
            )

            # OPTIMIZED: Bulk archive all PurchaseRequests for this budget
            prs_queryset = PurchaseRequest.all_objects.filter(
                budget_allocation__approved_budget=budget,
                is_archived=False
            )
            archived_counts['purchase_requests'] = prs_queryset.update(
                is_archived=True,
                archived_at=now,
                archived_by=archived_by,
                archive_reason=cascade_reason,
                archive_type=archive_type
            )

            # OPTIMIZED: Bulk archive all ActivityDesigns for this budget
            ads_queryset = ActivityDesign.all_objects.filter(
                budget_allocation__approved_budget=budget,
                is_archived=False
            )
            archived_counts['activity_designs'] = ads_queryset.update(
                is_archived=True,
                archived_at=now,
                archived_by=archived_by,
                archive_reason=cascade_reason,
                archive_type=archive_type
            )

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


def validate_fiscal_year_for_archive(fiscal_year: str) -> Dict[str, any]:
    """
    Validate if a fiscal year is ready for archiving.

    Checks for:
    - Future years (blocking)
    - Pending documents (warning)
    - Negative budget balances (blocking)
    - Already archived (blocking)

    Args:
        fiscal_year: Year to validate (e.g., "2024")

    Returns:
        Dictionary with:
        {
            'ready': bool,
            'warnings': list[str],
            'blocking_issues': list[str],
            'statistics': dict
        }
    """
    from django.db.models import Q

    warnings = []
    blocking_issues = []
    statistics = {}

    # Check 1: Fiscal year exists and is not already archived
    try:
        budget = ApprovedBudget.objects.get(fiscal_year=fiscal_year)
    except ApprovedBudget.DoesNotExist:
        try:
            # Check if it exists but is already archived
            budget = ApprovedBudget.all_objects.get(fiscal_year=fiscal_year, is_archived=True)
            blocking_issues.append(f"Fiscal year {fiscal_year} is already archived")
            return {
                'ready': False,
                'warnings': warnings,
                'blocking_issues': blocking_issues,
                'statistics': {}
            }
        except ApprovedBudget.DoesNotExist:
            blocking_issues.append(f"Fiscal year {fiscal_year} not found")
            return {
                'ready': False,
                'warnings': warnings,
                'blocking_issues': blocking_issues,
                'statistics': {}
            }

    # Check 2: Not a future year
    today = timezone.now()
    current_year = today.year

    try:
        year_int = int(fiscal_year)
        if year_int > current_year:
            blocking_issues.append(f"Cannot archive future year {fiscal_year} (current year is {current_year})")
        elif year_int == current_year:
            # Check if we're past the fiscal year end (assuming fiscal year = calendar year)
            if today.month < 12 or (today.month == 12 and today.day < 31):
                warnings.append(f"Archiving current year {fiscal_year} before year end (current date: {today.strftime('%Y-%m-%d')})")
    except ValueError:
        blocking_issues.append(f"Invalid fiscal year format: {fiscal_year}")

    # Check 3: Pending documents (warnings only, not blocking)
    pending_pres = DepartmentPRE.objects.filter(
        budget_allocation__approved_budget=budget,
        status='Pending'
    ).count()

    pending_prs = PurchaseRequest.objects.filter(
        budget_allocation__approved_budget=budget,
        status='Pending'
    ).count()

    pending_ads = ActivityDesign.objects.filter(
        budget_allocation__approved_budget=budget,
        status='Pending'
    ).count()

    if pending_pres > 0:
        warnings.append(f"{pending_pres} Department PRE(s) still pending approval")
    if pending_prs > 0:
        warnings.append(f"{pending_prs} Purchase Request(s) still pending approval")
    if pending_ads > 0:
        warnings.append(f"{pending_ads} Activity Design(s) still pending approval")

    # Check 4: Negative budget balances (blocking)
    if hasattr(budget, 'remaining_budget') and budget.remaining_budget < 0:
        blocking_issues.append(
            f"Budget has negative balance: ₱{budget.remaining_budget:,.2f}"
        )

    # Gather statistics
    statistics = {
        'fiscal_year': fiscal_year,
        'budget_amount': budget.amount,
        'remaining_budget': getattr(budget, 'remaining_budget', 0),
        'total_allocations': BudgetAllocation.objects.filter(approved_budget=budget).count(),
        'total_pres': DepartmentPRE.objects.filter(budget_allocation__approved_budget=budget).count(),
        'total_prs': PurchaseRequest.objects.filter(budget_allocation__approved_budget=budget).count(),
        'total_ads': ActivityDesign.objects.filter(budget_allocation__approved_budget=budget).count(),
        'pending_pres': pending_pres,
        'pending_prs': pending_prs,
        'pending_ads': pending_ads,
    }

    return {
        'ready': len(blocking_issues) == 0,
        'warnings': warnings,
        'blocking_issues': blocking_issues,
        'statistics': statistics
    }


def estimate_archive_size(fiscal_year: str) -> Dict[str, any]:
    """
    Estimate the size and duration of an archive operation.

    Args:
        fiscal_year: Year to estimate (e.g., "2024")

    Returns:
        Dictionary with:
        {
            'total_records': int,
            'estimated_time_seconds': int,
            'database_size_kb': float,
            'counts': dict
        }

    Raises:
        ValueError: If fiscal year not found
    """
    try:
        budget = ApprovedBudget.objects.get(fiscal_year=fiscal_year)
    except ApprovedBudget.DoesNotExist:
        raise ValueError(f"Fiscal year {fiscal_year} not found")

    # Count all records that will be archived
    counts = {
        'budgets': 1,
        'allocations': BudgetAllocation.objects.filter(
            approved_budget=budget
        ).count(),
        'pres': DepartmentPRE.objects.filter(
            budget_allocation__approved_budget=budget
        ).count(),
        'prs': PurchaseRequest.objects.filter(
            budget_allocation__approved_budget=budget
        ).count(),
        'ads': ActivityDesign.objects.filter(
            budget_allocation__approved_budget=budget
        ).count(),
    }

    total_records = sum(counts.values())

    # Estimation formulas (conservative estimates)
    # With bulk updates: ~500 records per second (optimized)
    # Without bulk updates: ~50 records per second (old method)
    estimated_time = max(1, total_records / 500)  # Using optimized bulk update speed

    # Average record size estimation: ~3KB per record (conservative)
    estimated_size = (total_records * 3)  # in KB

    return {
        'total_records': total_records,
        'estimated_time_seconds': int(estimated_time),
        'database_size_kb': round(estimated_size, 2),
        'database_size_mb': round(estimated_size / 1024, 2),
        'counts': counts,
        'fiscal_year': fiscal_year,
        'budget_title': budget.title,
        'budget_amount': budget.amount,
    }
