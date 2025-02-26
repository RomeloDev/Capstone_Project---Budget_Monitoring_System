from django.contrib import admin
from apps.admin_panel.models import BudgetAllocation, Budget

# Register your models here.
admin.site.register(BudgetAllocation)
admin.site.register(Budget)