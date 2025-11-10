# bb_budget_monitoring_system/apps/budgets/management/commands/create_archive_test_data.py
from django.core.management.base import BaseCommand
from apps.budgets.models import (
    ApprovedBudget,
    BudgetAllocation,
    DepartmentPRE,
    PurchaseRequest,
    ActivityDesign,
)
from apps.users.models import User
from decimal import Decimal
from django.utils import timezone


class Command(BaseCommand):
    help = 'Create test data for archive feature testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--years',
            type=str,
            default='2021,2022,2023,2024,2025',
            help='Comma-separated list of years to create (default: 2021,2022,2023,2024,2025)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing test data before creating new data',
        )

    def handle(self, *args, **options):
        years_str = options['years']
        clear_existing = options['clear']

        years = [year.strip() for year in years_str.split(',')]

        self.stdout.write(self.style.WARNING("=" * 70))
        self.stdout.write(self.style.WARNING("ARCHIVE TEST DATA CREATION"))
        self.stdout.write(self.style.WARNING("=" * 70))

        # Get or create test users
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'fullname': 'Admin User',
                'email': 'admin@test.com',
                'department': 'Finance',
                'is_admin': True,
                'is_staff': True,
            }
        )

        test_users = []
        departments = ['IT Department', 'HR Department', 'Finance Department']

        for i, dept in enumerate(departments, start=1):
            user, created = User.objects.get_or_create(
                username=f'testuser{i}',
                defaults={
                    'fullname': f'Test User {i}',
                    'email': f'testuser{i}@test.com',
                    'department': dept,
                    'position': f'Head - {dept}',
                }
            )
            test_users.append(user)
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"[OK] Created test user: {user.fullname} ({dept})")
                )

        if clear_existing:
            self.stdout.write(
                self.style.WARNING("\n[DELETE]  Clearing existing test data...")
            )
            ApprovedBudget.all_objects.filter(title__startswith='Test Budget').delete()
            self.stdout.write(
                self.style.SUCCESS("[OK] Existing test data cleared")
            )

        self.stdout.write(
            self.style.WARNING(f"\n[ARCHIVE] Creating test data for years: {', '.join(years)}")
        )

        total_created = {
            'budgets': 0,
            'allocations': 0,
            'pres': 0,
            'prs': 0,
            'ads': 0,
        }

        # Create test data for each year
        for year in years:
            self.stdout.write(
                self.style.WARNING(f"\n{'-' * 70}")
            )
            self.stdout.write(
                self.style.WARNING(f"[DATE] Creating data for fiscal year: {year}")
            )

            # Check if budget already exists for this year
            existing_budget = ApprovedBudget.all_objects.filter(fiscal_year=year).first()
            if existing_budget:
                self.stdout.write(
                    self.style.WARNING(f"[WARNING]  Budget for year {year} already exists: {existing_budget.title}")
                )
                self.stdout.write(
                    self.style.WARNING(f"   Skipping year {year}")
                )
                continue

            # Create ApprovedBudget
            budget = ApprovedBudget.objects.create(
                title=f'Test Budget {year}',
                fiscal_year=year,
                amount=Decimal('10000000.00'),  # 10 million
                remaining_budget=Decimal('10000000.00'),
                description=f'Test budget for fiscal year {year} (archive testing)',
                created_by=admin_user,
                is_active=True
            )
            total_created['budgets'] += 1

            self.stdout.write(
                self.style.SUCCESS(f"   [OK] Created ApprovedBudget: {budget.title} (PHP {budget.amount:,.2f})")
            )

            # Create BudgetAllocations (3 per year, one for each test user)
            for i, user in enumerate(test_users, start=1):
                allocation = BudgetAllocation.objects.create(
                    approved_budget=budget,
                    department=user.department,
                    end_user=user,
                    allocated_amount=Decimal('3000000.00'),  # 3 million per allocation
                    remaining_balance=Decimal('3000000.00')
                )
                total_created['allocations'] += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"      • Created BudgetAllocation for {user.fullname} ({user.department}): "
                        f"PHP {allocation.allocated_amount:,.2f}"
                    )
                )

                # Create DepartmentPRE for each allocation
                pre = DepartmentPRE.objects.create(
                    budget_allocation=allocation,
                    submitted_by=user,
                    department=user.department,
                    program=f'Test Program {i}',
                    fund_source='General Fund',
                    fiscal_year=year,
                    status='Approved',
                    is_valid=True,
                    total_amount=Decimal('1000000.00'),  # 1 million
                    submitted_at=timezone.now(),
                    final_approved_at=timezone.now(),
                )
                total_created['pres'] += 1

                # Create PurchaseRequest for each allocation
                pr = PurchaseRequest.objects.create(
                    budget_allocation=allocation,
                    submitted_by=user,
                    department=user.department,
                    pr_number=f'PR-{year}-{i:03d}',
                    purpose=f'Test purchase request for {year}',
                    status='Approved',
                    is_valid=True,
                    total_amount=Decimal('500000.00'),  # 500k
                    submitted_at=timezone.now(),
                    final_approved_at=timezone.now(),
                )
                total_created['prs'] += 1

                # Create ActivityDesign for each allocation
                ad = ActivityDesign.objects.create(
                    budget_allocation=allocation,
                    submitted_by=user,
                    department=user.department,
                    ad_number=f'AD-{year}-{i:03d}',
                    activity_title=f'Test Activity {year}',
                    activity_description=f'Test activity design for fiscal year {year}',
                    purpose='Testing purposes',
                    status='Approved',
                    is_valid=True,
                    total_amount=Decimal('500000.00'),  # 500k
                    submitted_at=timezone.now(),
                    final_approved_at=timezone.now(),
                )
                total_created['ads'] += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"   [OK] Created 3 allocations with PRE, PR, and AD documents"
                )
            )

        # Summary
        self.stdout.write(
            self.style.WARNING(f"\n{'=' * 70}")
        )
        self.stdout.write(
            self.style.WARNING("[STATS] SUMMARY")
        )
        self.stdout.write(
            self.style.WARNING(f"{'=' * 70}")
        )
        self.stdout.write(
            self.style.SUCCESS("[OK] TEST DATA CREATION COMPLETE")
        )
        self.stdout.write(
            self.style.SUCCESS(f"   • Approved Budgets: {total_created['budgets']}")
        )
        self.stdout.write(
            self.style.SUCCESS(f"   • Budget Allocations: {total_created['allocations']}")
        )
        self.stdout.write(
            self.style.SUCCESS(f"   • Department PREs: {total_created['pres']}")
        )
        self.stdout.write(
            self.style.SUCCESS(f"   • Purchase Requests: {total_created['prs']}")
        )
        self.stdout.write(
            self.style.SUCCESS(f"   • Activity Designs: {total_created['ads']}")
        )
        self.stdout.write(
            self.style.WARNING(f"\n[INFO] You can now test the archive feature with this data!")
        )
        self.stdout.write(
            self.style.WARNING(f"   Try: python manage.py auto_archive_fiscal_year --year 2021 --dry-run")
        )
