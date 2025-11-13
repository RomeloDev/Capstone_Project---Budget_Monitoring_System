from django.contrib import admin
from .models import ApprovedBudget, SupportingDocument, DepartmentPRE, BudgetAllocation, PRECategory, PRELineItem, PREReceipt, PRESubCategory, SystemNotification, RequestApproval, PurchaseRequest, PurchaseRequestAllocation, PurchaseRequestItem, PRDraft, PRDraftSupportingDocument, PurchaseRequestSupportingDocument, ActivityDesign, ActivityDesignAllocation, ActivityDesignSupportingDocument, DepartmentPRESupportingDocument

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


@admin.register(DepartmentPRESupportingDocument)
class DepartmentPRESupportingDocumentAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'department_pre', 'uploaded_by', 'get_file_size', 'uploaded_at']
    list_filter = ['uploaded_at', 'uploaded_by']
    search_fields = ['file_name', 'description', 'department_pre__id']
    readonly_fields = ['uploaded_at', 'file_size']
    date_hierarchy = 'uploaded_at'

    def get_file_size(self, obj):
        """Display file size in human-readable format"""
        return obj.get_file_size_display()
    get_file_size.short_description = 'File Size'