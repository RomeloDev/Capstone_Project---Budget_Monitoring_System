# Create file: apps/budgets/management/commands/init_pre_categories.py

from django.core.management.base import BaseCommand
from apps.budgets.models import PRECategory

class Command(BaseCommand):
    help = 'Initialize PRE budget categories'
    
    def handle(self, *args, **options):
        categories = [
            {
                'name': 'Personnel Services',
                'category_type': 'PERSONNEL',
                'code': 'PS',
                'sort_order': 1
            },
            {
                'name': 'Maintenance and Other Operating Expenses',
                'category_type': 'MOOE',
                'code': 'MOOE',
                'sort_order': 2
            },
            {
                'name': 'Capital Outlays',
                'category_type': 'CAPITAL',
                'code': 'CO',
                'sort_order': 3
            },
        ]
        
        created_count = 0
        
        for cat_data in categories:
            category, created = PRECategory.objects.get_or_create(
                category_type=cat_data['category_type'],
                defaults=cat_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Created category: {category.name}")
                )
            else:
                self.stdout.write(f"Category already exists: {category.name}")
        
        self.stdout.write(
            self.style.SUCCESS(f"\nCompleted: {created_count} new categories created")
        )