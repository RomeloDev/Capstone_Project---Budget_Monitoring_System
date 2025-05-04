from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.users.models import User  # Assuming you have a custom User model

# Create your models here.
class BudgetAllocation(models.Model):
    DEPARTMENTS = [
        ('instruction', 'Instruction'),
        ('research_ext', 'Research & Extension'),
        ('sports', 'Sports')
    ]
    
    department = models.CharField(max_length=100)
    papp = models.CharField(max_length=100, unique=True)  # PAPP - Program Allocation for Projects and Programs
    total_allocated = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    remaining_budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    assigned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Connect to your custom User model
        on_delete=models.CASCADE,  # Delete budget if user is deleted
        related_name="budget",  # User can access their budget with `user.budget`
        null=True, blank=True  # Optional, in case a budget is not yet assigned
    )
    
    allocated_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_department_display()} - {self.assigned_user.username if self.assigned_user else 'Unassigned'}"
    
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