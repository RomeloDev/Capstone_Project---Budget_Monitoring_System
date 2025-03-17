from django.db import models
from apps.users.models import User

# Create your models here.
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
    fund_cluster = models.CharField(max_length=255, default=None)
    office_section = models.CharField(max_length=255, default=None)
    pr_no = models.CharField(max_length=100, unique=True, default=None)
    responsibility_center_code = models.CharField(max_length=100, default=None)
    purpose = models.TextField(default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    pr_status = models.CharField(max_length=20, choices=PR_STATUS_CHOICES, default='draft')
    submitted_status = models.CharField(max_length=20, choices=SUBMITTED_STATUS_CHOICES, default='pending')
    
class PurchaseRequestItems(models.Model):
    pass
    