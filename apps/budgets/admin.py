from django.contrib import admin
from .models import ApprovedBudget, SupportingDocument, DepartmentPRE, BudgetAllocation, PRECategory, PRELineItem, PREReceipt, PRESubCategory, SystemNotification, RequestApproval, PurchaseRequest, PurchaseRequestAllocation, PurchaseRequestItem, PRDraft, PRDraftSupportingDocument, PurchaseRequestSupportingDocument, ActivityDesign, ActivityDesignAllocation, ActivityDesignSupportingDocument

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
admin.site.register(PurchaseRequest)
admin.site.register(PurchaseRequestAllocation)
admin.site.register(PurchaseRequestItem)
admin.site.register(PRDraft)
admin.site.register(PRDraftSupportingDocument)
admin.site.register(PurchaseRequestSupportingDocument)
admin.site.register(ActivityDesign)
admin.site.register(ActivityDesignAllocation)
admin.site.register(ActivityDesignSupportingDocument)