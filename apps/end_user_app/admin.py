from django.contrib import admin
from .models import PurchaseRequest, PurchaseRequestItems, DepartmentPRE, ActivityDesign, PRELineItemBudget

# Register your models here.
admin.site.register(PurchaseRequest)
admin.site.register(PurchaseRequestItems)
admin.site.register(DepartmentPRE)
admin.site.register(ActivityDesign)
admin.site.register(PRELineItemBudget)