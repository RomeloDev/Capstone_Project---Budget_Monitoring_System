import decimal
from django.db import models
from apps.users.models import User
from decimal import Decimal

# Create your models here
class PurchaseRequest(models.Model):
    PR_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('Submitted', 'Submitted'),
    ]
    
    SUBMITTED_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Partially Approved', 'Partially Approved'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    
    entity_name = models.CharField(max_length=255)
    fund_cluster = models.CharField(max_length=255, blank=True, null=True)
    office_section = models.CharField(max_length=255, blank=True, null=True)
    pr_no = models.CharField(max_length=100, unique=False, blank=True, null=True)  # Purchase Request Number
    responsibility_center_code = models.CharField(max_length=100, blank=True, null=True)
    purpose = models.TextField(blank=True, null=True)  # Program Allocation for Projects and Programs
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    pr_status = models.CharField(max_length=20, choices=PR_STATUS_CHOICES, default='draft')
    submitted_status = models.CharField(max_length=20, choices=SUBMITTED_STATUS_CHOICES, default='Pending')

    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="requested_purchases")
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_purchases")

    # New links for Budget Allocation and Source of Fund (PRE)
    budget_allocation = models.ForeignKey(
        'admin_panel.BudgetAllocation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_requests'
    )
    # Link to the PRE that is the source-of-fund, plus which item/quarter and amount
    source_pre = models.ForeignKey(
        'DepartmentPRE',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='linked_purchase_requests'
    )
    source_item_key = models.CharField(max_length=255, null=True, blank=True)
    source_quarter = models.CharField(max_length=10, null=True, blank=True)
    source_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    approved_by_approving_officer = models.BooleanField(default=False)
    approved_by_admin = models.BooleanField(default=False)
    
    # Store the original source of fund selection for display
    source_of_fund_display = models.CharField(max_length=500, null=True, blank=True)
    
    def __str__(self):
        return f"PR-{self.pr_no} ({self.entity_name})"

class PurchaseRequestItems(models.Model):
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name="items")
    stock_property_no = models.CharField(max_length=100, null=True, blank=True)
    unit = models.CharField(max_length=50, null=True, blank=True)
    item_description = models.TextField(null=True, blank=True)
    quantity = models.PositiveIntegerField(null=True, blank=True)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def save(self, *args, **kwargs):
        self.total_cost = self.quantity * self.unit_cost  # Auto-calculate total cost
        if self.purchase_request.total_amount is None:
            self.purchase_request.total_amount = Decimal('0.00')
        self.purchase_request.total_amount += self.total_cost  # Update total amount in PurchaseRequest
        self.purchase_request.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item_description} - {self.quantity} pcs"
    
class PurchaseRequestAllocation(models.Model):
    """Tracks how a purchase request is allocated across multiple PRE quarters"""
    
    purchase_request = models.ForeignKey(
        'PurchaseRequest', 
        on_delete=models.CASCADE, 
        related_name='quarter_allocations'
    )
    pre_line_item = models.ForeignKey(
        'PRELineItemBudget', 
        on_delete=models.CASCADE
    )
    allocated_amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['purchase_request', 'pre_line_item']
    
    def __str__(self):
        return f"PR {self.purchase_request.pr_no} - {self.pre_line_item.item_key} {self.pre_line_item.quarter.upper()}: ₱{self.allocated_amount}"


class Budget_Realignment(models.Model):
    SUBMITTED_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="budget_realignment_requests")
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="budget_realignment_approvals")
    target_papp = models.CharField(max_length=100)
    source_papp = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=100, choices=SUBMITTED_STATUS_CHOICES, default='pending')
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Realignment by {self.requested_by} from {self.source_papp} to {self.target_papp} - ₱{self.amount}"
    

class PRELineItemBudget(models.Model):
    """Tracks budget consumption for individual PRE line items"""
    
    pre = models.ForeignKey(
        'DepartmentPRE', 
        on_delete=models.CASCADE, 
        related_name='line_item_budgets'
    )
    item_key = models.CharField(max_length=255)  # e.g., 'travel_local'
    quarter = models.CharField(max_length=10)    # e.g., 'q1', 'q2', 'q3', 'q4'
    
    # Budget tracking
    allocated_amount = models.DecimalField(max_digits=12, decimal_places=2)
    consumed_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    reserved_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # For pending PRs
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['pre', 'item_key', 'quarter']
        
    @property
    def available_amount(self):
        return self.allocated_amount - self.consumed_amount - self.reserved_amount
    
    @property
    def remaining_amount(self):
        return self.allocated_amount - self.consumed_amount
    
    @property
    def utilization_percentage(self):
        if self.allocated_amount > 0:
            return (self.consumed_amount / self.allocated_amount) * 100
        return 0
    
    def __str__(self):
        return f"{self.pre.department} - {self.item_key} {self.quarter.upper()}: ₱{self.remaining_amount}"


class DepartmentPRE(models.Model):
    """Stores a submitted Program of Receipts and Expenditures (PRE) per department.

    We intentionally keep the structure flexible using JSON to accommodate the
    large, dynamic matrix of inputs without creating dozens of columns.
    """

    submitted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="submitted_department_pres",
    )
    department = models.CharField(max_length=255)

    # Full raw payload keyed by the input names (e.g. "basic_salary_q1", etc.)
    data = models.JSONField()

    # Signatories (free-text names provided by the user on the form)
    prepared_by_name = models.CharField(max_length=255, blank=True, null=True)
    certified_by_name = models.CharField(max_length=255, blank=True, null=True)
    approved_by_name = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    # Link to department's budget allocation so approved PREs can be tracked against budgets
    budget_allocation = models.ForeignKey(
        'admin_panel.BudgetAllocation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='department_pres'
    )

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Partially Approved', 'Partially Approved'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    approved_by_approving_officer = models.BooleanField(default=False)
    approved_by_admin = models.BooleanField(default=False)

    def __str__(self) -> str:
        dept = self.department or "Unknown Dept"
        creator = self.submitted_by.get_full_name() if self.submitted_by else "Unknown User"
        return f"PRE for {dept} by {creator} on {self.created_at:%Y-%m-%d}"
    
    def create_line_item_budgets(self):
        """Extract budget lines from JSON and create tracking records"""
        if not self.data:
            return

        for key, value in self.data.items():
            if key.endswith(('_q1', '_q2', '_q3', '_q4')):
                try:
                    # Handle empty strings, None, and whitespace
                    if value is None or str(value).strip() == '':
                        continue
                    
                    amount = Decimal(str(value).strip())
                    if amount > 0:
                        base_key, quarter = key.rsplit('_', 1)
                        PRELineItemBudget.objects.get_or_create(
                            pre=self,
                            item_key=base_key,
                            quarter=quarter,
                            defaults={'allocated_amount': amount}
                        )
                except (ValueError, TypeError, decimal.InvalidOperation, decimal.ConversionSyntax):
                    # Log the problematic data for debugging
                    print(f"Skipping invalid budget data: {key} = {repr(value)}")
                    continue
    

    
class ActivityDesign(models.Model):
    title_of_activity = models.CharField(max_length=255)
    schedule_date = models.DateField()
    venue = models.CharField(max_length=255)
    rationale = models.TextField()
    objectives = models.TextField()
    methodology = models.TextField()
    participants = models.TextField()
    resource_persons = models.TextField()
    materials_needed = models.TextField()
    evaluation_plan = models.TextField()
    status = models.CharField(max_length=50, default='Pending')
    approved_by_approving_officer = models.BooleanField(default=False)
    approved_by_admin = models.BooleanField(default=False)
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # New links for Budget Allocation and Source of Fund (PRE)
    budget_allocation = models.ForeignKey(
        'admin_panel.BudgetAllocation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_designs'
    )
    # Link to the PRE that is the source-of-fund, plus which item/quarter and amount
    source_pre = models.ForeignKey(
        'DepartmentPRE',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='linked_activity_designs'
    )
    source_item_key = models.CharField(max_length=255, null=True, blank=True)
    source_quarter = models.CharField(max_length=10, null=True, blank=True)
    source_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="activity_design_request")
    
    def __str__(self):
        return self.title_of_activity
    
class Session(models.Model):
    activity = models.ForeignKey(ActivityDesign, related_name='sessions', on_delete=models.CASCADE)
    content = models.TextField()
    order = models.PositiveIntegerField()
    
class FundsAvailable(models.Model):
    activity = models.ForeignKey(ActivityDesign, on_delete=models.CASCADE, related_name='funds_available')
    name = models.CharField(max_length=100, null=True, blank=True)
    position = models.CharField(max_length=50, null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    
class RecommendingApproval(models.Model):
    activity = models.ForeignKey(ActivityDesign, on_delete=models.CASCADE, related_name='recommending_approval')
    name = models.CharField(max_length=100, null=True, blank=True)
    position = models.CharField(max_length=50, null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    
class Signatory(models.Model):
    activity = models.ForeignKey(ActivityDesign, related_name='signatories', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    date = models.DateField(null=True, blank=True)
    
class CampusApproval(models.Model):
    activity = models.OneToOneField(ActivityDesign, related_name='campus_approval', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    date = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True, null=True)
    
class UniversityApproval(models.Model):
    activity = models.OneToOneField(ActivityDesign, related_name='university_approval', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    date = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True, null=True)