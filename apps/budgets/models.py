# bb_budget_monitoring_system/apps/budgets/models.py
from django.db import models
from apps.users.models import User
from django.core.validators import FileExtensionValidator
from decimal import Decimal
from django.utils import timezone
import uuid
import os
from django.conf import settings
from .managers import ArchiveManager

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
    amount = models.DecimalField(max_digits=15, decimal_places=6)
    remaining_budget = models.DecimalField(max_digits=15, decimal_places=6)
    description = models.TextField(blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    # Archive fields
    is_archived = models.BooleanField(default=False, db_index=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='archived_approved_budgets'
    )
    archive_reason = models.TextField(blank=True)
    ARCHIVE_TYPE_CHOICES = [
        ('FISCAL_YEAR', 'Fiscal Year Archive'),
        ('MANUAL', 'Manual Archive/Delete'),
    ]
    archive_type = models.CharField(
        max_length=20,
        choices=ARCHIVE_TYPE_CHOICES,
        default='FISCAL_YEAR',
        blank=True
    )

    # Managers
    objects = ArchiveManager()  # Default: excludes archived
    all_objects = models.Manager()  # Fallback: includes everything

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
        'ApprovedBudget', 
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
    approved_budget = models.ForeignKey('ApprovedBudget', on_delete=models.CASCADE, related_name='allocations')
    department = models.CharField(max_length=255)
    end_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budget_allocations')
    allocated_amount = models.DecimalField(max_digits=15, decimal_places=6)
    remaining_balance = models.DecimalField(max_digits=15, decimal_places=6)

    # Track different types of requests
    pre_amount_used = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal('0.00'))
    pr_amount_used = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal('0.00'))
    ad_amount_used = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal('0.00'))

    allocated_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    # Archive fields
    is_archived = models.BooleanField(default=False, db_index=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='archived_budget_allocations'
    )
    archive_reason = models.TextField(blank=True)
    archive_type = models.CharField(
        max_length=20,
        choices=ApprovedBudget.ARCHIVE_TYPE_CHOICES,
        default='FISCAL_YEAR',
        blank=True
    )

    # Managers
    objects = ArchiveManager()  # Default: excludes archived
    all_objects = models.Manager()  # Fallback: includes everything

    class Meta:
        unique_together = ['approved_budget', 'end_user']
        ordering = ['department', 'end_user']
        verbose_name = "Budget Allocation"
        verbose_name_plural = "Budget Allocations"

    def __str__(self):
        return f"{self.department} - {self.end_user.get_full_name()} (₱{self.allocated_amount:,.2f})"
    
    def get_total_used(self):
        """Calculate total amount used (PR and AD only, excluding PRE)"""
        return self.pr_amount_used + self.ad_amount_used

    def update_remaining_balance(self):
        """Update remaining balance based on approved requests"""
        self.remaining_balance = self.allocated_amount - self.get_total_used()
        self.save()

    def get_pre_approved_total(self):
        """
        Get total amount from approved PRE grand total.
        This is the amount that was approved for spending based on the PRE.

        Returns:
            Decimal: Total from approved PRE, or 0 if no approved PRE exists

        Phase 5: New PRE Workflow - Budget monitoring based on PRE grand total
        """
        from django.db.models import Sum

        # Get approved PRE for this allocation
        approved_pre = self.pres.filter(status='Approved').first()

        if approved_pre:
            return approved_pre.total_amount

        return Decimal('0.00')

    def get_available_pre_budget(self):
        """
        Get available budget based on approved PRE grand total minus PR/AD usage.

        This is the recommended way to calculate available budget in the new workflow:
        - Budget comes from PRE grand total (not full allocation)
        - PR and AD requests consume this PRE budget

        Returns:
            Decimal: Available budget from PRE

        Phase 5: New PRE Workflow - Budget monitoring based on PRE grand total
        """
        pre_total = self.get_pre_approved_total()

        if pre_total == Decimal('0.00'):
            # No approved PRE - fall back to allocated amount
            return self.remaining_balance

        # PRE approved - calculate based on PRE total minus PR/AD usage
        return pre_total - self.get_total_used()

    def has_approved_pre(self):
        """
        Check if this allocation has an approved PRE.

        Returns:
            bool: True if approved PRE exists, False otherwise

        Phase 5: New PRE Workflow
        """
        return self.pres.filter(status='Approved').exists()


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
        ('Awaiting Admin Verification', 'Awaiting Admin Verification'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Draft')
    
    # Validation
    is_valid = models.BooleanField(default=False)
    validation_errors = models.JSONField(default=dict, blank=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal('0.00'))
    
    # Workflow files
    partially_approved_pdf = models.FileField(
        upload_to='pre_pdfs/%Y/%m/',
        null=True,
        blank=True,
        help_text="PDF generated from database when partially approved (includes custom line items)"
    )

    original_excel_pdf = models.FileField(
        upload_to='pre_pdfs/%Y/%m/',
        null=True,
        blank=True,
        help_text="PDF converted from original uploaded Excel file (preserved snapshot)"
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

    # NEW FIELDS FOR END USER DOCUMENT UPLOAD WORKFLOW
    awaiting_verification = models.BooleanField(
        default=False,
        help_text="True when end user has uploaded signed documents, awaiting admin verification"
    )
    end_user_uploaded_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when end user uploaded signed documents"
    )

    # NEW FIELDS FOR ADMIN APPROVAL FLOW
    approved_documents = models.FileField(
        upload_to='pre_approved_docs/%Y/%m/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']
        )],
        help_text="Scanned approved documents uploaded by admin"
    )
    
    admin_approved_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Timestamp when admin uploaded approved documents"
    )
    
    admin_approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='admin_approved_pres',
        help_text="Admin who uploaded the approved documents"
    )
    
    # Archive fields
    is_archived = models.BooleanField(default=False, db_index=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='archived_department_pres'
    )
    archive_reason = models.TextField(blank=True)
    archive_type = models.CharField(
        max_length=20,
        choices=[
            ('FISCAL_YEAR', 'Fiscal Year Archive'),
            ('MANUAL', 'Manual Archive/Delete'),
        ],
        default='FISCAL_YEAR',
        blank=True
    )

    # Managers
    objects = ArchiveManager()  # Default: excludes archived
    all_objects = models.Manager()  # Fallback: includes everything

    # Helper methods
    def can_upload_approved_docs(self):
        """Check if admin can upload approved documents"""
        return self.status == 'Partially Approved'

    def approve_with_documents(self, admin_user):
        """Final approval after document upload"""
        was_already_approved = self.status == 'Approved'
        
        self.status = 'Approved'
        self.final_approved_at = timezone.now()
        self.admin_approved_by = admin_user
        self.admin_approved_at = timezone.now()
        
        # Update budget allocation
        if self.budget_allocation and not was_already_approved:
            # Calculate correct total from line items
            correct_total = sum(item.get_total() for item in self.line_items.all())
            
            # Update PRE total_amount if it doesn't match
            if self.total_amount != correct_total:
                print(f"⚠️ PRE total mismatch detected! Correcting: ₱{self.total_amount:,.2f} → ₱{correct_total:,.2f}")
                self.total_amount = correct_total
            
            # Update allocation with correct total
            self.budget_allocation.pre_amount_used += correct_total
            self.budget_allocation.update_remaining_balance()
            
        self.save()
    
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
    
    def get_total_remaining(self):
        """Calculate total remaining budget across all line items and quarters"""
        total_remaining = Decimal('0')
        for line_item in self.line_items.all():
            for quarter in ['Q1', 'Q2', 'Q3', 'Q4']:
                total_remaining += line_item.get_quarter_available(quarter)
        return total_remaining
    
    @property
    def total_consumed(self):
        """Calculate total consumed from all line items across all quarters"""
        from django.db.models import Sum
        from django.db.models.functions import Coalesce
        
        # Get all PR allocations for this PRE
        pr_consumed = PurchaseRequestAllocation.objects.filter(
            pre_line_item__pre=self,
            purchase_request__status__in=['Pending', 'Partially Approved', 'Approved']
        ).aggregate(
            total=Coalesce(Sum('allocated_amount'), Decimal('0.00'))
        )['total']
        
        # Get all AD allocations for this PRE
        ad_consumed = ActivityDesignAllocation.objects.filter(
            pre_line_item__pre=self,
            activity_design__status__in=['Pending', 'Partially Approved', 'Approved']
        ).aggregate(
            total=Coalesce(Sum('allocated_amount'), Decimal('0.00'))
        )['total']
        
        return pr_consumed + ad_consumed

    @property
    def total_remaining(self):
        """Calculate total remaining budget"""
        return self.total_amount - self.total_consumed


class PurchaseRequest(models.Model):
    """Purchase Request for procurement items"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic Info
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='purchase_requests'
    )
    department = models.CharField(max_length=255)
    pr_number = models.CharField(max_length=50, unique=True)
    
    # Budget Linkage
    budget_allocation = models.ForeignKey(
        'BudgetAllocation',
        on_delete=models.CASCADE,
        related_name='purchase_requests'
    )
    
    # PRE Line Item Linkage (NEW)
    source_pre = models.ForeignKey(
        'DepartmentPRE',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_requests',
        help_text='Source PRE document'
    )
    source_line_item = models.ForeignKey(
        'PRELineItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_requests',
        help_text='Specific PRE line item used for funding'
    )
    source_of_fund_display = models.CharField(
        max_length=500,
        blank=True,
        help_text='Human-readable source of fund description'
    )
    
    # PR Details
    purpose = models.TextField()
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        default=Decimal('0.00')
    )
    
    # Optional Fields (for form-based PR)
    entity_name = models.CharField(max_length=255, blank=True)
    fund_cluster = models.CharField(max_length=100, blank=True)
    office_section = models.CharField(max_length=255, blank=True)
    responsibility_center_code = models.CharField(max_length=100, blank=True)
    
    # File Upload (for upload-based PR)
    uploaded_document = models.FileField(
        upload_to='pr_documents/%Y/%m/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['docx', 'doc', 'pdf'])],
        help_text="Uploaded PR document"
    )
    
    # Status Workflow
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Pending', 'Pending Review'),
        ('Partially Approved', 'Partially Approved'),
        ('Awaiting Admin Verification', 'Awaiting Admin Verification'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='Draft'
    )
    
    # Workflow Files
    partially_approved_pdf = models.FileField(
        upload_to='pr/partially_approved_pdfs/',
        null=True,
        blank=True,
        help_text="Auto-generated PDF when admin partially approves"
    )
    
    approved_documents = models.FileField(
        upload_to='pr/approved_documents/',
        null=True,
        blank=True,
        help_text="Scanned signed copy uploaded by admin"
    )
    
    final_approved_scan = models.FileField(
        upload_to='pr_scanned/%Y/%m/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
        help_text="Scanned copy of signed PR"
    )
    
    # Validation
    is_valid = models.BooleanField(default=False)
    validation_errors = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    partially_approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When admin partially approved"
    )
    final_approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When admin uploaded signed copy (full approval)"
    )
    
    # Admin notes
    admin_notes = models.TextField(
        blank=True,
        help_text="Admin notes when uploading signed copy"
    )
    rejection_reason = models.TextField(blank=True)

    # New Workflow Fields (Phase 4b - similar to PRE workflow)
    awaiting_verification = models.BooleanField(
        default=False,
        help_text="True when PR is awaiting admin verification of signed documents"
    )
    end_user_uploaded_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When end user uploaded signed documents"
    )
    admin_approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pr_final_approvals',
        help_text="Admin who gave final approval"
    )
    admin_approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When admin gave final approval after verification"
    )
    original_pr_pdf = models.FileField(
        upload_to='pr_original_pdfs/%Y/%m/',
        null=True,
        blank=True,
        help_text="PDF of original PR with BISU header (generated on partial approval)"
    )

    # Archive fields
    is_archived = models.BooleanField(default=False, db_index=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='archived_purchase_requests'
    )
    archive_reason = models.TextField(blank=True)
    archive_type = models.CharField(
        max_length=20,
        choices=[
            ('FISCAL_YEAR', 'Fiscal Year Archive'),
            ('MANUAL', 'Manual Archive/Delete'),
        ],
        default='FISCAL_YEAR',
        blank=True
    )

    # Managers
    objects = ArchiveManager()  # Default: excludes archived
    all_objects = models.Manager()  # Fallback: includes everything

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Purchase Request"
        verbose_name_plural = "Purchase Requests"

    def __str__(self):
        return f"PR-{self.pr_number} - {self.department} (₱{self.total_amount:,.2f})"
    
    def get_allocated_line_items(self):
        """Get all PRE line items allocated to this PR"""
        return self.pre_allocations.select_related(
            'pre_line_item__category',
            'pre_line_item__subcategory',
            'pre_line_item__pre'
        )
    
    def get_total_allocated_from_pre(self):
        """Calculate total allocated from PRE line items"""
        from django.db.models import Sum
        result = self.pre_allocations.aggregate(
            total=Sum('allocated_amount')
        )
        return result['total'] or Decimal('0.00')
    
    def validate_against_budget(self):
        """Validate PR total against allocated budget"""
        errors = []

        if not self.budget_allocation:
            errors.append("PR must be linked to a budget allocation")
            return errors

        if not self.source_line_item:
            errors.append("PR must have a PRE line item as funding source")

        if self.total_amount <= 0:
            errors.append("PR total amount must be greater than zero")

        # Check if approving this PR would exceed the budget allocation
        allocation = self.budget_allocation

        # Calculate current used amount (excluding this PR if it's already approved)
        current_pr_used = allocation.pr_amount_used
        if self.status == 'Approved':
            # Subtract this PR's amount if already counted
            current_pr_used -= self.total_amount

        # Calculate what the new total would be
        new_pr_total = current_pr_used + self.total_amount
        new_total_used = new_pr_total + allocation.ad_amount_used

        # Check against allocated amount
        if new_total_used > allocation.allocated_amount:
            available = allocation.allocated_amount - (allocation.pr_amount_used + allocation.ad_amount_used)
            if self.status == 'Approved':
                available += self.total_amount  # Add back this PR's current amount
            errors.append(
                f"PR amount (₱{self.total_amount:,.2f}) would exceed available budget. "
                f"Available: ₱{available:,.2f}"
            )

        return errors

    def validate_quarterly_limits(self):
        """
        Validate that PR allocations don't exceed quarterly budgets in PRE line items.
        This prevents front-loading spending in early quarters.
        """
        errors = []

        # Get all allocations for this PR
        allocations = self.allocations.all()

        if not allocations.exists():
            errors.append("PR has no allocations to validate")
            return errors

        # Group allocations by PRE line item and quarter
        quarter_usage = {}

        for allocation in allocations:
            line_item = allocation.pre_line_item
            quarter = allocation.quarter

            if not line_item or not quarter:
                continue

            key = (line_item.id, quarter)

            if key not in quarter_usage:
                quarter_usage[key] = {
                    'line_item': line_item,
                    'quarter': quarter,
                    'pr_amount': Decimal('0.00')
                }

            quarter_usage[key]['pr_amount'] += allocation.allocated_amount

        # Validate each quarter's usage
        for key, data in quarter_usage.items():
            line_item = data['line_item']
            quarter = data['quarter']
            pr_amount = data['pr_amount']

            # Get the budgeted amount for this quarter
            quarter_budget = line_item.get_quarter_amount(quarter)

            # Get currently consumed amount for this quarter (including other PRs and ADs)
            quarter_consumed = line_item.get_quarter_consumed(quarter)

            # If this PR is already approved, subtract its current contribution
            if self.status == 'Approved':
                # Find this PR's current allocation for this quarter
                current_allocation = allocations.filter(
                    pre_line_item=line_item,
                    quarter=quarter
                ).aggregate(total=Sum('allocated_amount'))['total'] or Decimal('0.00')
                quarter_consumed -= current_allocation

            # Calculate what would be consumed after adding this PR
            new_quarter_consumed = quarter_consumed + pr_amount

            # Check if it exceeds the quarterly budget
            if new_quarter_consumed > quarter_budget:
                available = quarter_budget - quarter_consumed
                errors.append(
                    f"PR allocation of ₱{pr_amount:,.2f} to {quarter} exceeds available quarterly budget for '{line_item.category}'. "
                    f"Quarter budget: ₱{quarter_budget:,.2f}, Already consumed: ₱{quarter_consumed:,.2f}, Available: ₱{available:,.2f}"
                )

        return errors


class PurchaseRequestItem(models.Model):
    """Individual items in a Purchase Request (for form-based PR)"""
    purchase_request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.CASCADE,
        related_name='items'
    )
    stock_property_no = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=50)
    item_description = models.TextField()
    quantity = models.IntegerField()
    unit_cost = models.DecimalField(max_digits=15, decimal_places=2)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    
    def save(self, *args, **kwargs):
        self.total_cost = self.quantity * self.unit_cost
        super().save(*args, **kwargs)
        
        # Update parent PR total
        self.purchase_request.total_amount = sum(
            item.total_cost for item in self.purchase_request.items.all()
        )
        self.purchase_request.save()
    
    def __str__(self):
        return f"{self.item_description} (x{self.quantity})"


class ActivityDesign(models.Model):
    """Activity Design for non-procurement requests"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activity_designs")
    budget_allocation = models.ForeignKey(BudgetAllocation, on_delete=models.CASCADE, related_name='activity_designs')

    # AD Details
    ad_number = models.CharField(max_length=50, unique=True, blank=True)
    department = models.CharField(max_length=255)
    activity_title = models.CharField(max_length=255, blank=True)
    activity_description = models.TextField(blank=True)
    purpose = models.TextField(blank=True, help_text="Purpose/justification for this activity")
    total_amount = models.DecimalField(max_digits=15, decimal_places=6)

    # File uploads
    uploaded_document = models.FileField(
        upload_to='ad_uploads/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['docx', 'doc'])],
        help_text="Upload Activity Design document (.docx format)"
    )

    # Status and workflow (same as PRE)
    STATUS_CHOICES = DepartmentPRE.STATUS_CHOICES
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Draft')

    # Workflow files
    partially_approved_pdf = models.FileField(upload_to='ad_pdfs/%Y/%m/', null=True, blank=True)
    final_approved_scan = models.FileField(upload_to='ad_scanned/%Y/%m/', null=True, blank=True)

    # Approval tracking
    approved_documents = models.FileField(
        upload_to='ad_approved_docs/%Y/%m/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']
        )],
        help_text="Scanned approved documents uploaded by admin"
    )

    admin_approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when admin uploaded approved documents"
    )

    admin_approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='admin_approved_ads',
        help_text="Admin who uploaded the approved documents"
    )

    # Validation
    is_valid = models.BooleanField(default=False)
    validation_errors = models.JSONField(default=dict, blank=True)

    # Admin notes
    admin_notes = models.TextField(blank=True, help_text="Admin notes during review")
    rejection_reason = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    partially_approved_at = models.DateTimeField(null=True, blank=True)
    final_approved_at = models.DateTimeField(null=True, blank=True)

    # Archive fields
    is_archived = models.BooleanField(default=False, db_index=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='archived_activity_designs'
    )
    archive_reason = models.TextField(blank=True)
    archive_type = models.CharField(
        max_length=20,
        choices=[
            ('FISCAL_YEAR', 'Fiscal Year Archive'),
            ('MANUAL', 'Manual Archive/Delete'),
        ],
        default='FISCAL_YEAR',
        blank=True
    )

    # Managers
    objects = ArchiveManager()  # Default: excludes archived
    all_objects = models.Manager()  # Fallback: includes everything

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Activity Design"
        verbose_name_plural = "Activity Designs"

    def __str__(self):
        return f"AD-{self.ad_number or self.id.hex[:8]} - {self.activity_title or 'Untitled'}"

    def get_allocated_line_items(self):
        """Get all PRE line items allocated to this AD"""
        return self.pre_allocations.select_related(
            'pre_line_item__category',
            'pre_line_item__subcategory',
            'pre_line_item__pre'
        )

    def get_total_allocated_from_pre(self):
        """Calculate total allocated from PRE line items"""
        from django.db.models import Sum
        result = self.pre_allocations.aggregate(
            total=Sum('allocated_amount')
        )
        return result['total'] or Decimal('0.00')

    def validate_against_budget(self):
        """Validate AD total against allocated budget"""
        errors = []

        if not self.budget_allocation:
            errors.append("AD must be linked to a budget allocation")
            return errors

        if self.total_amount <= 0:
            errors.append("AD total amount must be greater than zero")

        # Check if approving this AD would exceed the budget allocation
        allocation = self.budget_allocation

        # Calculate current used amount (excluding this AD if it's already approved)
        current_ad_used = allocation.ad_amount_used
        if self.status == 'Approved':
            # Subtract this AD's amount if already counted
            current_ad_used -= self.total_amount

        # Calculate what the new total would be
        new_ad_total = current_ad_used + self.total_amount
        new_total_used = allocation.pr_amount_used + new_ad_total

        # Check against allocated amount
        if new_total_used > allocation.allocated_amount:
            available = allocation.allocated_amount - (allocation.pr_amount_used + allocation.ad_amount_used)
            if self.status == 'Approved':
                available += self.total_amount  # Add back this AD's current amount
            errors.append(
                f"AD amount (₱{self.total_amount:,.2f}) would exceed available budget. "
                f"Available: ₱{available:,.2f}"
            )

        return errors

    def validate_quarterly_limits(self):
        """
        Validate that AD allocations don't exceed quarterly budgets in PRE line items.
        This prevents front-loading spending in early quarters.
        """
        errors = []

        # Get all allocations for this AD
        allocations = self.allocations.all()

        if not allocations.exists():
            errors.append("AD has no allocations to validate")
            return errors

        # Group allocations by PRE line item and quarter
        quarter_usage = {}

        for allocation in allocations:
            line_item = allocation.pre_line_item
            quarter = allocation.quarter

            if not line_item or not quarter:
                continue

            key = (line_item.id, quarter)

            if key not in quarter_usage:
                quarter_usage[key] = {
                    'line_item': line_item,
                    'quarter': quarter,
                    'ad_amount': Decimal('0.00')
                }

            quarter_usage[key]['ad_amount'] += allocation.allocated_amount

        # Validate each quarter's usage
        for key, data in quarter_usage.items():
            line_item = data['line_item']
            quarter = data['quarter']
            ad_amount = data['ad_amount']

            # Get the budgeted amount for this quarter
            quarter_budget = line_item.get_quarter_amount(quarter)

            # Get currently consumed amount for this quarter (including other PRs and ADs)
            quarter_consumed = line_item.get_quarter_consumed(quarter)

            # If this AD is already approved, subtract its current contribution
            if self.status == 'Approved':
                # Find this AD's current allocation for this quarter
                current_allocation = allocations.filter(
                    pre_line_item=line_item,
                    quarter=quarter
                ).aggregate(total=Sum('allocated_amount'))['total'] or Decimal('0.00')
                quarter_consumed -= current_allocation

            # Calculate what would be consumed after adding this AD
            new_quarter_consumed = quarter_consumed + ad_amount

            # Check if it exceeds the quarterly budget
            if new_quarter_consumed > quarter_budget:
                available = quarter_budget - quarter_consumed
                errors.append(
                    f"AD allocation of ₱{ad_amount:,.2f} to {quarter} exceeds available quarterly budget for '{line_item.category}'. "
                    f"Quarter budget: ₱{quarter_budget:,.2f}, Already consumed: ₱{quarter_consumed:,.2f}, Available: ₱{available:,.2f}"
                )

        return errors


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
    pre = models.ForeignKey('budgets.DepartmentPRE', on_delete=models.CASCADE, related_name='line_items')
    category = models.ForeignKey(PRECategory, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(PRESubCategory, on_delete=models.CASCADE, null=True, blank=True)

    # Line item details
    item_name = models.CharField(max_length=255)
    item_code = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)

    # Source type - track whether item came from Excel template or was manually added
    source_type = models.CharField(
        max_length=20,
        choices=[
            ('excel', 'From Excel Template'),
            ('manual', 'Manually Added')
        ],
        default='excel'
    )
    
    # Quarterly amounts
    q1_amount = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal('0.00'))
    q2_amount = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal('0.00'))
    q3_amount = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal('0.00'))
    q4_amount = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal('0.00'))
    
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
    
    def get_quarter_amount(self, quarter):
        """Get the amount for a specific quarter"""
        return getattr(self, f'{quarter.lower()}_amount', Decimal('0'))

    def get_quarter_consumed(self, quarter):
        """
        Calculate consumed amount for a specific quarter.
        Includes Pending, Partially Approved, and Approved statuses.
        Excludes Draft, Rejected, and Cancelled.

        This ensures accurate budget tracking by counting budget as "consumed"
        as soon as a PR/AD is submitted (Pending status), not just when fully approved.
        """
        from django.db.models import Sum
        from django.db.models.functions import Coalesce

        # Count PR allocations (exclude only Draft, Rejected, Cancelled)
        pr_consumed = PurchaseRequestAllocation.objects.filter(
            pre_line_item=self,
            quarter=quarter
        ).exclude(
            purchase_request__status__in=['Draft', 'Rejected', 'Cancelled']
        ).aggregate(
            total=Coalesce(Sum('allocated_amount'), Decimal('0.00'))
        )['total']

        # Count AD allocations (exclude only Draft, Rejected, Cancelled)
        ad_consumed = ActivityDesignAllocation.objects.filter(
            pre_line_item=self,
            quarter=quarter
        ).exclude(
            activity_design__status__in=['Draft', 'Rejected', 'Cancelled']
        ).aggregate(
            total=Coalesce(Sum('allocated_amount'), Decimal('0.00'))
        )['total']

        return pr_consumed + ad_consumed

    def get_quarter_available(self, quarter):
        """Calculate available amount for a specific quarter"""
        quarter_amount = self.get_quarter_amount(quarter)
        consumed = self.get_quarter_consumed(quarter)
        return quarter_amount - consumed

    def get_quarter_pr_consumed(self, quarter):
        """
        Calculate consumed amount by Purchase Requests only for a specific quarter.
        Includes Pending, Partially Approved, and Approved statuses.
        """
        from django.db.models import Sum
        from django.db.models.functions import Coalesce

        pr_consumed = PurchaseRequestAllocation.objects.filter(
            pre_line_item=self,
            quarter=quarter
        ).exclude(
            purchase_request__status__in=['Draft', 'Rejected', 'Cancelled']
        ).aggregate(
            total=Coalesce(Sum('allocated_amount'), Decimal('0.00'))
        )['total']

        return pr_consumed

    def get_quarter_ad_consumed(self, quarter):
        """
        Calculate consumed amount by Activity Designs only for a specific quarter.
        Includes Pending, Partially Approved, and Approved statuses.
        """
        from django.db.models import Sum
        from django.db.models.functions import Coalesce

        ad_consumed = ActivityDesignAllocation.objects.filter(
            pre_line_item=self,
            quarter=quarter
        ).exclude(
            activity_design__status__in=['Draft', 'Rejected', 'Cancelled']
        ).aggregate(
            total=Coalesce(Sum('allocated_amount'), Decimal('0.00'))
        )['total']

        return ad_consumed

    def get_quarter_pr_count(self, quarter):
        """Get count of Purchase Requests using this line item in a quarter"""
        return PurchaseRequestAllocation.objects.filter(
            pre_line_item=self,
            quarter=quarter
        ).exclude(
            purchase_request__status__in=['Draft', 'Rejected', 'Cancelled']
        ).values('purchase_request').distinct().count()

    def get_quarter_ad_count(self, quarter):
        """Get count of Activity Designs using this line item in a quarter"""
        return ActivityDesignAllocation.objects.filter(
            pre_line_item=self,
            quarter=quarter
        ).exclude(
            activity_design__status__in=['Draft', 'Rejected', 'Cancelled']
        ).values('activity_design').distinct().count()

    def get_quarter_breakdown(self, quarter):
        """
        Get detailed breakdown of budget usage for a specific quarter.
        Returns a dictionary with original, consumed (PR + AD), and available amounts.
        """
        original = self.get_quarter_amount(quarter)
        pr_consumed = self.get_quarter_pr_consumed(quarter)
        ad_consumed = self.get_quarter_ad_consumed(quarter)
        total_consumed = pr_consumed + ad_consumed
        available = original - total_consumed

        pr_count = self.get_quarter_pr_count(quarter)
        ad_count = self.get_quarter_ad_count(quarter)

        return {
            'quarter': quarter,
            'original': original,
            'pr_consumed': pr_consumed,
            'pr_count': pr_count,
            'ad_consumed': ad_consumed,
            'ad_count': ad_count,
            'total_consumed': total_consumed,
            'available': available,
            'utilization_percent': (total_consumed / original * 100) if original > 0 else 0
        }


class PREReceipt(models.Model):
    """Budget receipts/income for PRE"""
    pre = models.ForeignKey('budgets.DepartmentPRE', on_delete=models.CASCADE, related_name='receipts')
    receipt_type = models.CharField(max_length=100)
    
    # Quarterly amounts
    q1_amount = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal('0.00'))
    q2_amount = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal('0.00'))
    q3_amount = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal('0.00'))
    q4_amount = models.DecimalField(max_digits=15, decimal_places=6, default=Decimal('0.00'))
    
    def get_total(self):
        return (self.q1_amount or 0) + (self.q2_amount or 0) + (self.q3_amount or 0) + (self.q4_amount or 0)
    

class PurchaseRequestAllocation(models.Model):
    """
    Track allocation of PRE line items to Purchase Requests
    Records which PRE line items are funding each PR
    """
    
    purchase_request = models.ForeignKey(
        'PurchaseRequest',
        on_delete=models.CASCADE,
        related_name='pre_allocations',
        help_text='The purchase request being funded'
    )
    
    pre_line_item = models.ForeignKey(
        'PRELineItem',
        on_delete=models.PROTECT,  # Don't allow deleting line items that have allocations
        related_name='pr_allocations',
        help_text='The PRE line item providing the funds'
    )
    
    quarter = models.CharField(
        max_length=2,
        choices=[
            ('Q1', 'Quarter 1'),
            ('Q2', 'Quarter 2'),
            ('Q3', 'Quarter 3'),
            ('Q4', 'Quarter 4'),
        ],
        help_text='Which quarter of the PRE line item is being used'
    )
    
    allocated_amount = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        default=Decimal('0.00'),
        help_text='Amount allocated from this line item'
    )
    
    allocated_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the allocation was made'
    )
    
    # Optional: Add notes about the allocation
    notes = models.TextField(blank=True, help_text='Optional notes about this allocation')
    
    class Meta:
        db_table = 'purchase_request_allocations'
        ordering = ['-allocated_at']
        verbose_name = 'Purchase Request Allocation'
        verbose_name_plural = 'Purchase Request Allocations'
        indexes = [
            models.Index(fields=['purchase_request', 'pre_line_item']),
        ]
    
    def __str__(self):
        return f"PR Allocation: ₱{self.allocated_amount:,.2f} from {self.pre_line_item.item_name}"
    
    def get_line_item_display(self):
        """Return formatted display of the line item"""
        category = self.pre_line_item.category.name if self.pre_line_item.category else 'Other'
        return f"{category} - {self.pre_line_item.item_name}"


class ActivityDesignAllocation(models.Model):
    """
    Track allocation of PRE line items to Activity Designs
    Records which PRE line items are funding each AD
    """
    
    activity_design = models.ForeignKey(
        'ActivityDesign',
        on_delete=models.CASCADE,
        related_name='pre_allocations',
        help_text='The activity design being funded'
    )
    
    pre_line_item = models.ForeignKey(
        'PRELineItem',
        on_delete=models.PROTECT,  # Don't allow deleting line items that have allocations
        related_name='ad_allocations',
        help_text='The PRE line item providing the funds'
    )
    
    quarter = models.CharField(
        max_length=2,
        choices=[
            ('Q1', 'Quarter 1'),
            ('Q2', 'Quarter 2'),
            ('Q3', 'Quarter 3'),
            ('Q4', 'Quarter 4'),
        ],
        help_text='Which quarter of the PRE line item is being used'
    )
    
    allocated_amount = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        default=Decimal('0.00'),
        help_text='Amount allocated from this line item'
    )
    
    allocated_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the allocation was made'
    )
    
    # Optional: Add notes about the allocation
    notes = models.TextField(blank=True, help_text='Optional notes about this allocation')
    
    class Meta:
        db_table = 'activity_design_allocations'
        ordering = ['-allocated_at']
        verbose_name = 'Activity Design Allocation'
        verbose_name_plural = 'Activity Design Allocations'
        indexes = [
            models.Index(fields=['activity_design', 'pre_line_item']),
        ]
    
    def __str__(self):
        return f"AD Allocation: ₱{self.allocated_amount:,.2f} from {self.pre_line_item.item_name}"
    
    def get_line_item_display(self):
        """Return formatted display of the line item"""
        category = self.pre_line_item.category.name if self.pre_line_item.category else 'Other'
        return f"{category} - {self.pre_line_item.item_name}"


# IMPORTANT: Also update the existing PurchaseRequest model
# Add these methods to the PurchaseRequest class:

def get_allocated_line_items(self):
    """Get all PRE line items allocated to this PR"""
    return self.pre_allocations.select_related(
        'pre_line_item__category',
        'pre_line_item__subcategory',
        'pre_line_item__pre'
    )

def get_total_allocated_from_pre(self):
    """Calculate total allocated from PRE line items"""
    from django.db.models import Sum
    result = self.pre_allocations.aggregate(
        total=Sum('allocated_amount')
    )
    return result['total'] or Decimal('0.00')

def get_allocation_summary(self):
    """Get summary of all allocations for this PR"""
    allocations = []
    for alloc in self.pre_allocations.all():
        allocations.append({
            'line_item': alloc.pre_line_item.item_name,
            'category': alloc.pre_line_item.category.name if alloc.pre_line_item.category else 'Other',
            'amount': alloc.allocated_amount,
            'pre_id': alloc.pre_line_item.pre.id,
        })
    return allocations


# IMPORTANT: Also update the existing ActivityDesign model
# Add these methods to the ActivityDesign class:

def get_allocated_line_items(self):
    """Get all PRE line items allocated to this AD"""
    return self.pre_allocations.select_related(
        'pre_line_item__category',
        'pre_line_item__subcategory',
        'pre_line_item__pre'
    )

def get_total_allocated_from_pre(self):
    """Calculate total allocated from PRE line items"""
    from django.db.models import Sum
    result = self.pre_allocations.aggregate(
        total=Sum('allocated_amount')
    )
    return result['total'] or Decimal('0.00')

def get_allocation_summary(self):
    """Get summary of all allocations for this AD"""
    allocations = []
    for alloc in self.pre_allocations.all():
        allocations.append({
            'line_item': alloc.pre_line_item.item_name,
            'category': alloc.pre_line_item.category.name if alloc.pre_line_item.category else 'Other',
            'amount': alloc.allocated_amount,
            'pre_id': alloc.pre_line_item.pre.id,
        })
    return allocations

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
        

class PRDraft(models.Model):
    """Draft storage for PR uploads before submission"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pr_draft'
    )
    
    # PR Document
    pr_file = models.FileField(
        upload_to='pr_drafts/%Y/%m/',
        null=True,
        blank=True,
        help_text="Uploaded PR document"
    )
    pr_filename = models.CharField(max_length=255, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_submitted = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'pr_drafts'
        verbose_name = 'PR Draft'
        verbose_name_plural = 'PR Drafts'
    
    def __str__(self):
        return f"PR Draft - {self.user.username}"


class PRDraftSupportingDocument(models.Model):
    """Supporting documents for PR draft"""
    draft = models.ForeignKey(
        PRDraft,
        on_delete=models.CASCADE,
        related_name='supporting_documents'
    )
    document = models.FileField(
        upload_to='pr_draft_supporting/%Y/%m/',
        help_text="Supporting document"
    )
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField(help_text="File size in bytes")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'pr_draft_supporting_documents'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.file_name} ({self.draft.user.username})"
    

class PurchaseRequestSupportingDocument(models.Model):
    """Supporting documents for Purchase Requests"""
    purchase_request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.CASCADE,
        related_name='supporting_documents'
    )
    document = models.FileField(
        upload_to='pr_supporting_docs/%Y/%m/',
        help_text='Supporting document file'
    )
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField(help_text='File size in bytes')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # 🔥 NEW FIELD
    is_signed_copy = models.BooleanField(
        default=False,
        help_text="True if this is the signed version uploaded by admin"
    )

    # 🔥 NEW FIELD - Track who uploaded signed copy
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who uploaded this document (admin for signed copies)"
    )

    class Meta:
        db_table = 'purchase_request_supporting_documents'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.file_name} for PR {self.purchase_request.pr_number}"

    def get_file_extension(self):
        """Get file extension in lowercase"""
        return self.file_name.split('.')[-1].lower() if '.' in self.file_name else ''

    def get_file_size_display(self):
        """Return human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


class PurchaseRequestApprovedDocument(models.Model):
    """
    Approved/signed PR documents uploaded by end users after getting signatures
    from the Approving Officer

    New Workflow:
    1. Admin partially approves PR → PDF generated
    2. End user prints PDF → gets it signed by Approving Officer
    3. End user uploads signed documents using this model
    4. Admin verifies and gives final approval
    """
    purchase_request = models.ForeignKey(
        'PurchaseRequest',
        on_delete=models.CASCADE,
        related_name='signed_approved_documents',
        help_text='Link to PR submission'
    )
    document = models.FileField(
        upload_to='pr_approved_uploads/%Y/%m/',
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'jpg', 'jpeg', 'png']
        )],
        help_text='Signed/approved document (PDF or image scan)'
    )
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField(help_text='File size in bytes', editable=False)
    document_type = models.CharField(
        max_length=50,
        choices=[
            ('signed_pr', 'Signed PR Document'),
            ('signed_supporting', 'Signed Supporting Document'),
        ],
        default='signed_pr',
        help_text='Type of approved document'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_pr_approved_documents',
        help_text='End user who uploaded this document'
    )
    description = models.TextField(
        blank=True,
        help_text='Optional description or notes'
    )

    class Meta:
        db_table = 'purchase_request_approved_documents'
        ordering = ['-uploaded_at']
        verbose_name = 'PR Approved Document'
        verbose_name_plural = 'PR Approved Documents'

    def __str__(self):
        return f"{self.file_name} for PR {self.purchase_request.pr_number}"

    def get_file_extension(self):
        """Get file extension in lowercase"""
        return self.file_name.split('.')[-1].lower() if '.' in self.file_name else ''

    def get_file_size_display(self):
        """Return human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def save(self, *args, **kwargs):
        """Auto-calculate file size before saving"""
        if self.document and not self.file_size:
            self.file_size = self.document.size
        super().save(*args, **kwargs)


class DepartmentPRESupportingDocument(models.Model):
    """Supporting documents for Department PRE submissions"""
    department_pre = models.ForeignKey(
        'DepartmentPRE',
        on_delete=models.CASCADE,
        related_name='supporting_documents',
        help_text='Link to PRE submission'
    )
    document = models.FileField(
        upload_to='pre_supporting_docs/%Y/%m/',
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'docx', 'doc', 'xlsx', 'xls', 'jpg', 'jpeg', 'png']
        )],
        help_text='Supporting document file (PDF, Word, Excel, Images)'
    )
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField(help_text='File size in bytes', editable=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='User who uploaded this document'
    )
    description = models.CharField(
        max_length=500,
        blank=True,
        help_text='Optional description of the document'
    )
    converted_pdf = models.FileField(
        upload_to='pre_supporting_docs_pdf/%Y/%m/',
        null=True,
        blank=True,
        help_text='Auto-converted PDF version for preview (Excel/Word files)'
    )

    class Meta:
        db_table = 'department_pre_supporting_documents'
        ordering = ['-uploaded_at']
        verbose_name = 'PRE Supporting Document'
        verbose_name_plural = 'PRE Supporting Documents'

    def __str__(self):
        return f"{self.file_name} for PRE {str(self.department_pre.id)[:8]}"

    def get_file_extension(self):
        """Get file extension in lowercase"""
        return self.file_name.split('.')[-1].lower() if '.' in self.file_name else ''

    def get_file_size_display(self):
        """Return human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def save(self, *args, **kwargs):
        """Auto-calculate file size before saving"""
        if self.document and not self.file_size:
            self.file_size = self.document.size
        super().save(*args, **kwargs)


class DepartmentPREApprovedDocument(models.Model):
    """
    Approved/signed documents uploaded by end users after getting signatures
    from the Approving Officer

    New Workflow:
    1. Admin partially approves PRE → PDF generated
    2. End user prints PDF → gets it signed by Approving Officer
    3. End user uploads signed documents using this model
    4. Admin verifies and gives final approval
    """
    pre = models.ForeignKey(
        'DepartmentPRE',
        on_delete=models.CASCADE,
        related_name='signed_approved_documents',
        help_text='Link to PRE submission'
    )
    document = models.FileField(
        upload_to='pre_approved_uploads/%Y/%m/',
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'jpg', 'jpeg', 'png']
        )],
        help_text='Signed/approved document (PDF or image scan)'
    )
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField(help_text='File size in bytes', editable=False)
    document_type = models.CharField(
        max_length=50,
        choices=[
            ('signed_pre', 'Signed PRE Document'),
            ('signed_supporting', 'Signed Supporting Document'),
        ],
        default='signed_pre',
        help_text='Type of approved document'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_pre_approved_documents',
        help_text='End user who uploaded this document'
    )
    description = models.TextField(
        blank=True,
        help_text='Optional description or notes'
    )

    class Meta:
        db_table = 'department_pre_approved_documents'
        ordering = ['-uploaded_at']
        verbose_name = 'PRE Approved Document'
        verbose_name_plural = 'PRE Approved Documents'

    def __str__(self):
        return f"{self.file_name} for PRE {str(self.pre.id)[:8]}"

    def get_file_extension(self):
        """Get file extension in lowercase"""
        return self.file_name.split('.')[-1].lower() if '.' in self.file_name else ''

    def get_file_size_display(self):
        """Return human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def save(self, *args, **kwargs):
        """Auto-calculate file size before saving"""
        if self.document and not self.file_size:
            self.file_size = self.document.size
        super().save(*args, **kwargs)


class ADDraft(models.Model):
    """Draft storage for Activity Design uploads before submission"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ad_draft'
    )

    # AD Document (.docx only)
    ad_file = models.FileField(
        upload_to='ad_drafts/%Y/%m/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['docx', 'doc'])],
        help_text="Uploaded Activity Design document (.docx format only)"
    )
    ad_filename = models.CharField(max_length=255, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_submitted = models.BooleanField(default=False)

    class Meta:
        db_table = 'ad_drafts'
        verbose_name = 'AD Draft'
        verbose_name_plural = 'AD Drafts'

    def __str__(self):
        return f"AD Draft - {self.user.username}"


class ADDraftSupportingDocument(models.Model):
    """Supporting documents for AD draft"""
    draft = models.ForeignKey(
        ADDraft,
        on_delete=models.CASCADE,
        related_name='supporting_documents'
    )
    document = models.FileField(
        upload_to='ad_draft_supporting/%Y/%m/',
        help_text="Supporting document"
    )
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField(help_text="File size in bytes")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ad_draft_supporting_documents'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.file_name} ({self.draft.user.username})"

    def get_file_size_display(self):
        """Return human-readable file size"""
        size = self.file_size
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.2f} KB"
        else:
            return f"{size / (1024 * 1024):.2f} MB"


class ActivityDesignSupportingDocument(models.Model):
    """Supporting documents for Activity Designs"""
    activity_design = models.ForeignKey(
        ActivityDesign,
        on_delete=models.CASCADE,
        related_name='supporting_documents'
    )
    document = models.FileField(
        upload_to='ad_supporting_docs/%Y/%m/',
        help_text='Supporting document file'
    )
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField(help_text='File size in bytes')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # Track if this is a signed copy uploaded by admin
    is_signed_copy = models.BooleanField(
        default=False,
        help_text="True if this is the signed version uploaded by admin"
    )

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who uploaded this document (admin for signed copies)"
    )

    class Meta:
        db_table = 'activity_design_supporting_documents'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.file_name} for AD {self.activity_design.ad_number}"

    def get_file_size_display(self):
        """Return human-readable file size"""
        size = self.file_size
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.2f} KB"
        else:
            return f"{size / (1024 * 1024):.2f} MB"


class BudgetSavings(models.Model):
    """
    Snapshot of budget savings at end of fiscal period.
    Captures unused/unspent budget amounts by department.
    """

    budget_allocation = models.ForeignKey(
        BudgetAllocation,
        on_delete=models.CASCADE,
        related_name='savings_snapshots',
        help_text='Link to the budget allocation'
    )

    # Snapshot data - copied from allocation at time of snapshot
    fiscal_year = models.CharField(max_length=10, help_text='Fiscal year of the savings')
    department = models.CharField(max_length=255, help_text='Department name')
    allocated_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text='Total amount allocated to department'
    )
    pr_used = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Amount used by Purchase Requests'
    )
    ad_used = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Amount used by Activity Designs'
    )
    total_used = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text='Total amount used (PR + AD)'
    )
    savings_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text='Savings amount (Allocated - Used)'
    )

    # Metadata
    snapshot_date = models.DateTimeField(
        auto_now_add=True,
        help_text='When this snapshot was created'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_savings_snapshots',
        help_text='Admin who created this snapshot'
    )
    quarter = models.CharField(
        max_length=10,
        blank=True,
        help_text='Q1, Q2, Q3, Q4, or Full Year'
    )
    notes = models.TextField(
        blank=True,
        help_text='Optional notes about this savings snapshot'
    )

    # Archive fields
    is_archived = models.BooleanField(default=False, db_index=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='archived_budget_savings'
    )
    archive_reason = models.TextField(blank=True)

    # Managers
    objects = ArchiveManager()  # Default: excludes archived
    all_objects = models.Manager()  # Fallback: includes everything

    class Meta:
        ordering = ['-snapshot_date']
        verbose_name = "Budget Savings"
        verbose_name_plural = "Budget Savings"
        indexes = [
            models.Index(fields=['fiscal_year', 'department']),
            models.Index(fields=['-snapshot_date']),
        ]

    def __str__(self):
        return f"{self.department} {self.fiscal_year} - Savings: ₱{self.savings_amount:,.2f}"

    @property
    def utilization_rate(self):
        """Calculate budget utilization percentage"""
        if self.allocated_amount > 0:
            return (self.total_used / self.allocated_amount) * 100
        return Decimal('0.00')

    @property
    def savings_rate(self):
        """Calculate savings percentage"""
        if self.allocated_amount > 0:
            return (self.savings_amount / self.allocated_amount) * 100
        return Decimal('0.00')

    def get_quarterly_breakdown(self):
        """
        Get quarterly breakdown of savings from the associated PRE line items.
        Returns dict with Q1-Q4 allocated, used, and available amounts.
        """
        if not self.budget_allocation:
            return None

        # Get all PREs for this allocation
        pres = self.budget_allocation.pres.filter(status='Approved')

        quarterly_data = {
            'Q1': {'allocated': Decimal('0.00'), 'consumed': Decimal('0.00'), 'available': Decimal('0.00')},
            'Q2': {'allocated': Decimal('0.00'), 'consumed': Decimal('0.00'), 'available': Decimal('0.00')},
            'Q3': {'allocated': Decimal('0.00'), 'consumed': Decimal('0.00'), 'available': Decimal('0.00')},
            'Q4': {'allocated': Decimal('0.00'), 'consumed': Decimal('0.00'), 'available': Decimal('0.00')},
        }

        for pre in pres:
            for line_item in pre.line_items.all():
                for quarter in ['Q1', 'Q2', 'Q3', 'Q4']:
                    quarterly_data[quarter]['allocated'] += line_item.get_quarter_amount(quarter)
                    quarterly_data[quarter]['consumed'] += line_item.get_quarter_consumed(quarter)
                    quarterly_data[quarter]['available'] += line_item.get_quarter_available(quarter)

        return quarterly_data


class PRELineItemSavings(models.Model):
    """
    Track savings at the PRE line item level for granular analysis.
    Captures unused budget from specific line items and quarters.
    This is an optional enhancement to BudgetSavings for detailed tracking.
    """

    # Links to parent savings snapshot and original line item
    budget_savings = models.ForeignKey(
        BudgetSavings,
        on_delete=models.CASCADE,
        related_name='line_item_breakdowns',
        help_text='Parent savings snapshot'
    )
    pre_line_item = models.ForeignKey(
        PRELineItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='savings_records',
        help_text='Original PRE line item (may be null if deleted)'
    )

    # Line item details (snapshot at time of creation)
    category = models.CharField(
        max_length=255,
        help_text='Budget category (Personnel/MOOE/Capital)'
    )
    subcategory = models.CharField(
        max_length=255,
        blank=True,
        help_text='Budget subcategory if applicable'
    )
    item_name = models.CharField(
        max_length=255,
        help_text='Name of the budget line item'
    )

    # Q1 Breakdown
    q1_allocated = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Q1 allocated amount'
    )
    q1_consumed = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Q1 consumed amount (PR + AD)'
    )
    q1_surplus = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Q1 unused/surplus amount'
    )

    # Q2 Breakdown
    q2_allocated = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Q2 allocated amount'
    )
    q2_consumed = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Q2 consumed amount (PR + AD)'
    )
    q2_surplus = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Q2 unused/surplus amount'
    )

    # Q3 Breakdown
    q3_allocated = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Q3 allocated amount'
    )
    q3_consumed = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Q3 consumed amount (PR + AD)'
    )
    q3_surplus = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Q3 unused/surplus amount'
    )

    # Q4 Breakdown
    q4_allocated = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Q4 allocated amount'
    )
    q4_consumed = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Q4 consumed amount (PR + AD)'
    )
    q4_surplus = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Q4 unused/surplus amount'
    )

    # Totals
    total_allocated = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Total allocated across all quarters'
    )
    total_consumed = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Total consumed across all quarters'
    )
    total_surplus = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Total unused/surplus across all quarters'
    )

    # Additional metadata
    is_procurable = models.BooleanField(
        default=False,
        help_text='Whether this item requires procurement'
    )
    is_significant = models.BooleanField(
        default=False,
        help_text='True if surplus exceeds threshold (e.g., >₱5,000)'
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When this line item savings record was created'
    )

    class Meta:
        ordering = ['-total_surplus', 'category', 'item_name']
        verbose_name = "PRE Line Item Savings"
        verbose_name_plural = "PRE Line Item Savings"
        indexes = [
            models.Index(fields=['budget_savings', 'category']),
            models.Index(fields=['-total_surplus']),
            models.Index(fields=['is_significant']),
        ]

    def __str__(self):
        return f"{self.item_name} - Surplus: ₱{self.total_surplus:,.2f}"

    @property
    def utilization_rate(self):
        """Calculate utilization percentage"""
        if self.total_allocated > 0:
            return (self.total_consumed / self.total_allocated) * 100
        return Decimal('0.00')

    @property
    def surplus_rate(self):
        """Calculate surplus percentage"""
        if self.total_allocated > 0:
            return (self.total_surplus / self.total_allocated) * 100
        return Decimal('0.00')

    def get_quarter_data(self, quarter):
        """Get data for a specific quarter"""
        quarter_map = {
            'Q1': (self.q1_allocated, self.q1_consumed, self.q1_surplus),
            'Q2': (self.q2_allocated, self.q2_consumed, self.q2_surplus),
            'Q3': (self.q3_allocated, self.q3_consumed, self.q3_surplus),
            'Q4': (self.q4_allocated, self.q4_consumed, self.q4_surplus),
        }
        allocated, consumed, surplus = quarter_map.get(quarter, (0, 0, 0))
        return {
            'allocated': allocated,
            'consumed': consumed,
            'surplus': surplus,
            'utilization': (consumed / allocated * 100) if allocated > 0 else 0
        }


class BudgetTransactionLog(models.Model):
    """
    Tracks all budget balance changes for complete financial audit trail.
    Records every transaction that affects a BudgetAllocation's balance.
    """
    TRANSACTION_TYPES = [
        ('PRE_APPROVED', 'PRE Approved'),
        ('PR_APPROVED', 'Purchase Request Approved'),
        ('AD_APPROVED', 'Activity Design Approved'),
        ('PRE_REJECTED', 'PRE Rejected'),
        ('PR_REJECTED', 'Purchase Request Rejected'),
        ('AD_REJECTED', 'Activity Design Rejected'),
        ('ALLOCATION_CREATED', 'Allocation Created'),
        ('ALLOCATION_MODIFIED', 'Allocation Modified'),
        ('ALLOCATION_DELETED', 'Allocation Deleted'),
        ('REALIGNMENT_APPROVED', 'Budget Realignment Approved'),
    ]

    # Core fields
    allocation = models.ForeignKey(
        'BudgetAllocation',
        on_delete=models.CASCADE,
        related_name='transaction_logs',
        help_text="The budget allocation affected by this transaction"
    )
    transaction_type = models.CharField(
        max_length=30,
        choices=TRANSACTION_TYPES,
        help_text="Type of transaction that caused the balance change"
    )

    # Amount tracking
    amount_change = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Amount added (positive) or deducted (negative) from budget"
    )
    previous_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Balance before this transaction"
    )
    new_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Balance after this transaction"
    )

    # Related document tracking
    related_document_type = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Type of related document (PRE, PR, AD, etc.)"
    )
    related_document_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="ID or number of the related document"
    )

    # User and timestamp
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who triggered this transaction"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this transaction occurred"
    )

    # Additional context
    notes = models.TextField(
        blank=True,
        help_text="Additional notes or context about this transaction"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Budget Transaction Log'
        verbose_name_plural = 'Budget Transaction Logs'
        indexes = [
            models.Index(fields=['allocation', '-created_at']),
            models.Index(fields=['transaction_type', '-created_at']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.transaction_type} - {self.allocation.end_user.department if self.allocation.end_user else 'N/A'} - ₱{self.amount_change:,.2f}"

    @property
    def is_increase(self):
        """Check if this transaction increased the budget"""
        return self.amount_change > 0

    @property
    def is_decrease(self):
        """Check if this transaction decreased the budget"""
        return self.amount_change < 0

    @property
    def formatted_amount(self):
        """Return formatted amount with sign"""
        if self.amount_change > 0:
            return f"+₱{self.amount_change:,.2f}"
        elif self.amount_change < 0:
            return f"-₱{abs(self.amount_change):,.2f}"
        else:
            return "₱0.00"


class PREBudgetRealignment(models.Model):
    """PRE-based budget realignment between line items with quarterly tracking"""
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Partially Approved', 'Partially Approved'),
        ('Rejected', 'Rejected'),
    ]

    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="pre_realignment_requests")
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="pre_realignment_approvals")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    reason = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    partially_approved_at = models.DateTimeField(null=True, blank=True)
    final_approved_at = models.DateTimeField(null=True, blank=True)

    # Approval tracking
    approved_by_approving_officer = models.BooleanField(default=False, null=True, blank=True)
    approved_by_admin = models.BooleanField(default=False, null=True, blank=True)
    partial_approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="pre_realignment_partial_approvals")
    admin_approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="pre_realignment_admin_approvals")
    admin_approved_at = models.DateTimeField(null=True, blank=True)

    # Document fields (following PRE/PR pattern)
    partially_approved_pdf = models.FileField(
        upload_to='br_pdfs/%Y/%m/',
        null=True,
        blank=True,
        help_text="PDF generated from uploaded documents when partially approved"
    )
    approved_documents = models.FileField(
        upload_to='br_approved_docs/%Y/%m/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
        help_text="Scanned approved documents uploaded by admin"
    )
    final_approved_scan = models.FileField(
        upload_to='br_scanned/%Y/%m/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
        help_text="Scanned copy of signed budget realignment"
    )

    # Admin notes and rejection
    admin_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)

    # Source (Where funds come FROM)
    source_pre = models.ForeignKey(
        'DepartmentPRE',
        on_delete=models.CASCADE,
        related_name='source_budget_realignments'
    )
    source_item_key = models.CharField(max_length=255)
    source_quarter = models.CharField(max_length=10, null=True, blank=True)  # Deprecated - use quarterly amounts

    target_pre = models.ForeignKey(
        'DepartmentPRE',
        on_delete=models.CASCADE,
        related_name='target_budget_realignments'
    )
    target_item_key = models.CharField(max_length=255)
    target_quarter = models.CharField(max_length=10, null=True, blank=True)  # Deprecated - use quarterly amounts

    # Quarterly amounts (NEW - replaces single 'amount' field)
    q1_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    q2_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    q3_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    q4_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Keep single amount for backward compatibility
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    source_item_display = models.CharField(max_length=500, null=True, blank=True)
    target_item_display = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        total_amount = self.get_total_amount()
        return f"Realignment: {self.source_item_display} → {self.target_item_display} (₱{total_amount:,.2f})"

    def save(self, *args, **kwargs):
        """Auto-calculate total amount from quarterly amounts"""
        self.amount = self.get_total_amount()
        super().save(*args, **kwargs)

    def get_total_amount(self):
        """Calculate total amount from quarterly amounts"""
        return self.q1_amount + self.q2_amount + self.q3_amount + self.q4_amount

    def get_selected_quarters(self):
        """Get list of quarters with non-zero amounts"""
        quarters = []
        if self.q1_amount > 0:
            quarters.append(('q1', 'Q1', self.q1_amount))
        if self.q2_amount > 0:
            quarters.append(('q2', 'Q2', self.q2_amount))
        if self.q3_amount > 0:
            quarters.append(('q3', 'Q3', self.q3_amount))
        if self.q4_amount > 0:
            quarters.append(('q4', 'Q4', self.q4_amount))
        return quarters

    @property
    def can_be_approved(self):
        """Check if realignment can still be approved"""
        if self.status != 'Pending' and self.status != 'Partially Approved':
            return False

        # Check each quarter has sufficient funds in the NEW PRELineItem structure
        quarters_to_check = self.get_selected_quarters()

        for quarter_code, quarter_label, quarter_amount in quarters_to_check:
            # Use NEW PRELineItem model - source_item_key now stores the PRELineItem ID
            try:
                source_item = PRELineItem.objects.get(id=self.source_item_key, pre=self.source_pre)
            except (PRELineItem.DoesNotExist, ValueError):
                return False

            # Check the specific quarter's remaining amount
            allocated = getattr(source_item, f'{quarter_code}_amount', 0)
            consumed = source_item.get_quarter_consumed(quarter_code)
            remaining = allocated - consumed

            if remaining < quarter_amount:
                return False

        return True

    @property
    def source_available_budget(self):
        """Get total available budget for source line item"""
        try:
            source_item = PRELineItem.objects.get(id=self.source_item_key, pre=self.source_pre)
        except (PRELineItem.DoesNotExist, ValueError):
            return 0

        # Sum all quarterly remaining amounts
        total_remaining = 0
        for quarter in ['q1', 'q2', 'q3', 'q4']:
            allocated = getattr(source_item, f'{quarter}_amount', 0)
            consumed = source_item.get_quarter_consumed(quarter)
            total_remaining += (allocated - consumed)

        return total_remaining

    def get_source_quarterly_available(self):
        """Get available budget for each quarter in source"""
        quarters = {}
        try:
            source_item = PRELineItem.objects.get(id=self.source_item_key, pre=self.source_pre)
        except (PRELineItem.DoesNotExist, ValueError):
            source_item = None

        for quarter in ['q1', 'q2', 'q3', 'q4']:
            if source_item:
                allocated = getattr(source_item, f'{quarter}_amount', 0)
                consumed = source_item.get_quarter_consumed(quarter)
                remaining = allocated - consumed
            else:
                allocated = consumed = remaining = 0

            quarters[quarter] = {
                'allocated': allocated,
                'consumed': consumed,
                'remaining': remaining,
            }
        return quarters

    @property
    def target_current_budget(self):
        """Get current allocated budget for target line item"""
        try:
            target_item = PRELineItem.objects.get(id=self.target_item_key, pre=self.target_pre)
        except (PRELineItem.DoesNotExist, ValueError):
            return 0

        # Sum all quarterly allocated amounts
        return sum([
            getattr(target_item, 'q1_amount', 0),
            getattr(target_item, 'q2_amount', 0),
            getattr(target_item, 'q3_amount', 0),
            getattr(target_item, 'q4_amount', 0),
        ])

    @property
    def source_total_allocated(self):
        """Get total allocated budget for source line item"""
        try:
            source_item = PRELineItem.objects.get(id=self.source_item_key, pre=self.source_pre)
        except (PRELineItem.DoesNotExist, ValueError):
            return 0

        return sum([
            getattr(source_item, 'q1_amount', 0),
            getattr(source_item, 'q2_amount', 0),
            getattr(source_item, 'q3_amount', 0),
            getattr(source_item, 'q4_amount', 0),
        ])

    @property
    def source_total_consumed(self):
        """Get total consumed budget for source line item"""
        try:
            source_item = PRELineItem.objects.get(id=self.source_item_key, pre=self.source_pre)
        except (PRELineItem.DoesNotExist, ValueError):
            return 0

        return sum([
            source_item.get_quarter_consumed('q1'),
            source_item.get_quarter_consumed('q2'),
            source_item.get_quarter_consumed('q3'),
            source_item.get_quarter_consumed('q4'),
        ])

    def approve_with_documents(self, admin_user):
        """Final approval after document upload - executes budget realignment"""
        from django.utils import timezone
        from decimal import Decimal

        was_already_approved = self.status == 'Approved'

        self.status = 'Approved'
        self.final_approved_at = timezone.now()
        self.admin_approved_by = admin_user
        self.admin_approved_at = timezone.now()
        self.approved_by_admin = True

        # Execute budget realignment if not already done
        if not was_already_approved:
            self._execute_budget_realignment()

        self.save()

    def _execute_budget_realignment(self):
        """Execute the actual budget transfer between line items"""
        from decimal import Decimal
        from django.db import transaction

        # Transfer each quarter's amount
        quarters_to_transfer = self.get_selected_quarters()

        with transaction.atomic():
            for quarter_code, quarter_label, quarter_amount in quarters_to_transfer:
                if quarter_amount <= 0:
                    continue

                # Get source line item by ID
                try:
                    source_item = PRELineItem.objects.get(id=self.source_item_key, pre=self.source_pre)
                except PRELineItem.DoesNotExist:
                    raise ValueError(f"Source line item not found for ID {self.source_item_key}")

                # Get target line item by ID
                try:
                    target_item = PRELineItem.objects.get(id=self.target_item_key, pre=self.target_pre)
                except PRELineItem.DoesNotExist:
                    raise ValueError(f"Target line item not found for ID {self.target_item_key}")

                # Deduct from source
                quarter_field = f'{quarter_code}_amount'
                current_source = getattr(source_item, quarter_field, 0)
                setattr(source_item, quarter_field, current_source - quarter_amount)
                source_item.save()

                # Add to target
                current_target = getattr(target_item, quarter_field, 0)
                setattr(target_item, quarter_field, current_target + quarter_amount)
                target_item.save()


class BudgetRealignmentSupportingDocument(models.Model):
    """Supporting documents for Budget Realignment requests"""
    budget_realignment = models.ForeignKey(
        PREBudgetRealignment,
        on_delete=models.CASCADE,
        related_name='supporting_documents'
    )
    document = models.FileField(
        upload_to='br_supporting_docs/%Y/%m/',
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'docx', 'doc', 'xlsx', 'xls', 'jpg', 'jpeg', 'png']
        )]
    )
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=500, blank=True)
    is_signed_copy = models.BooleanField(default=False, help_text="Is this a signed/approved copy?")

    class Meta:
        ordering = ['uploaded_at']

    def __str__(self):
        return self.file_name

    def get_file_size_display(self):
        """Return human-readable file size"""
        size_bytes = self.file_size
        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"