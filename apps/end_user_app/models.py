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