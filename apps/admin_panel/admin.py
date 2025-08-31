from django.contrib import admin
from apps.admin_panel.models import Budget, BudgetAllocation, AuditTrail, ApprovedBudget

# Register your models here.
admin.site.register(BudgetAllocation)
admin.site.register(AuditTrail)
admin.site.register(ApprovedBudget)