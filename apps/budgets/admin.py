from django.contrib import admin
from .models import ApprovedBudget, SupportingDocument, DepartmentPRE, BudgetAllocation, PRECategory, PRELineItem, PREReceipt, PRESubCategory, SystemNotification, RequestApproval, PurchaseRequest, PurchaseRequestAllocation, PurchaseRequestItem, PRDraft, PRDraftSupportingDocument, PurchaseRequestSupportingDocument, ActivityDesign, ActivityDesignAllocation, ActivityDesignSupportingDocument, DepartmentPRESupportingDocument, BudgetSavings, PRELineItemSavings

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


@admin.register(BudgetSavings)
class BudgetSavingsAdmin(admin.ModelAdmin):
    list_display = [
        'department',
        'fiscal_year',
        'get_allocated',
        'get_used',
        'get_savings',
        'get_utilization',
        'snapshot_date',
        'created_by'
    ]
    list_filter = ['fiscal_year', 'department', 'snapshot_date', 'quarter']
    search_fields = ['department', 'fiscal_year', 'notes']
    readonly_fields = ['snapshot_date', 'is_archived', 'archived_at', 'archived_by']
    date_hierarchy = 'snapshot_date'
    ordering = ['-snapshot_date', 'department']

    fieldsets = (
        ('Budget Information', {
            'fields': ('budget_allocation', 'fiscal_year', 'department', 'quarter')
        }),
        ('Amounts', {
            'fields': ('allocated_amount', 'pr_used', 'ad_used', 'total_used', 'savings_amount')
        }),
        ('Metadata', {
            'fields': ('snapshot_date', 'created_by', 'notes')
        }),
        ('Archive', {
            'fields': ('is_archived', 'archived_at', 'archived_by', 'archive_reason'),
            'classes': ('collapse',)
        }),
    )

    def get_allocated(self, obj):
        """Display allocated amount with currency"""
        return f"₱{obj.allocated_amount:,.2f}"
    get_allocated.short_description = 'Allocated'
    get_allocated.admin_order_field = 'allocated_amount'

    def get_used(self, obj):
        """Display used amount with currency"""
        return f"₱{obj.total_used:,.2f}"
    get_used.short_description = 'Used'
    get_used.admin_order_field = 'total_used'

    def get_savings(self, obj):
        """Display savings amount with currency"""
        return f"₱{obj.savings_amount:,.2f}"
    get_savings.short_description = 'Savings'
    get_savings.admin_order_field = 'savings_amount'

    def get_utilization(self, obj):
        """Display utilization rate"""
        return f"{obj.utilization_rate:.1f}%"
    get_utilization.short_description = 'Utilization'


@admin.register(PRELineItemSavings)
class PRELineItemSavingsAdmin(admin.ModelAdmin):
    list_display = [
        'item_name',
        'category',
        'subcategory',
        'get_total_surplus',
        'is_significant',
        'is_procurable',
        'get_budget_snapshot',
        'created_at'
    ]
    list_filter = ['category', 'is_significant', 'is_procurable', 'created_at']
    search_fields = ['item_name', 'category', 'subcategory']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    ordering = ['-total_surplus', 'category', 'item_name']

    fieldsets = (
        ('Line Item Information', {
            'fields': ('budget_savings', 'pre_line_item', 'category', 'subcategory', 'item_name')
        }),
        ('Quarter 1 Breakdown', {
            'fields': ('q1_allocated', 'q1_consumed', 'q1_surplus')
        }),
        ('Quarter 2 Breakdown', {
            'fields': ('q2_allocated', 'q2_consumed', 'q2_surplus')
        }),
        ('Quarter 3 Breakdown', {
            'fields': ('q3_allocated', 'q3_consumed', 'q3_surplus')
        }),
        ('Quarter 4 Breakdown', {
            'fields': ('q4_allocated', 'q4_consumed', 'q4_surplus')
        }),
        ('Totals', {
            'fields': ('total_allocated', 'total_consumed', 'total_surplus')
        }),
        ('Flags', {
            'fields': ('is_procurable', 'is_significant')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )

    def get_total_surplus(self, obj):
        """Display total surplus with currency"""
        return f"₱{obj.total_surplus:,.2f}"
    get_total_surplus.short_description = 'Total Surplus'
    get_total_surplus.admin_order_field = 'total_surplus'

    def get_budget_snapshot(self, obj):
        """Display budget snapshot info"""
        return f"{obj.budget_savings.department} ({obj.budget_savings.fiscal_year})"
    get_budget_snapshot.short_description = 'Budget Snapshot'