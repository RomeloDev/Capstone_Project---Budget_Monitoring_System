from django.contrib import admin
from .models import PurchaseRequest, PurchaseRequestItems, DepartmentPRE, ActivityDesign, PRELineItemBudget, PurchaseRequestAllocation, ActivityDesignAllocations, PREBudgetRealignment

# Register your models here.
admin.site.register(PurchaseRequest)
admin.site.register(PurchaseRequestItems)
admin.site.register(DepartmentPRE)
admin.site.register(ActivityDesign)
admin.site.register(PRELineItemBudget)
admin.site.register(PurchaseRequestAllocation)
admin.site.register(ActivityDesignAllocations)
admin.site.register(PREBudgetRealignment)