"""
Helper functions for budget report generation

This module centralizes data retrieval and processing logic for budget reports.
All export formats (Excel, PDF, CSV, JSON) use these helpers to ensure
consistent data across all report types.
"""

from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from apps.budgets.models import (
    BudgetAllocation,
    DepartmentPRE,
    PurchaseRequest,
    ActivityDesign,
    PurchaseRequestAllocation,
    ActivityDesignAllocation
)


def get_budget_data(user, year_filter=None, date_from=None, date_to=None, status_filter=None):
    """
    Get comprehensive budget data for reports with common filtering logic

    Args:
        user: Current user (for scoping data)
        year_filter: Fiscal year or 'all' (filters on allocated_at__year)
        date_from: Start date for transactions
        date_to: End date for transactions
        status_filter: Filter by status (Pending, Approved, etc.)

    Returns:
        dict: Contains all necessary data for reports including:
            - budget_allocations: QuerySet of BudgetAllocation objects
            - pres: QuerySet of DepartmentPRE objects
            - prs: QuerySet of PurchaseRequest objects
            - ads: QuerySet of ActivityDesign objects
            - totals: Dict with calculated totals
    """
    # Get budget allocations for the user
    budget_allocations = BudgetAllocation.objects.filter(
        end_user=user,
        is_active=True
    ).select_related('approved_budget')

    # Apply year filter
    if year_filter and year_filter != 'all':
        budget_allocations = budget_allocations.filter(allocated_at__year=year_filter)

    # Get PREs
    pres = DepartmentPRE.objects.filter(
        submitted_by=user,
        budget_allocation__in=budget_allocations
    ).exclude(
        status__in=['Draft', 'Rejected', 'Cancelled']
    ).select_related(
        'budget_allocation',
        'budget_allocation__approved_budget'
    ).prefetch_related(
        'line_items',
        'line_items__category',
        'line_items__subcategory'
    )

    # Apply status filter to PREs
    if status_filter and status_filter != 'all':
        pres = pres.filter(status=status_filter)

    # Get Purchase Requests
    prs = PurchaseRequest.objects.filter(
        submitted_by=user,
        budget_allocation__in=budget_allocations
    ).exclude(
        status__in=['Draft', 'Rejected', 'Cancelled']
    ).select_related(
        'budget_allocation',
        'source_pre',
        'source_line_item'
    ).prefetch_related('pre_allocations')

    # Apply date and status filters to PRs
    if date_from:
        prs = prs.filter(submitted_at__gte=date_from)
    if date_to:
        prs = prs.filter(submitted_at__lte=date_to)
    if status_filter and status_filter != 'all':
        prs = prs.filter(status=status_filter)

    # Get Activity Designs
    ads = ActivityDesign.objects.filter(
        submitted_by=user,
        budget_allocation__in=budget_allocations
    ).exclude(
        status__in=['Draft', 'Rejected', 'Cancelled']
    ).select_related('budget_allocation').prefetch_related('pre_allocations')

    # Apply date and status filters to ADs
    if date_from:
        ads = ads.filter(submitted_at__gte=date_from)
    if date_to:
        ads = ads.filter(submitted_at__lte=date_to)
    if status_filter and status_filter != 'all':
        ads = ads.filter(status=status_filter)

    # Calculate totals
    total_allocated = sum(ba.allocated_amount for ba in budget_allocations)
    total_pr_used = sum(ba.pr_amount_used for ba in budget_allocations)
    total_ad_used = sum(ba.ad_amount_used for ba in budget_allocations)
    total_used = total_pr_used + total_ad_used
    remaining = total_allocated - total_used

    return {
        'budget_allocations': budget_allocations,
        'pres': pres,
        'prs': prs,
        'ads': ads,
        'totals': {
            'allocated': total_allocated,
            'pr_used': total_pr_used,
            'ad_used': total_ad_used,
            'total_used': total_used,
            'remaining': remaining,
        }
    }


def get_quarterly_data(user, quarter, year_filter=None):
    """
    Get quarter-specific data for quarterly reports

    Args:
        user: Current user
        quarter: Quarter string ('Q1', 'Q2', 'Q3', 'Q4')
        year_filter: Optional year filter

    Returns:
        dict: Quarter-specific budget data
    """
    # Get base data
    data = get_budget_data(user, year_filter)

    # Calculate quarter-specific totals
    quarter_allocated = Decimal('0.00')
    quarter_consumed = Decimal('0.00')

    approved_pres = data['pres'].filter(status__in=['Approved', 'Partially Approved'])

    for pre in approved_pres:
        for line_item in pre.line_items.all():
            # Get quarter amount
            quarter_attr = f'q{quarter[1]}_amount'
            q_amount = getattr(line_item, quarter_attr, Decimal('0.00'))
            quarter_allocated += q_amount

            # Get quarter consumed
            quarter_consumed += line_item.get_quarter_consumed(quarter)

    quarter_remaining = quarter_allocated - quarter_consumed

    return {
        **data,
        'quarter': quarter,
        'quarter_totals': {
            'allocated': quarter_allocated,
            'consumed': quarter_consumed,
            'remaining': quarter_remaining
        }
    }


def get_category_data(user, year_filter=None):
    """
    Get category-wise breakdown of budget

    Args:
        user: Current user
        year_filter: Optional year filter

    Returns:
        dict: Category-wise budget breakdown
    """
    data = get_budget_data(user, year_filter)

    # Group by category
    categories = {}

    approved_pres = data['pres'].filter(status__in=['Approved', 'Partially Approved'])

    for pre in approved_pres:
        for line_item in pre.line_items.all():
            category_name = line_item.category.name if line_item.category else 'Uncategorized'

            if category_name not in categories:
                categories[category_name] = {
                    'total': Decimal('0.00'),
                    'consumed': Decimal('0.00'),
                    'items': []
                }

            total_allocated = line_item.get_total()
            total_consumed = sum(
                line_item.get_quarter_consumed(q) for q in ['Q1', 'Q2', 'Q3', 'Q4']
            )

            categories[category_name]['total'] += total_allocated
            categories[category_name]['consumed'] += total_consumed
            categories[category_name]['items'].append({
                'name': line_item.item_name,
                'allocated': total_allocated,
                'consumed': total_consumed,
                'remaining': total_allocated - total_consumed
            })

    # Calculate remaining and utilization for each category
    for category_name, cat_data in categories.items():
        cat_data['remaining'] = cat_data['total'] - cat_data['consumed']
        cat_data['utilization'] = (
            (cat_data['consumed'] / cat_data['total'] * 100)
            if cat_data['total'] > 0 else 0
        )

    return {
        **data,
        'categories': categories
    }


def get_transaction_data(user, year_filter=None, date_from=None, date_to=None, status_filter=None):
    """
    Get all transactions (PREs, PRs, ADs) in a unified format

    Args:
        user: Current user
        year_filter: Optional year filter
        date_from: Start date filter
        date_to: End date filter
        status_filter: Status filter

    Returns:
        dict: Transaction data with unified list
    """
    data = get_budget_data(user, year_filter, date_from, date_to, status_filter)

    transactions = []

    # Add PRE transactions
    for pre in data['pres']:
        quarters_used = []
        for q in ['Q1', 'Q2', 'Q3', 'Q4']:
            if pre.line_items.filter(**{f'{q.lower()}_amount__gt': 0}).exists():
                quarters_used.append(q)

        transactions.append({
            'date': pre.submitted_at or pre.created_at,
            'type': 'PRE',
            'number': f"{pre.department} - FY {pre.fiscal_year}",
            'line_item': f"{pre.line_items.count()} Line Items",
            'quarter': ', '.join(quarters_used) if quarters_used else 'All',
            'amount': pre.total_amount,
            'status': pre.status
        })

    # Add PR transactions
    for pr in data['prs']:
        allocations = pr.pre_allocations.all()
        if allocations:
            quarters = set(alloc.quarter for alloc in allocations)
            line_items = set(alloc.pre_line_item.item_name for alloc in allocations)

            transactions.append({
                'date': pr.submitted_at or pr.created_at,
                'type': 'PR',
                'number': pr.pr_number,
                'line_item': ', '.join(list(line_items)[:2]) + ('...' if len(line_items) > 2 else ''),
                'quarter': ', '.join(sorted(quarters)),
                'amount': pr.total_amount,
                'status': pr.status
            })

    # Add AD transactions
    for ad in data['ads']:
        allocations = ad.pre_allocations.all()
        if allocations:
            quarters = set(alloc.quarter for alloc in allocations)
            line_items = set(alloc.pre_line_item.item_name for alloc in allocations)

            transactions.append({
                'date': ad.submitted_at or ad.created_at,
                'type': 'AD',
                'number': ad.ad_number,
                'line_item': ', '.join(list(line_items)[:2]) + ('...' if len(line_items) > 2 else ''),
                'quarter': ', '.join(sorted(quarters)),
                'amount': ad.total_amount,
                'status': ad.status
            })

    # Sort by date descending
    transactions.sort(
        key=lambda x: x['date'] if x['date'] else timezone.now(),
        reverse=True
    )

    return {
        **data,
        'transactions': transactions
    }


def format_currency(amount):
    """
    Consistent currency formatting across all reports

    Args:
        amount: Decimal or float amount

    Returns:
        str: Formatted currency string
    """
    return f'₱{amount:,.2f}'


def get_quarter_label(quarter):
    """
    Get user-friendly quarter label

    Args:
        quarter: Quarter string ('Q1', 'Q2', 'Q3', 'Q4')

    Returns:
        str: Formatted quarter label
    """
    quarter_names = {
        'Q1': 'First Quarter',
        'Q2': 'Second Quarter',
        'Q3': 'Third Quarter',
        'Q4': 'Fourth Quarter'
    }
    return quarter_names.get(quarter, quarter)


def validate_year_filter(year):
    """
    Validate year filter parameter

    Args:
        year: Year string or 'all'

    Returns:
        bool: True if valid, False otherwise
    """
    if year == 'all':
        return True
    try:
        year_int = int(year)
        current_year = timezone.now().year
        return 2020 <= year_int <= current_year + 1
    except (ValueError, TypeError):
        return False


def get_available_years(user):
    """
    Get list of years with budget allocations for the user

    Args:
        user: Current user

    Returns:
        list: List of years (integers) sorted descending
    """
    allocations = BudgetAllocation.objects.filter(
        end_user=user,
        is_active=True
    ).dates('allocated_at', 'year', order='DESC')

    return [alloc.year for alloc in allocations]
