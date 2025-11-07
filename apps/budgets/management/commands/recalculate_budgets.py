"""
Management command to recalculate budget allocations from actual approved documents.

This fixes any discrepancies caused by the old buggy signal logic where only
the largest PR/AD was being tracked instead of the sum of all approved requests.

Usage:
    python manage.py recalculate_budgets
    python manage.py recalculate_budgets --dry-run  # Preview changes without saving
"""

from django.core.management.base import BaseCommand
from django.db.models import Sum
from decimal import Decimal
from apps.budgets.models import BudgetAllocation


class Command(BaseCommand):
    help = 'Recalculate budget allocations based on actual approved PRE, PR, and AD documents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without actually saving to database',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('\n[!] DRY RUN MODE - No changes will be saved\n'))
        else:
            self.stdout.write(self.style.WARNING('\n[*] RECALCULATING BUDGET ALLOCATIONS...\n'))

        allocations = BudgetAllocation.objects.all()
        total_allocations = allocations.count()
        fixed_count = 0

        self.stdout.write(f'Found {total_allocations} budget allocations to check\n')
        self.stdout.write('='*80 + '\n')

        for allocation in allocations:
            # Calculate actual amounts from approved documents
            actual_pre_total = allocation.pres.filter(
                status='Approved'
            ).aggregate(
                total=Sum('total_amount')
            )['total'] or Decimal('0.00')

            actual_pr_total = allocation.purchase_requests.filter(
                status='Approved'
            ).aggregate(
                total=Sum('total_amount')
            )['total'] or Decimal('0.00')

            actual_ad_total = allocation.activity_designs.filter(
                status='Approved'
            ).aggregate(
                total=Sum('total_amount')
            )['total'] or Decimal('0.00')

            # Compare with current tracked amounts
            pre_diff = actual_pre_total - allocation.pre_amount_used
            pr_diff = actual_pr_total - allocation.pr_amount_used
            ad_diff = actual_ad_total - allocation.ad_amount_used

            has_discrepancy = (pre_diff != 0 or pr_diff != 0 or ad_diff != 0)

            if has_discrepancy:
                fixed_count += 1

                self.stdout.write(f'\n[#] Allocation #{allocation.id}: {allocation.department} - {allocation.end_user.get_full_name()}')
                self.stdout.write(f'   Approved Budget: {allocation.approved_budget.title} (FY {allocation.approved_budget.fiscal_year})')
                self.stdout.write(f'   Allocated Amount: P{allocation.allocated_amount:,.2f}\n')

                # PRE discrepancy
                if pre_diff != 0:
                    self.stdout.write(self.style.WARNING(
                        f'   PRE: P{allocation.pre_amount_used:,.2f} -> P{actual_pre_total:,.2f} '
                        f'({"+" if pre_diff > 0 else ""}{pre_diff:,.2f})'
                    ))
                else:
                    self.stdout.write(f'   PRE: P{allocation.pre_amount_used:,.2f} [OK]')

                # PR discrepancy
                if pr_diff != 0:
                    approved_prs = allocation.purchase_requests.filter(status='Approved')
                    self.stdout.write(self.style.WARNING(
                        f'   PR:  P{allocation.pr_amount_used:,.2f} -> P{actual_pr_total:,.2f} '
                        f'({"+" if pr_diff > 0 else ""}{pr_diff:,.2f}) - {approved_prs.count()} approved PRs'
                    ))
                    for pr in approved_prs:
                        self.stdout.write(f'        - PR-{pr.pr_number}: P{pr.total_amount:,.2f}')
                else:
                    self.stdout.write(f'   PR:  P{allocation.pr_amount_used:,.2f} [OK]')

                # AD discrepancy
                if ad_diff != 0:
                    approved_ads = allocation.activity_designs.filter(status='Approved')
                    self.stdout.write(self.style.WARNING(
                        f'   AD:  P{allocation.ad_amount_used:,.2f} -> P{actual_ad_total:,.2f} '
                        f'({"+" if ad_diff > 0 else ""}{ad_diff:,.2f}) - {approved_ads.count()} approved ADs'
                    ))
                    for ad in approved_ads:
                        self.stdout.write(f'        - AD-{ad.ad_number or ad.id.hex[:8]}: P{ad.total_amount:,.2f}')
                else:
                    self.stdout.write(f'   AD:  P{allocation.ad_amount_used:,.2f} [OK]')

                # Calculate new remaining balance
                old_remaining = allocation.remaining_balance
                new_remaining = allocation.allocated_amount - (actual_pr_total + actual_ad_total)

                self.stdout.write(f'\n   Remaining Balance: P{old_remaining:,.2f} -> P{new_remaining:,.2f}')

                # Apply changes
                if not dry_run:
                    allocation.pre_amount_used = actual_pre_total
                    allocation.pr_amount_used = actual_pr_total
                    allocation.ad_amount_used = actual_ad_total
                    allocation.update_remaining_balance()
                    self.stdout.write(self.style.SUCCESS('   [FIXED]'))
                else:
                    self.stdout.write(self.style.WARNING('   [Would fix - dry run]'))

                self.stdout.write('-'*80)

        # Summary
        self.stdout.write('\n' + '='*80)
        if fixed_count > 0:
            if dry_run:
                self.stdout.write(self.style.WARNING(
                    f'\n[!] Found {fixed_count} allocation(s) with discrepancies'
                ))
                self.stdout.write(self.style.WARNING(
                    'Run without --dry-run to apply fixes\n'
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f'\n[OK] Successfully fixed {fixed_count} allocation(s)!\n'
                ))
        else:
            self.stdout.write(self.style.SUCCESS(
                '\n[OK] All budget allocations are accurate! No fixes needed.\n'
            ))
