# bb_budget_monitoring_system/apps/budgets/management/commands/auto_archive_fiscal_year.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.budgets.services import archive_fiscal_year
from apps.budgets.models import ApprovedBudget
from apps.users.models import User
from datetime import datetime
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Automatically archive previous fiscal year(s) on January 1st'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run in dry-run mode (no actual archiving)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force archive regardless of date (for testing)',
        )
        parser.add_argument(
            '--year',
            type=str,
            help='Specific year to archive (e.g., 2023)',
        )
        parser.add_argument(
            '--no-email',
            action='store_true',
            help='Skip sending email notifications',
        )

    def handle(self, *args, **options):
        today = timezone.now()
        is_dry_run = options['dry_run']
        force = options['force']
        specific_year = options.get('year')
        send_email_notification = not options['no_email']

        self.stdout.write(self.style.WARNING("=" * 70))
        self.stdout.write(self.style.WARNING("AUTOMATIC FISCAL YEAR ARCHIVE"))
        self.stdout.write(self.style.WARNING("=" * 70))

        if is_dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN MODE - No actual changes will be made"))

        # Check if today is January 1st (or force flag is set)
        if not force and not (today.month == 1 and today.day == 1):
            self.stdout.write(
                self.style.ERROR(
                    f"❌ Not January 1st (today is {today.strftime('%Y-%m-%d')}). "
                    "Use --force to run anyway."
                )
            )
            return

        current_year = str(today.year)

        if specific_year:
            # Archive specific year
            years_to_archive = [specific_year]
        else:
            # Archive all years before current year
            previous_year = str(today.year - 1)
            years_to_archive = [previous_year]

        self.stdout.write(
            self.style.SUCCESS(f"📅 Current year: {current_year}")
        )
        self.stdout.write(
            self.style.WARNING(f"📦 Years to archive: {', '.join(years_to_archive)}")
        )

        # Get all active budgets for years to archive
        budgets_to_archive = ApprovedBudget.objects.filter(
            fiscal_year__in=years_to_archive,
            is_archived=False
        )

        if not budgets_to_archive.exists():
            self.stdout.write(
                self.style.WARNING(f"⚠️  No active budgets found for years: {', '.join(years_to_archive)}")
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f"\n✅ Found {budgets_to_archive.count()} budget(s) to archive:")
        )

        total_archived = {
            'approved_budgets': 0,
            'budget_allocations': 0,
            'department_pres': 0,
            'purchase_requests': 0,
            'activity_designs': 0,
        }

        # Archive each fiscal year
        for budget in budgets_to_archive:
            fiscal_year = budget.fiscal_year

            self.stdout.write(
                self.style.WARNING(f"\n{'─' * 70}")
            )
            self.stdout.write(
                self.style.WARNING(f"📁 Processing Fiscal Year: {fiscal_year}")
            )
            self.stdout.write(
                self.style.WARNING(f"   Title: {budget.title}")
            )
            self.stdout.write(
                self.style.WARNING(f"   Amount: ₱{budget.amount:,.2f}")
            )

            if is_dry_run:
                self.stdout.write(
                    self.style.SUCCESS(f"   🔍 DRY RUN: Would archive fiscal year {fiscal_year}")
                )
                continue

            try:
                # Perform the archive
                archived_counts = archive_fiscal_year(
                    fiscal_year=fiscal_year,
                    archived_by=None,  # System user (automatic)
                    reason=f"Automatic archive on {today.strftime('%Y-%m-%d')}",
                    archive_type='FISCAL_YEAR'
                )

                # Update total counts
                for key in total_archived:
                    total_archived[key] += archived_counts[key]

                self.stdout.write(
                    self.style.SUCCESS(f"   ✅ Successfully archived fiscal year {fiscal_year}:")
                )
                self.stdout.write(
                    self.style.SUCCESS(f"      • Budgets: {archived_counts['approved_budgets']}")
                )
                self.stdout.write(
                    self.style.SUCCESS(f"      • Allocations: {archived_counts['budget_allocations']}")
                )
                self.stdout.write(
                    self.style.SUCCESS(f"      • PREs: {archived_counts['department_pres']}")
                )
                self.stdout.write(
                    self.style.SUCCESS(f"      • PRs: {archived_counts['purchase_requests']}")
                )
                self.stdout.write(
                    self.style.SUCCESS(f"      • ADs: {archived_counts['activity_designs']}")
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"   ❌ Error archiving fiscal year {fiscal_year}: {str(e)}")
                )
                continue

        # Summary
        self.stdout.write(
            self.style.WARNING(f"\n{'═' * 70}")
        )
        self.stdout.write(
            self.style.WARNING("📊 SUMMARY")
        )
        self.stdout.write(
            self.style.WARNING(f"{'═' * 70}")
        )

        if is_dry_run:
            self.stdout.write(
                self.style.WARNING("🔍 DRY RUN COMPLETE - No changes were made")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("✅ AUTOMATIC ARCHIVE COMPLETE")
            )
            self.stdout.write(
                self.style.SUCCESS(f"   • Budgets archived: {total_archived['approved_budgets']}")
            )
            self.stdout.write(
                self.style.SUCCESS(f"   • Allocations archived: {total_archived['budget_allocations']}")
            )
            self.stdout.write(
                self.style.SUCCESS(f"   • PREs archived: {total_archived['department_pres']}")
            )
            self.stdout.write(
                self.style.SUCCESS(f"   • PRs archived: {total_archived['purchase_requests']}")
            )
            self.stdout.write(
                self.style.SUCCESS(f"   • ADs archived: {total_archived['activity_designs']}")
            )

            # Send email notification to admins
            if send_email_notification and total_archived['approved_budgets'] > 0:
                self.send_admin_notifications(years_to_archive, total_archived, today)

    def send_admin_notifications(self, years_archived, counts, archive_date):
        """Send email notifications to all admin users"""
        admin_users = User.objects.filter(is_admin=True, is_active=True, is_archived=False)

        if not admin_users.exists():
            self.stdout.write(
                self.style.WARNING("⚠️  No admin users found to send notifications")
            )
            return

        subject = f"Budget System: Fiscal Year{'s' if len(years_archived) > 1 else ''} {', '.join(years_archived)} Automatically Archived"

        message = f"""
Budget Monitoring System - Automatic Archive Notification
{'=' * 60}

The following fiscal year(s) have been automatically archived:
{', '.join(years_archived)}

Archive Date: {archive_date.strftime('%B %d, %Y at %I:%M %p')}

Summary:
--------
• Approved Budgets: {counts['approved_budgets']}
• Budget Allocations: {counts['budget_allocations']}
• Department PREs: {counts['department_pres']}
• Purchase Requests: {counts['purchase_requests']}
• Activity Designs: {counts['activity_designs']}

Total Documents Archived: {counts['department_pres'] + counts['purchase_requests'] + counts['activity_designs']}

These records are now archived and will not appear in the active budget views.
To view or restore archived data, please access the Archive Center in the admin panel.

{'=' * 60}
This is an automated message from the Budget Monitoring System.
"""

        admin_emails = list(admin_users.values_list('email', flat=True))

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS(f"   📧 Email notifications sent to {len(admin_emails)} admin(s)")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ Failed to send email notifications: {str(e)}")
            )
