from django.db import models
from apps.users.models import User
from django.core.validators import FileExtensionValidator
from decimal import Decimal
from django.utils import timezone
import uuid
import os


def approved_budget_upload_path(instance, filename):
    """
    Segregate uploaded files by format into different folders
    Structure: approved_budgets/{year}/{file_format}/{filename}
    """
    # Get file extension
    ext = filename.split('.')[-1].lower()
    
    # Get current year
    from datetime import datetime
    year = datetime.now().year
    
    # Determine folder based on file format
    if ext == 'pdf':
        folder = 'pdf_files'
    elif ext in ['doc', 'docx']:
        folder = 'word_files'
    elif ext in ['xls', 'xlsx']:
        folder = 'excel_files'
    else:
        folder = 'other_files'
    
    # Return organized path: approved_budgets/2025/pdf_files/filename.pdf
    return f'approved_budgets/{year}/{folder}/{filename}'

def supporting_document_upload_path(instance, filename):
    """
    Segregate uploaded files by format into different folders
    Structure: approved_budgets/{fiscal_year}/{file_format}/{filename}
    """
    ext = filename.split('.')[-1].lower()
    fiscal_year = instance.approved_budget.fiscal_year
    
    # Determine folder based on file format
    if ext == 'pdf':
        folder = 'pdf_files'
    elif ext in ['doc', 'docx']:
        folder = 'word_files'
    elif ext in ['xls', 'xlsx']:
        folder = 'excel_files'
    else:
        folder = 'other_files'
    
    return f'approved_budgets/{fiscal_year}/{folder}/{filename}'


class ApprovedBudget(models.Model):
    """Stores approved budgets for specific fiscal years"""
    title = models.CharField(max_length=255)
    fiscal_year = models.CharField(max_length=10)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    remaining_budget = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField(blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Approved Budget"
        verbose_name_plural = "Approved Budgets"
        unique_together = ['fiscal_year']
    
    def __str__(self):
        return f"{self.title} ({self.fiscal_year}) - ₱{self.amount:,.2f}"
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.remaining_budget = self.amount
        super().save(*args, **kwargs)
    
    def get_documents_count(self):
        """Get total number of supporting documents"""
        return self.supporting_documents.count()
    
    def get_documents_by_format(self):
        """Group documents by file format"""
        from django.db.models import Count
        return self.supporting_documents.values('file_format').annotate(
            count=Count('id')
        ).order_by('file_format')


class SupportingDocument(models.Model):
    """Stores multiple supporting documents for each approved budget"""
    approved_budget = models.ForeignKey(
        ApprovedBudget, 
        on_delete=models.CASCADE, 
        related_name='supporting_documents'
    )
    
    document = models.FileField(
        upload_to=supporting_document_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'docx', 'doc', 'xlsx', 'xls'])],
        help_text="Supporting document (PDF, Word, Excel)"
    )
    
    file_name = models.CharField(max_length=255)
    file_format = models.CharField(max_length=10, editable=False)
    file_size = models.BigIntegerField(help_text="File size in bytes", editable=False)
    
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Supporting Document"
        verbose_name_plural = "Supporting Documents"
    
    def __str__(self):
        return f"{self.file_name} ({self.file_format.upper()})"
    
    def save(self, *args, **kwargs):
        # Auto-detect file format and size
        if self.document:
            self.file_format = self.document.name.split('.')[-1].lower()
            self.file_size = self.document.size
            if not self.file_name:
                self.file_name = self.document.name
        super().save(*args, **kwargs)
    
    def get_file_size_display(self):
        """Return human-readable file size"""
        size = self.file_size
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.2f} KB"
        else:
            return f"{size / (1024 * 1024):.2f} MB"
    
    def get_file_icon_color(self):
        """Return Tailwind color class based on file format"""
        colors = {
            'pdf': 'red',
            'doc': 'blue',
            'docx': 'blue',
            'xls': 'green',
            'xlsx': 'green',
        }
        return colors.get(self.file_format, 'gray')


class BudgetAllocation(models.Model):
    """Budget allocations distributed to departments from approved budgets"""
    approved_budget = models.ForeignKey(ApprovedBudget, on_delete=models.CASCADE, related_name='allocations')
    department = models.CharField(max_length=255)
    end_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budget_allocations')
    allocated_amount = models.DecimalField(max_digits=15, decimal_places=2)
    remaining_balance = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Track different types of requests
    pre_amount_used = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    pr_amount_used = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    ad_amount_used = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    allocated_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['approved_budget', 'end_user']
        ordering = ['department', 'end_user']
        verbose_name = "Budget Allocation"
        verbose_name_plural = "Budget Allocations"
    
    def __str__(self):
        return f"{self.department} - {self.end_user.get_full_name()} (₱{self.allocated_amount:,.2f})"
    
    def get_total_used(self):
        """Calculate total amount used across all request types"""
        return self.pre_amount_used + self.pr_amount_used + self.ad_amount_used
    
    def update_remaining_balance(self):
        """Update remaining balance based on approved requests"""
        self.remaining_balance = self.allocated_amount - self.get_total_used()
        self.save()


class DepartmentPRE(models.Model):
    """Program of Receipts and Expenditures with complete workflow support"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic info
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="submitted_pres")
    department = models.CharField(max_length=255)
    program = models.CharField(max_length=255, null=True, blank=True)
    fund_source = models.CharField(max_length=100, null=True, blank=True)
    fiscal_year = models.CharField(max_length=10)
    
    # Link to budget allocation - CRITICAL for validation
    budget_allocation = models.ForeignKey(
        BudgetAllocation,
        on_delete=models.CASCADE,
        related_name='pres',
        help_text="Must be linked to specific budget allocation"
    )
    
    # File uploads
    uploaded_excel_file = models.FileField(
        upload_to='pre_uploads/%Y/%m/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['xlsx', 'xls'])],
        help_text="Upload PRE Excel file"
    )
    
    # Status workflow
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Pending', 'Pending Review'),
        ('Partially Approved', 'Partially Approved'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    
    # Validation
    is_valid = models.BooleanField(default=False)
    validation_errors = models.JSONField(default=dict, blank=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Workflow files
    partially_approved_pdf = models.FileField(
        upload_to='pre_pdfs/%Y/%m/',
        null=True,
        blank=True,
        help_text="PDF generated when partially approved for printing"
    )
    
    final_approved_scan = models.FileField(
        upload_to='pre_scanned/%Y/%m/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
        help_text="Scanned copy of signed printed PRE"
    )
    
    # Signatories
    prepared_by_name = models.CharField(max_length=255, blank=True)
    certified_by_name = models.CharField(max_length=255, blank=True)
    approved_by_name = models.CharField(max_length=255, blank=True)
    
    # Timestamps for workflow tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    partially_approved_at = models.DateTimeField(null=True, blank=True)
    final_approved_at = models.DateTimeField(null=True, blank=True)
    
    # Admin notes
    admin_notes = models.TextField(blank=True, help_text="Admin notes during review")
    rejection_reason = models.TextField(blank=True)
    
    # Status workflow fields
    submitted_at = models.DateTimeField(null=True, blank=True)
    partially_approved_at = models.DateTimeField(null=True, blank=True)
    final_approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Department PRE"
        verbose_name_plural = "Department PREs"
    
    def __str__(self):
        return f"PRE-{self.id.hex[:8]} - {self.department} ({self.status})"
    
    def validate_against_budget(self):
        """Validate PRE total against allocated budget"""
        errors = []
        
        if not self.budget_allocation:
            errors.append("PRE must be linked to a budget allocation")
            
        if self.total_amount > self.budget_allocation.remaining_balance:
            errors.append(f"PRE total (₱{self.total_amount:,.2f}) exceeds remaining budget (₱{self.budget_allocation.remaining_balance:,.2f})")
        
        # Additional validations
        if self.total_amount <= 0:
            errors.append("PRE total amount must be greater than zero")
            
        return errors
    
    def can_be_submitted(self):
        """Check if PRE can be submitted"""
        validation_errors = self.validate_against_budget()
        return len(validation_errors) == 0
    
    def submit_for_review(self):
        """Submit PRE for admin review"""
        if self.can_be_submitted():
            self.status = 'Pending'
            self.submitted_at = timezone.now()
            self.save()
            return True
        return False


class PurchaseRequest(models.Model):
    """Purchase Request for procurement items"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="purchase_requests")
    budget_allocation = models.ForeignKey(BudgetAllocation, on_delete=models.CASCADE, related_name='purchase_requests')
    
    # PR Details
    pr_number = models.CharField(max_length=50, unique=True, blank=True)
    department = models.CharField(max_length=255)
    purpose = models.TextField()
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    # File uploads
    uploaded_document = models.FileField(
        upload_to='pr_uploads/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['docx', 'doc'])],
        help_text="Upload Purchase Request document (.docx format)"
    )
    
    # Status and workflow (same as PRE)
    STATUS_CHOICES = DepartmentPRE.STATUS_CHOICES
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    
    # Workflow files
    partially_approved_pdf = models.FileField(upload_to='pr_pdfs/%Y/%m/', null=True, blank=True)
    final_approved_scan = models.FileField(upload_to='pr_scanned/%Y/%m/', null=True, blank=True)
    
    # Validation
    is_valid = models.BooleanField(default=False)
    validation_errors = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    partially_approved_at = models.DateTimeField(null=True, blank=True)
    final_approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Purchase Request"
        verbose_name_plural = "Purchase Requests"
    
    def __str__(self):
        return f"PR-{self.pr_number or self.id.hex[:8]} - {self.department}"


class ActivityDesign(models.Model):
    """Activity Design for non-procurement requests"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activity_designs")
    budget_allocation = models.ForeignKey(BudgetAllocation, on_delete=models.CASCADE, related_name='activity_designs')
    
    # AD Details
    ad_number = models.CharField(max_length=50, unique=True, blank=True)
    department = models.CharField(max_length=255)
    activity_title = models.CharField(max_length=255)
    activity_description = models.TextField()
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    # File uploads
    uploaded_document = models.FileField(
        upload_to='ad_uploads/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['docx', 'doc'])],
        help_text="Upload Activity Design document (.docx format)"
    )
    
    # Status and workflow (same as PRE)
    STATUS_CHOICES = DepartmentPRE.STATUS_CHOICES
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    
    # Workflow files
    partially_approved_pdf = models.FileField(upload_to='ad_pdfs/%Y/%m/', null=True, blank=True)
    final_approved_scan = models.FileField(upload_to='ad_scanned/%Y/%m/', null=True, blank=True)
    
    # Validation
    is_valid = models.BooleanField(default=False)
    validation_errors = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    partially_approved_at = models.DateTimeField(null=True, blank=True)
    final_approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Activity Design"
        verbose_name_plural = "Activity Designs"
    
    def __str__(self):
        return f"AD-{self.ad_number or self.id.hex[:8]} - {self.activity_title}"


# PRE Category and Line Item models (from previous version)
class PRECategory(models.Model):
    """Budget categories (Personnel Services, MOOE, Capital Outlays)"""
    CATEGORY_TYPES = [
        ('PERSONNEL', 'Personnel Services'),
        ('MOOE', 'Maintenance and Other Operating Expenses'),
        ('CAPITAL', 'Capital Outlays'),
    ]
    
    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES)
    code = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = "PRE Category"
        verbose_name_plural = "PRE Categories"
    
    def __str__(self):
        return f"{self.name} ({self.category_type})"


class PRESubCategory(models.Model):
    """Sub-categories within main categories"""
    category = models.ForeignKey(PRECategory, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = "PRE Sub-Category"
        verbose_name_plural = "PRE Sub-Categories"
        unique_together = ['category', 'code']
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"


class PRELineItem(models.Model):
    """Individual budget line items for PRE"""
    pre = models.ForeignKey(DepartmentPRE, on_delete=models.CASCADE, related_name='line_items')
    category = models.ForeignKey(PRECategory, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(PRESubCategory, on_delete=models.CASCADE, null=True, blank=True)
    
    # Line item details
    item_name = models.CharField(max_length=255)
    item_code = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    
    # Quarterly amounts
    q1_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    q2_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    q3_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    q4_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    # Additional fields
    is_procurable = models.BooleanField(default=False)
    procurement_method = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        ordering = ['category__sort_order', 'subcategory__sort_order', 'item_name']
    
    def __str__(self):
        return f"{self.item_name} - {self.pre.department}"
    
    def get_total(self):
        return (self.q1_amount or 0) + (self.q2_amount or 0) + (self.q3_amount or 0) + (self.q4_amount or 0)


class PREReceipt(models.Model):
    """Budget receipts/income for PRE"""
    pre = models.ForeignKey(DepartmentPRE, on_delete=models.CASCADE, related_name='receipts')
    receipt_type = models.CharField(max_length=100)
    
    # Quarterly amounts
    q1_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    q2_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    q3_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    q4_amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    
    def get_total(self):
        return (self.q1_amount or 0) + (self.q2_amount or 0) + (self.q3_amount or 0) + (self.q4_amount or 0)


class RequestApproval(models.Model):
    """Generic approval tracking for all request types"""
    CONTENT_TYPE_CHOICES = [
        ('pre', 'PRE'),
        ('pr', 'Purchase Request'),
        ('ad', 'Activity Design'),
    ]
    
    # Generic foreign key setup
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPE_CHOICES)
    object_id = models.UUIDField()
    
    # Approval details
    approved_by = models.ForeignKey(User, on_delete=models.CASCADE)
    approval_level = models.CharField(max_length=50)  # 'partial' or 'final'
    approved_at = models.DateTimeField(auto_now_add=True)
    comments = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-approved_at']
        unique_together = ['content_type', 'object_id', 'approved_by', 'approval_level']


class SystemNotification(models.Model):
    """Notifications for users about request status changes"""
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Link to related request
    content_type = models.CharField(max_length=10, choices=RequestApproval.CONTENT_TYPE_CHOICES)
    object_id = models.UUIDField()
    
    # Status
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

