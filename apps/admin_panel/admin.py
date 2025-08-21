from django.contrib import admin
from unfold.admin import ModelAdmin  # 🧠 Use Unfold’s upgraded admin
from apps.admin_panel.models import Budget, BudgetAllocation, AuditTrail, ApprovedBudget

@admin.register(BudgetAllocation)
class BudgetAllocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'approved_budget', 'department', 'total_allocated', 'spent', 'allocated_at', 'updated_at')

@admin.register(ApprovedBudget)
class ApprovedBudgetAdmin(ModelAdmin):
    list_display = (
        "id",
        "title",
        "period",
        "amount",
        "remaining_budget",
        "created_at",
        "updated_at",
    )
    search_fields = ("title",)
    list_filter = ("period", "created_at")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

@admin.register(Budget)
class BudgetAdmin(ModelAdmin):
    list_display = (
        "id",
        "title",
        "total_fund",
        "remaining_budget",
        "created_at",
        "updated_at",
    )
    search_fields = ("title",)
    list_filter = ("created_at",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)


@admin.register(AuditTrail)
class AuditTrailAdmin(ModelAdmin):
    list_display = (
        "id",
        "user",
        "action",
        "model_name",
        "record_id",
        "detail",
        "ip_address",
        "timestamp",
    )
    search_fields = ("user__username", "model_name", "action")
    list_filter = ("action", "timestamp")
    date_hierarchy = "timestamp"
    ordering = ("-timestamp",)

# Register your models here.
# admin.site.register(BudgetAllocation)
# admin.site.register(Budget)