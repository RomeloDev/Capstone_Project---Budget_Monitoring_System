from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.users.models import User  # Assuming you have a custom User model

# Create your models here.    
class Budget(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    total_fund = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    remaining_budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)


class AuditTrail(models.Model):
    ACTION_TYPES = [
        ("LOGIN", "Login"),
        ("LOGOUT", "Logout"),
        ("APPROVED", "Approved Request"),
        ("DENIED", "Denied Request"),
        ("REALIGN", "Realignment Submitted"),
        ("ALLOCATE", "Budget Allocated"),
        ("ADD_FUNDS", "Institutional Fund Added"),
        # Add more as needed
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']  # Most recent first

    def __str__(self):
        return f"{self.user.username} - {self.action} at {self.timestamp}"
    
class ApprovedBudget(models.Model):
    PERIOD_CHOICES = [
        ('Q1', 'Q1'),
        ('Q2', 'Q2'),
        ('Q3', 'Q3'),
        ('Q4', 'Q4'),
        ('Full Year', 'Full Year'),
    ]
    
    title = models.CharField(max_length=255)
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.period}"
    
    @property
    def remaining_budget(self):
        from django.db.models import Sum
        total_allocated = self.allocations.aggregate(total=Sum('total_allocated'))['total'] or 0
        return self.amount - total_allocated
    
class BudgetAllocation(models.Model):
    department = models.CharField(max_length=255)
    approved_budget = models.ForeignKey(ApprovedBudget, on_delete=models.CASCADE, related_name='allocations')
    total_allocated = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    spent = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    allocated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def remaining_budget(self):
        return self.total_allocated - self.spent

    def __str__(self):
        return f"{self.department} - {self.approved_budget.title}"