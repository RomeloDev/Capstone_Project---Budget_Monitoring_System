from django.contrib import admin
from unfold.admin import ModelAdmin  # 🧠 Use Unfold’s upgraded admin
from apps.admin_panel.models import Budget, BudgetAllocation, AuditTrail

@admin.register(BudgetAllocation)
class BudgetAllocationAdmin(ModelAdmin):
    list_display = (
        "id",
        "department",
        "papp",
        "total_allocated",
        "spent",
        "remaining_budget",
        "assigned_user",
        "allocated_at",
        "updated_at",
    )
    search_fields = ("papp", "assigned_user__username", "department")
    list_filter = ("department", "allocated_at", "updated_at")
    date_hierarchy = "allocated_at"
    ordering = ("-allocated_at",)
    list_per_page = 25


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
        "department",
        "action",
        "description",
        "timestamp",
    )
    search_fields = ("user__username", "department", "action", "description")
    list_filter = ("action", "department", "timestamp")
    date_hierarchy = "timestamp"
    ordering = ("-timestamp",)
    list_per_page = 50

# Register your models here.
# admin.site.register(BudgetAllocation)
# admin.site.register(Budget)