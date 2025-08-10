from django.db import models
from apps.users.models import User
from decimal import Decimal

# Create your models here
class PurchaseRequest(models.Model):
    PR_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
    ]
    
    SUBMITTED_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    entity_name = models.CharField(max_length=255)
    fund_cluster = models.CharField(max_length=255, blank=True, null=True)
    office_section = models.CharField(max_length=255, blank=True, null=True)
    pr_no = models.CharField(max_length=100, unique=True)
    responsibility_center_code = models.CharField(max_length=100, blank=True, null=True)
    purpose = models.TextField(blank=True, null=True)  # Program Allocation for Projects and Programs
    papp = models.CharField(max_length=100, default='N/A')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    pr_status = models.CharField(max_length=20, choices=PR_STATUS_CHOICES, default='draft')
    submitted_status = models.CharField(max_length=20, choices=SUBMITTED_STATUS_CHOICES, default='pending')

    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="requested_purchases")
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_purchases")
    
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
    status = models.CharField(max_length=100, choices=SUBMITTED_STATUS_CHOICES, default='Pending')
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Realignment by {self.requested_by} from {self.source_papp} to {self.target_papp} - ₱{self.amount}"


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

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
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