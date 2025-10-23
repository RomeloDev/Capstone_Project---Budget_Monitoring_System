# Create file: apps/budgets/management/commands/migrate_pre_line_items.py

from django.core.management.base import BaseCommand
from apps.budgets.models import DepartmentPRE as NewDepartmentPRE
from apps.end_user_app.utils.pre_parser import parse_pre_excel
import os

class Command(BaseCommand):
    help = 'Migrate existing PREs to create line items from Excel files'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--pre-id',
            type=str,
            help='Specific PRE ID to migrate (optional)',
        )
    
    def handle(self, *args, **options):
        pre_id = options.get('pre_id')
        
        if pre_id:
            # Migrate specific PRE
            pres = NewDepartmentPRE.objects.filter(id=pre_id)
        else:
            # Migrate all PREs without line items
            pres = NewDepartmentPRE.objects.filter(
                uploaded_excel_file__isnull=False
            ).exclude(status='Draft')
        
        total = pres.count()
        success_count = 0
        error_count = 0
        skipped_count = 0
        
        self.stdout.write(f"Found {total} PREs to process...")
        
        for pre in pres:
            # Skip if already has line items
            if pre.line_items.exists():
                self.stdout.write(f"⏭️  PRE {pre.id}: Already has {pre.line_items.count()} line items")
                skipped_count += 1
                continue
            
            # Check if file exists
            if not pre.uploaded_excel_file:
                self.stdout.write(
                    self.style.WARNING(f"⚠️  PRE {pre.id}: No Excel file")
                )
                error_count += 1
                continue
            
            if not os.path.exists(pre.uploaded_excel_file.path):
                self.stdout.write(
                    self.style.WARNING(f"⚠️  PRE {pre.id}: Excel file not found at {pre.uploaded_excel_file.path}")
                )
                error_count += 1
                continue
            
            self.stdout.write(f"🔄 Processing PRE {pre.id}...")
            
            try:
                # Parse Excel
                result = parse_pre_excel(pre.uploaded_excel_file.path)
                
                if not result['success']:
                    self.stdout.write(
                        self.style.ERROR(f"❌ PRE {pre.id}: Parse failed - {'; '.join(result['errors'])}")
                    )
                    error_count += 1
                    continue
                
                # Create line items
                from apps.end_user_app.views import create_pre_line_items
                
                line_items_created = create_pre_line_items(pre, result['data'])
                
                if line_items_created > 0:
                    # Update total amount if needed
                    if pre.total_amount != result['grand_total']:
                        pre.total_amount = result['grand_total']
                        pre.save()
                    
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ PRE {pre.id}: Created {line_items_created} items, "
                            f"Total: ₱{result['grand_total']:,.2f}"
                        )
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f"❌ PRE {pre.id}: No line items created")
                    )
                
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"❌ PRE {pre.id}: {str(e)}")
                )
        
        # Summary
        self.stdout.write("\n" + "="*60)
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Success: {success_count}\n"
                f"⏭️  Skipped: {skipped_count}\n"
                f"❌ Errors: {error_count}\n"
                f"📊 Total: {total}"
            )
        )