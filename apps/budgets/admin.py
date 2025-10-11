from django.contrib import admin
from .models import ApprovedBudget, SupportingDocument, DepartmentPRE, BudgetAllocation, PRECategory, PRELineItem, PREReceipt, PRESubCategory, SystemNotification, RequestApproval

# Register your models here.
admin.site.register(ApprovedBudget)
admin.site.register(SupportingDocument)
admin.site.register(DepartmentPRE)
admin.site.register(BudgetAllocation)
admin.site.register(PRECategory)
admin.site.register(PRELineItem)
admin.site.register(PREReceipt)
admin.site.register(PRESubCategory)
admin.site.register(SystemNotification)
admin.site.register(RequestApproval)