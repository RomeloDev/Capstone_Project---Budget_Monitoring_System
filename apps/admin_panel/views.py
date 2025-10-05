from datetime import datetime, timedelta
import decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from apps.users.models import User
from .models import BudgetAllocation, Budget, ApprovedBudget, AuditTrail
from apps.budgets.models import ApprovedBudget as NewApprovedBudget, SupportingDocument
from apps.users.models import User
from django.contrib import messages
from decimal import Decimal
from apps.end_user_app.models import PurchaseRequest, Budget_Realignment, DepartmentPRE, ActivityDesign, PRELineItemBudget, PurchaseRequestAllocation, ActivityDesignAllocations, PREBudgetRealignment
from apps.users.models import User
from django.db import transaction
from django.db.models import Sum
from django.template.defaultfilters import floatformat
from django.contrib.humanize.templatetags.humanize import intcomma
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .utils import log_audit_trail
from django.db.models import Count
from datetime import timedelta
from apps.users.utils import role_required
import mimetypes
from django.http import FileResponse, Http404
import os
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from django.http import HttpResponse
from openpyxl.utils import get_column_letter
from openpyxl import Workbook
from django.db.models import Q

# Create your views here.
@role_required('admin', login_url='/admin/')
def admin_dashboard(request):
    try:
        # Total Users (Active users who logged in within last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        end_users_total = User.objects.filter(
            is_staff=False, 
            is_approving_officer=True,
            last_login__gte=thirty_days_ago
        ).count()
        
        # Alternative: All registered users if you prefer total count
        # end_users_total = User.objects.filter(is_staff=False, is_approving_officer=True).count()
        
        # Total Budget from ApprovedBudget (since Budget model seems different)
        total_budget = ApprovedBudget.objects.aggregate(
            Sum('amount')
        )['amount__sum'] or 0
        
        # Pending Requests Count
        total_pending_realignment_request = Budget_Realignment.objects.filter(
            status='pending'
        ).count()
        
        # Approved Requests Count  
        total_approved_realignment_request = Budget_Realignment.objects.filter(
            status='approved'
        ).count()
        
        # Budget allocations for the table
        budget_allocated = BudgetAllocation.objects.select_related('approved_budget').all()
        
        # Calculate percentage changes for trends (you can customize this based on your needs)
        # This is a simple example - you might want to compare with previous period
        user_trend = "up"  # You can calculate actual trend
        budget_trend = "up"
        pending_trend = "down" if total_pending_realignment_request < 10 else "up"
        approved_trend = "up"
        
        # Chart data (group by department)
        dept_agg = (
            BudgetAllocation.objects
            .values('department')
            .annotate(
                total_allocated=Sum('total_allocated'),
                total_spent=Sum('spent')
            )
            .order_by('department')
        )
        
        dept_labels = [row['department'] or 'Unknown' for row in dept_agg]
        dept_allocated = [float(row['total_allocated'] or 0) for row in dept_agg]
        dept_spent = [float(row['total_spent'] or 0) for row in dept_agg]
        dept_remaining = [max(0.0, a - s) for a, s in zip(dept_allocated, dept_spent)]
        
        # Recent Activity (latest 8 for better display)
        recent_activities = (
            AuditTrail.objects
            .select_related('user')
            .order_by('-timestamp')[:8]
        )
        
        # Additional metrics for enhanced dashboard
        # Total departments with active budgets
        active_departments = BudgetAllocation.objects.values('department').distinct().count()
        
        # Average budget utilization
        total_allocated_sum = sum(dept_allocated) or 1  # Avoid division by zero
        total_spent_sum = sum(dept_spent)
        avg_utilization = (total_spent_sum / total_allocated_sum * 100) if total_allocated_sum > 0 else 0
        
        # Low budget departments (less than 20% remaining)
        low_budget_depts = BudgetAllocation.objects.filter(
            total_allocated__gt=0
        ).extra(
            where=["(total_allocated - spent) / total_allocated < 0.2"]
        ).count()
        
    except Exception as e:
        # Fallback values in case of any errors
        print(f"Dashboard error: {e}")  # For debugging
        end_users_total = 0
        total_budget = 0
        total_pending_realignment_request = 0
        total_approved_realignment_request = 0
        budget_allocated = BudgetAllocation.objects.none()
        dept_labels, dept_allocated, dept_spent, dept_remaining = [], [], [], []
        recent_activities = AuditTrail.objects.none()
        user_trend = budget_trend = pending_trend = approved_trend = "neutral"
        active_departments = 0
        avg_utilization = 0
        low_budget_depts = 0

    context = {
        # Main metrics
        'end_users_total': end_users_total,
        'total_budget': total_budget,
        'total_pending_realignment_request': total_pending_realignment_request,
        'total_approved_realignment_request': total_approved_realignment_request,
        
        # Trends (you can implement actual trend calculation)
        'user_trend': user_trend,
        'budget_trend': budget_trend,
        'pending_trend': pending_trend,
        'approved_trend': approved_trend,
        
        # Data for table and charts
        'budget_allocated': budget_allocated,
        'dept_labels': dept_labels,
        'dept_allocated': dept_allocated,
        'dept_spent': dept_spent,
        'dept_remaining': dept_remaining,
        
        # Recent activity
        'recent_activities': recent_activities,
        
        # Additional metrics
        'active_departments': active_departments,
        'avg_utilization': round(avg_utilization, 1),
        'low_budget_depts': low_budget_depts,
        
        # Template helper
        'current_time': timezone.now(),
    }
    
    return render(request, 'admin_panel/dashboard.html', context)
    
@role_required('admin', login_url='/admin/')
def client_accounts(request):
    try:
        end_users = User.objects.filter(is_staff=False)
    except User.DoesNotExist:
        end_users = None
    return render(request, 'admin_panel/client_accounts.html', {'end_users': end_users})

@role_required('admin', login_url='/admin/')
def register_account(request):
    
    if request.method == "POST":
         # Retrieval of value in input fields
        username = request.POST.get('username')
        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        department = request.POST.get('department')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm-password')
        position = request.POST.get('position')
        
        # Validate password confirmation
        if password != confirm_password:
            return render(request, 'admin_panel/client_accounts.html', {'error': 'Passwords do not match'})
        
        # Check if the department or username or email are already exists
        if User.objects.filter(username=username).exists():
            return render(request, 'admin_panel/client_accounts.html', {'error': 'Username already taken.'})

        if User.objects.filter(email=email).exists():
            return render(request, 'admin_panel/client_accounts.html', {'error': f'Email {email} already registered.'})
        
        if User.objects.filter(department=department).exists():
            return render(request, 'admin_panel/client_accounts.html', {'error': f'Department {department} already registered.'})
        
        if department == 'Approving-Officer':
            approving_officer = User.objects.create_approving_officer(username=username, fullname=fullname, email=email, password=password)
            return render(request, "admin_panel/client_accounts.html", {'success': "Approving Officer Account registered successfully!"})
        else:
            # Create and save the user
            user = User.objects.create_user(username=username, fullname=fullname, email=email, password=password, department=department, position=position)
            
            try:
                end_users = User.objects.filter(is_staff=False)
            except User.DoesNotExist:
                end_users = None
            return render(request, "admin_panel/client_accounts.html", {'success': "Account registered successfully!", 'end_users': end_users})

@role_required('admin', login_url='/admin/')
def departments_pr_request(request):
    STATUS = (
        ('Pending', 'Pending'),
        ('Partially Approved', 'Partially Approved'),
        ('Rejected', 'Rejected'),
        ('Approved', 'Approved')
    )
    departments = User.objects.filter(is_staff=False, is_approving_officer=False).values_list('department', flat=True).distinct()
    
    try:
        users_purchase_requests = PurchaseRequest.objects.filter(pr_status='Submitted').select_related('requested_by', 'budget_allocation__approved_budget', 'source_pre')
    except PurchaseRequest.DoesNotExist:
        users_purchase_requests = None
    
    status_counts = {
        'total': users_purchase_requests.count(),
        'pending': users_purchase_requests.filter(submitted_status='Pending').count(),
        'approved': users_purchase_requests.filter(submitted_status='Approved').count(),
        'partially_approved': users_purchase_requests.filter(submitted_status='Partially Approved').count(),
        'rejected': users_purchase_requests.filter(submitted_status='Rejected').count(),
    }
    
    filter_department = request.GET.get('department')
    if filter_department:
        users_purchase_requests = PurchaseRequest.objects.filter(requested_by__department=filter_department, pr_status='Submitted',).select_related('requested_by', 'budget_allocation__approved_budget', 'source_pre')
        
    status_filter = request.GET.get('status')
    if status_filter:
        users_purchase_requests = users_purchase_requests.filter(submitted_status=status_filter, pr_status='Submitted')
        
    context = {'users_purchase_requests': users_purchase_requests,     'departments': departments, 'status_choices': STATUS, 'status_counts': status_counts}
    
    return render(request, 'admin_panel/departments_pr_request.html', context)

@role_required('admin', login_url='/admin/')
def handle_departments_request(request, request_id):
    """
    Optional admin handler for PRs. Aligns with model fields and updates allocation.
    Note: Approving Officer flow is canonical; consider removing this view if redundant.
    """
    purchase_request = get_object_or_404(PurchaseRequest, id=request_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        allocation = purchase_request.budget_allocation
        if action == 'approve':
            if allocation is None:
                messages.error(request, 'No budget allocation linked to this request.')
                return redirect('department_pr_request')
            
            # if purchase_request.source_pre and purchase_request.source_item_key:
            #     try:
            #         line_item = PRELineItemBudget.objects.get(
            #             pre=purchase_request.source_pre, 
            #             item_key=purchase_request.source_item_key,
            #             quarter=purchase_request.source_quarter
            #             )
                    
            #         # Check if sufficient budget remains
            #         if line_item.remaining_amount >= purchase_request.total_amount:
            #             line_item.consumed_amount += purchase_request.total_amount
            #             line_item.save()
                        
            #         else:
            #             messages.error(request, f"Insufficient budget in {line_item}. Remaining: ₱{line_item.remaining_amount}")
            #             return redirect('department_pr_request')
            #     except PRELineItemBudget.DoesNotExist:
            #         messages.error(request, "Budget line item not found.")
            #         return redirect('department_pr_request')
            
            # if purchase_request.source_pre and purchase_request.source_item_key:
            #     try:
            #         # Simple query first - no annotations
            #         all_items = PRELineItemBudget.objects.filter(
            #             pre=purchase_request.source_pre,
            #             item_key=purchase_request.source_item_key
            #         )
                    
            #         available_items = [item for item in all_items if item.remaining_amount > 0]
                    
            #         remaining_to_allocate = purchase_request.total_amount
                    
            #         for item in available_items:
            #             if remaining_to_allocate <= 0:
            #                 break
                        
            #             allocation_amount = min(item.remaining_amount, remaining_to_allocate)
            #             if allocation_amount > 0:
            #                 item.consumed_amount += allocation_amount
            #                 item.save()
            #                 remaining_to_allocate -= allocation_amount
                            
            #     except Exception as e:
            #         messages.error(request, f"Error processing budget: {e}")
            #         return redirect('department_pr_request')
                    
                #     print(f"DEBUG: Found {all_items.count()} items for {purchase_request.source_item_key}")
                    
                #     # Filter in Python for remaining budget
                #     available_items = []
                #     for item in all_items:
                #         remaining = item.remaining_amount
                #         print(f"DEBUG: {item.quarter} - Allocated: ₱{item.allocated_amount}, Consumed: ₱{item.consumed_amount}, Remaining: ₱{remaining}")
                #         if remaining > 0:
                #             available_items.append(item)
                    
                #     if not available_items:
                #         messages.error(request, f"No budget available for {purchase_request.source_item_key}. All quarters consumed.")
                #         return redirect('department_pr_request')
                    
                #     # Calculate total available
                #     total_available = sum(item.remaining_amount for item in available_items)
                #     print(f"DEBUG: Total available across all quarters: ₱{total_available}")
                    
                #     if total_available < purchase_request.total_amount:
                #         messages.error(request, f"Insufficient total budget. Available: ₱{total_available}, Required: ₱{purchase_request.total_amount}")
                #         return redirect('department_pr_request')
                    
                #     # Distribute across quarters - ROBUST VERSION
                #     remaining_to_allocate = purchase_request.total_amount
                #     allocated_quarters = []
                #     total_allocated = Decimal('0')

                #     for item in available_items:
                #         if remaining_to_allocate <= Decimal('0'):
                #             print(f"DEBUG: Breaking loop - remaining_to_allocate: ₱{remaining_to_allocate}")
                #             break
                        
                #         allocation_amount = min(item.remaining_amount, remaining_to_allocate)
                        
                #         if allocation_amount > Decimal('0'):
                #             # Update the item
                #             item.consumed_amount += allocation_amount
                #             item.save()
                            
                #             # Track the allocation
                #             allocated_quarters.append(f"{item.quarter.upper()}: ₱{allocation_amount}")
                #             total_allocated += allocation_amount
                #             remaining_to_allocate -= allocation_amount
                            
                #             print(f"DEBUG: Allocated ₱{allocation_amount} from {item.quarter}")
                #             print(f"DEBUG: Remaining to allocate: ₱{remaining_to_allocate}")

                #     # Verify the allocation
                #     print(f"DEBUG: Total allocated: ₱{total_allocated}")
                #     print(f"DEBUG: Purchase request amount: ₱{purchase_request.total_amount}")
                #     print(f"DEBUG: Final remaining: ₱{remaining_to_allocate}")

                #     if total_allocated != purchase_request.total_amount:
                #         print(f"ERROR: Allocation mismatch! Expected: ₱{purchase_request.total_amount}, Actual: ₱{total_allocated}")

                #     messages.success(request, f"Budget updated: {', '.join(allocated_quarters)} (Total: ₱{total_allocated})")
                    
                # except Exception as e:
                #     print(f"DEBUG ERROR: {e}")
                #     messages.error(request, f"Error processing budget allocation: {e}")
                #     return redirect('department_pr_request')

            # Check remaining budget before approval (this is the BudgetAllocation object)
            # if allocation.remaining_budget < (purchase_request.total_amount or 0):
            #     messages.error(request, 'Insufficient remaining budget to approve this request.')
            #     return redirect('department_pr_request')
            
            # allocation.spent = (allocation.spent or 0) + (purchase_request.total_amount or 0)
            # allocation.save(update_fields=['spent', 'updated_at'])
            purchase_request.pr_status = 'Submitted'
            purchase_request.submitted_status = 'Partially Approved'
            purchase_request.approved_by_admin = True
            purchase_request.save(update_fields=['pr_status', 'submitted_status', 'updated_at', 'approved_by_admin'])
            
            log_audit_trail(
                request=request,
                action='APPROVE',
                model_name='PurchaseRequest',
                record_id=purchase_request.id,
                detail=f'Purchase Request {purchase_request.pr_no} have been Partially Approved by Admin'
            )
            
            messages.success(request, 'Purchase Request approved successfully.')
        elif action == 'reject':
            try:
                allocations = PurchaseRequestAllocation.objects.filter(purchase_request=purchase_request).select_related('pre_line_item')
                
                total_released = Decimal('0')
                released_details = []
                
                for pr_allocation in allocations:
                    line_item = pr_allocation.pre_line_item
                    allocated_amount = pr_allocation.allocated_amount
                    
                    line_item.consumed_amount -= allocated_amount
                    line_item.save()
                    
                    total_released += allocated_amount
                    released_details.append(f"{line_item.item_key} {line_item.quarter}: ₱{allocated_amount}")
                    
                    print(f"Released ₱{allocated_amount} back to {line_item.item_key} {line_item.quarter}")
                    
                # Delete allocations after reversal
                allocations.delete()
                
                purchase_request.pr_status = 'Submitted'
                purchase_request.submitted_status = 'Rejected'
                
                purchase_request.save(update_fields=['pr_status', 'submitted_status', 'updated_at'])
                
                log_audit_trail(
                    request=request,
                    action='REJECT',
                    model_name='PurchaseRequest',
                    record_id=purchase_request.id,
                    detail=f'Purchase Request {purchase_request.pr_no} have been Rejected by Admin'
                )
                
                messages.error(request, f"Purchase Request PR-{purchase_request.pr_no} has been Rejected")
                messages.success(request, f'Released ₱{total_released:,.2f} back to budget.')
                
            except Exception as e:
                print(f"DEBUG ERROR: {e}")
                messages.error(request, f"Error processing rejection: {e}")
                return redirect('department_pr_request')

    return redirect('department_pr_request')

@role_required('admin', login_url='/admin/')
def budget_allocation(request):
    approved_budgets = ApprovedBudget.objects.all()
    departments = User.objects.filter(is_staff=False, is_approving_officer=False).values_list('department', flat=True).distinct()
    
    if request.method == 'POST':
        department = request.POST.get('department')
        approved_budget_id = request.POST.get('approved_budget')
        amount = request.POST.get('amount')
        
        # Validation
        if not department or not approved_budget_id or not amount:
            messages.error(request, "All fields are required.")
            return redirect('budget_allocation')
        
        try:
            amount = float(amount)
            if amount < 0:
                raise ValueError("Amount cannot be negative.")
        except ValueError:
            messages.error(request, "Enter a valid non-negative amount.")
            return redirect('budget_allocation')
        
        try:
            approved_budget = ApprovedBudget.objects.get(id=approved_budget_id)
        except ApprovedBudget.DoesNotExist:
            messages.error(request, "Selected approved budget does not exist.")
            return redirect('budget_allocation')
        
        # Prevent duplicate department allocations for same approved budget
        existing = BudgetAllocation.objects.filter(department=department, approved_budget=approved_budget).exists()
        if existing:
            messages.warning(request, "This department already has an allocation under this budget.")
            return redirect('budget_allocation')

        # Save Allocations
        BudgetAllocation.objects.create(
            department=department,
            approved_budget= approved_budget,
            total_allocated = amount
        )
        
        # Force update the approved budget’s updated_at field
        approved_budget.updated_at = timezone.now()
        approved_budget.save(update_fields=['updated_at'])
        
        
        messages.success(request, "Budget successfully allocated.")
        log_audit_trail(
            request=request,
            action='CREATE',
            model_name='BudgetAllocation',
            record_id=None,  # No specific record ID for creation
            detail=f"Allocated {intcomma(amount)} to {department} from approved budget: {approved_budget.title}."
        )
        return redirect('budget_allocation')
    
    # --- 📊 Load existing allocations for table view ---
    allocations = (
        BudgetAllocation.objects
        .select_related('approved_budget')
        .order_by('-allocated_at')
    )
    
    return render(request, "admin_panel/budget_allocation.html", {'approved_budgets': approved_budgets, 'departments': departments, 'budgets': allocations})


@role_required('admin', login_url='/admin/')
def institutional_funds(request):
    if request.method == 'POST':
        action = request.POST.get('action', 'create')
        
        if action == 'edit':
            # Handle Edit
            budget_id = request.POST.get('budget_id')
            title = request.POST.get('title')
            fiscal_year = request.POST.get('fiscal_year')  # Now editable
            amount = request.POST.get('amount')
            description = request.POST.get('description', '')
            new_documents = request.FILES.getlist('supporting_documents')
            remove_doc_ids = request.POST.getlist('remove_documents[]')
            
            try:
                budget = NewApprovedBudget.objects.get(id=budget_id)
                
                # Validate fiscal year
                if not fiscal_year:
                    messages.error(request, "Fiscal year is required.")
                    return redirect("institutional_funds")
                
                # Check if fiscal year is being changed and if new fiscal year already exists
                if budget.fiscal_year != fiscal_year:
                    if NewApprovedBudget.objects.filter(fiscal_year=fiscal_year).exclude(id=budget_id).exists():
                        messages.error(request, f"A budget for fiscal year {fiscal_year} already exists.")
                        return redirect("institutional_funds")
                
                # Validate amount
                amount = Decimal(amount)
                if amount <= 0:
                    messages.error(request, "Amount must be greater than zero.")
                    return redirect("institutional_funds")
                
                # Update budget fields
                budget.title = title
                budget.fiscal_year = fiscal_year  # Now updating fiscal year
                budget.amount = amount
                budget.description = description
                
                # Recalculate remaining budget if amount changed
                old_allocated = budget.amount - budget.remaining_budget
                budget.remaining_budget = amount - old_allocated
                
                budget.save()
                
                # Remove documents marked for deletion
                if remove_doc_ids:
                    SupportingDocument.objects.filter(
                        id__in=remove_doc_ids,
                        approved_budget=budget
                    ).delete()
                
                # Add new documents
                if new_documents:
                    allowed_formats = ['pdf', 'doc', 'docx', 'xls', 'xlsx']
                    max_file_size = 10 * 1024 * 1024
                    
                    for doc in new_documents:
                        if doc.size > max_file_size:
                            messages.warning(request, f"File '{doc.name}' exceeds 10MB limit and was skipped.")
                            continue
                        
                        ext = doc.name.split('.')[-1].lower()
                        if ext not in allowed_formats:
                            messages.warning(request, f"File '{doc.name}' has invalid format and was skipped.")
                            continue
                        
                        SupportingDocument.objects.create(
                            approved_budget=budget,
                            document=doc,
                            uploaded_by=request.user
                        )
                
                messages.success(request, f"Budget '{title}' for FY {fiscal_year} updated successfully!")
                
                log_audit_trail(
                    request=request,
                    action='UPDATE',
                    model_name='ApprovedBudget',
                    record_id=budget.id,
                    detail=f"Updated approved budget: {title} for fiscal year {fiscal_year}"
                )
                
                return redirect("institutional_funds")
                
            except NewApprovedBudget.DoesNotExist:
                messages.error(request, "Budget not found.")
                return redirect("institutional_funds")
            except Exception as e:
                messages.error(request, f"Error updating budget: {str(e)}")
                return redirect("institutional_funds")
    
        else:
            # Handle Create (existing code)
            title = request.POST.get('title')
            fiscal_year = request.POST.get('fiscal_year')
            amount = request.POST.get('amount')
            description = request.POST.get('description', '')
            supporting_documents = request.FILES.getlist('supporting_documents')  # Multiple files
            
            # Validation
            if not all([title, fiscal_year, amount]):
                messages.error(request, "Title, Fiscal Year, and Amount are required.")
                return redirect("institutional_funds")
            
            if not supporting_documents:
                messages.error(request, "At least one supporting document is required.")
                return redirect("institutional_funds")
            
            try:
                amount = Decimal(amount)
                if amount <= 0:
                    messages.error(request, "Amount must be greater than zero.")
                    return redirect("institutional_funds")
            except (ValueError, TypeError, decimal.InvalidOperation):
                messages.error(request, "Invalid amount entered.")
                return redirect("institutional_funds")
            
            # Check if budget for this fiscal year already exists
            if NewApprovedBudget.objects.filter(fiscal_year=fiscal_year).exists():
                messages.error(request, f"Approved budget for fiscal year {fiscal_year} already exists.")
                return redirect("institutional_funds")
            
            # Validate files
            allowed_formats = ['pdf', 'doc', 'docx', 'xls', 'xlsx']
            max_file_size = 10 * 1024 * 1024  # 10MB
            
            for doc in supporting_documents:
                # Check file size
                if doc.size > max_file_size:
                    messages.error(request, f"File '{doc.name}' exceeds 10MB limit.")
                    return redirect("institutional_funds")
                
                # Check file format
                ext = doc.name.split('.')[-1].lower()
                if ext not in allowed_formats:
                    messages.error(request, f"File '{doc.name}' has invalid format. Allowed: {', '.join(allowed_formats).upper()}")
                    return redirect("institutional_funds")
            
            # Create the approved budget
            try:
                budget = NewApprovedBudget.objects.create(
                    title=title,
                    fiscal_year=fiscal_year,
                    amount=amount,
                    remaining_budget=amount,
                    description=description,
                    created_by=request.user
                )
                
                # Create supporting document records for each uploaded file
                document_count = 0
                for doc in supporting_documents:
                    SupportingDocument.objects.create(
                        approved_budget=budget,
                        document=doc,
                        uploaded_by=request.user
                    )
                    document_count += 1
                
                messages.success(request, 
                    f"Approved budget '{title}' for FY {fiscal_year} successfully added with {document_count} supporting document(s).")
                
                log_audit_trail(
                    request=request,
                    action='CREATE',
                    model_name='ApprovedBudget',
                    record_id=budget.id,
                    detail=f"Created approved budget: {title} for fiscal year {fiscal_year} with amount ₱{intcomma(amount)}. Uploaded {document_count} supporting documents."
                )
                
                return redirect("institutional_funds")
                
            except Exception as e:
                messages.error(request, f"Error creating approved budget: {str(e)}")
                return redirect("institutional_funds")
    
    # GET request - Display budgets
    current_year = str(datetime.now().year)
    
    # Get year filter for summary cards (separate from table filters)
    summary_year = request.GET.get('summary_year', current_year)
    
    # Get budgets for summary statistics
    if summary_year == 'all':
        summary_budgets = NewApprovedBudget.objects.all()
    else:
        summary_budgets = NewApprovedBudget.objects.filter(fiscal_year=summary_year)
    
    # Calculate summary statistics based on selected year
    summary_stats = summary_budgets.aggregate(
        total_approved=Sum('amount'),
        total_remaining=Sum('remaining_budget'),
        total_count=Count('id')
    )
    
    total_approved_budget = summary_stats['total_approved'] or Decimal('0')
    total_remaining_budget = summary_stats['total_remaining'] or Decimal('0')
    total_budget_count = summary_stats['total_count'] or 0
    
    # Calculate utilization rate
    budget_utilization_rate = 0
    if total_approved_budget > 0:
        total_allocated = total_approved_budget - total_remaining_budget
        budget_utilization_rate = round((total_allocated / total_approved_budget) * 100, 1)
    
    # Get table budgets (with all table filters applied)
    approved_budgets_list = NewApprovedBudget.objects.order_by('-created_at')
    
    # Apply table filters (keep your existing filter logic)
    fiscal_year_filter = request.GET.get('fiscal_year')
    amount_min = request.GET.get('amount_min')
    amount_max = request.GET.get('amount_max')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search_query = request.GET.get('search')
    
    if fiscal_year_filter:
        approved_budgets_list = approved_budgets_list.filter(fiscal_year=fiscal_year_filter)
    
    if amount_min:
        try:
            approved_budgets_list = approved_budgets_list.filter(amount__gte=Decimal(amount_min))
        except:
            pass
    
    if amount_max:
        try:
            approved_budgets_list = approved_budgets_list.filter(amount__lte=Decimal(amount_max))
        except:
            pass
    
    if date_from:
        approved_budgets_list = approved_budgets_list.filter(created_at__date__gte=date_from)
    
    if date_to:
        approved_budgets_list = approved_budgets_list.filter(created_at__date__lte=date_to)
    
    if search_query:
        from django.db.models import Q
        approved_budgets_list = approved_budgets_list.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(fiscal_year__icontains=search_query)
        )
    
    # Get available years for dropdown
    available_years = NewApprovedBudget.objects.values_list('fiscal_year', flat=True).distinct().order_by('-fiscal_year')
    
    # Pagination
    paginator = Paginator(approved_budgets_list, 10)
    page_number = request.GET.get('page')
    
    try:
        approved_budgets = paginator.page(page_number)
    except PageNotAnInteger:
        approved_budgets = paginator.page(1)
    except EmptyPage:
        approved_budgets = paginator.page(paginator.num_pages)
    
    context = {
        'approved_budgets': approved_budgets,
        'total_approved_budget': total_approved_budget,
        'total_remaining_budget': total_remaining_budget,
        'total_budget_count': total_budget_count,
        'budget_utilization_rate': budget_utilization_rate,
        'available_years': available_years,
        'selected_year': summary_year,
        'current_year': current_year,
    }
    
    return render(request, 'admin_panel/institutional_funds.html', context)

@role_required('admin', login_url='/admin/')
def download_document(request, document_id):
    """Download supporting document with 'Save As' dialog"""
    document = get_object_or_404(SupportingDocument, id=document_id)
    
    # Check if file exists
    if not os.path.exists(document.document.path):
        raise Http404("Document file not found")
    
    # Open the file
    file_handle = open(document.document.path, 'rb')
    
    # Create response with attachment header to force download dialog
    response = FileResponse(file_handle)
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = f'attachment; filename="{document.file_name}"'
    
    return response

@role_required('admin', login_url='/admin/')
def export_budget_excel(request, budget_id):
    """Export single approved budget to Excel"""
    budget = get_object_or_404(NewApprovedBudget, id=budget_id)
    
    # Create workbook and worksheet
    wb = Workbook()
    ws = wb.active
    ws.title = f"Budget {budget.fiscal_year}"
    
    # Set column widths
    ws.column_dimensions['A'].width = 25
    ws.column_dimensions['B'].width = 40
    
    # Header styling
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=12)
    
    # Border styling
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Title
    ws.merge_cells('A1:B1')
    title_cell = ws['A1']
    title_cell.value = "APPROVED BUDGET REPORT"
    title_cell.font = Font(bold=True, size=14)
    title_cell.alignment = Alignment(horizontal='center', vertical='center')
    title_cell.fill = PatternFill(start_color="305496", end_color="305496", fill_type="solid")
    title_cell.font = Font(bold=True, color="FFFFFF", size=14)
    
    # Add some spacing
    current_row = 3
    
    # Budget Information Section
    ws[f'A{current_row}'] = "Budget Information"
    ws[f'A{current_row}'].font = header_font
    ws[f'A{current_row}'].fill = header_fill
    ws.merge_cells(f'A{current_row}:B{current_row}')
    current_row += 1
    
    # Budget details
    budget_data = [
        ("Title:", budget.title),
        ("Fiscal Year:", budget.fiscal_year),
        ("Approved Amount:", f"₱{budget.amount:,.2f}"),
        ("Remaining Balance:", f"₱{budget.remaining_budget:,.2f}"),
        ("Allocated Amount:", f"₱{budget.amount - budget.remaining_budget:,.2f}"),
        ("Created By:", budget.created_by.get_full_name() if budget.created_by else "N/A"),
        ("Created At:", budget.created_at.strftime("%B %d, %Y %I:%M %p")),
        ("Description:", budget.description or "N/A"),
    ]
    
    for label, value in budget_data:
        ws[f'A{current_row}'] = label
        ws[f'A{current_row}'].font = Font(bold=True)
        ws[f'A{current_row}'].border = thin_border
        
        ws[f'B{current_row}'] = value
        ws[f'B{current_row}'].border = thin_border
        current_row += 1
    
    # Supporting Documents Section
    current_row += 2
    ws[f'A{current_row}'] = "Supporting Documents"
    ws[f'A{current_row}'].font = header_font
    ws[f'A{current_row}'].fill = header_fill
    ws.merge_cells(f'A{current_row}:B{current_row}')
    current_row += 1
    
    # Document headers
    ws[f'A{current_row}'] = "File Name"
    ws[f'A{current_row}'].font = Font(bold=True)
    ws[f'A{current_row}'].fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    ws[f'A{current_row}'].border = thin_border
    
    ws[f'B{current_row}'] = "File Type"
    ws[f'B{current_row}'].font = Font(bold=True)
    ws[f'B{current_row}'].fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    ws[f'B{current_row}'].border = thin_border
    current_row += 1
    
    # List documents
    documents = budget.supporting_documents.all()
    if documents.exists():
        for doc in documents:
            ws[f'A{current_row}'] = doc.file_name
            ws[f'A{current_row}'].border = thin_border
            
            ws[f'B{current_row}'] = doc.file_format.upper()
            ws[f'B{current_row}'].border = thin_border
            current_row += 1
    else:
        ws[f'A{current_row}'] = "No documents attached"
        ws.merge_cells(f'A{current_row}:B{current_row}')
        ws[f'A{current_row}'].alignment = Alignment(horizontal='center')
        ws[f'A{current_row}'].font = Font(italic=True, color="999999")
        ws[f'A{current_row}'].border = thin_border
    
    # Footer
    current_row += 2
    ws[f'A{current_row}'] = f"Generated on: {budget.created_at.strftime('%B %d, %Y %I:%M %p')}"
    ws[f'A{current_row}'].font = Font(italic=True, size=9, color="666666")
    ws.merge_cells(f'A{current_row}:B{current_row}')
    
    # Prepare response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="Budget_{budget.fiscal_year}_{budget.title.replace(" ", "_")}.xlsx"'
    
    wb.save(response)
    return response

@role_required('admin', login_url='/admin/')
def bulk_export_budgets(request):
    """Export all approved budgets to Excel with filters applied"""
    
    # Get all budgets with same filters as the table view
    budgets = NewApprovedBudget.objects.order_by('-created_at')
    
    # Apply filters from GET parameters
    fiscal_year_filter = request.GET.get('fiscal_year')
    amount_min = request.GET.get('amount_min')
    amount_max = request.GET.get('amount_max')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search_query = request.GET.get('search')
    
    if fiscal_year_filter:
        budgets = budgets.filter(fiscal_year=fiscal_year_filter)
    
    if amount_min:
        try:
            budgets = budgets.filter(amount__gte=Decimal(amount_min))
        except:
            pass
    
    if amount_max:
        try:
            budgets = budgets.filter(amount__lte=Decimal(amount_max))
        except:
            pass
    
    if date_from:
        budgets = budgets.filter(created_at__date__gte=date_from)
    
    if date_to:
        budgets = budgets.filter(created_at__date__lte=date_to)
    
    if search_query:
        budgets = budgets.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(fiscal_year__icontains=search_query)
        )
    
    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Approved Budgets"
    
    # Set column widths
    ws.column_dimensions['A'].width = 8
    ws.column_dimensions['B'].width = 35
    ws.column_dimensions['C'].width = 12
    ws.column_dimensions['D'].width = 18
    ws.column_dimensions['E'].width = 18
    ws.column_dimensions['F'].width = 18
    ws.column_dimensions['G'].width = 15
    ws.column_dimensions['H'].width = 25
    ws.column_dimensions['I'].width = 22
    
    # Title
    ws.merge_cells('A1:I1')
    title_cell = ws['A1']
    title_cell.value = "APPROVED BUDGETS REPORT"
    title_cell.font = Font(bold=True, size=16, color="FFFFFF")
    title_cell.alignment = Alignment(horizontal='center', vertical='center')
    title_cell.fill = PatternFill(start_color="305496", end_color="305496", fill_type="solid")
    ws.row_dimensions[1].height = 30
    
    # Export info
    from django.utils import timezone
    ws.merge_cells('A2:I2')
    info_cell = ws['A2']
    info_cell.value = f"Generated on: {timezone.now().strftime('%B %d, %Y %I:%M %p')} | Total Records: {budgets.count()}"
    info_cell.font = Font(italic=True, size=10, color="666666")
    info_cell.alignment = Alignment(horizontal='center')
    
    # Headers
    headers = [
        'ID', 
        'Title', 
        'Fiscal Year', 
        'Amount (₱)', 
        'Remaining Balance (₱)', 
        'Allocated (₱)',
        'Utilization %',
        'Documents', 
        'Created At'
    ]
    
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col_num)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = thin_border
    
    ws.row_dimensions[4].height = 25
    
    # Data rows
    row_num = 5
    for budget in budgets:
        allocated = budget.amount - budget.remaining_budget
        utilization = (allocated / budget.amount * 100) if budget.amount > 0 else 0
        
        # Get document count and formats
        docs = budget.supporting_documents.all()
        doc_info = f"{docs.count()} file(s)"
        if docs.exists():
            formats = ", ".join(set([doc.file_format.upper() for doc in docs]))
            doc_info = f"{docs.count()} file(s) ({formats})"
        
        row_data = [
            budget.id,
            budget.title,
            budget.fiscal_year,
            float(budget.amount),
            float(budget.remaining_budget),
            float(allocated),
            round(utilization, 2),
            doc_info,
            budget.created_at.strftime('%b %d, %Y %I:%M %p')
        ]
        
        for col_num, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_num, column=col_num)
            cell.value = value
            cell.border = thin_border
            cell.alignment = Alignment(vertical='center')
            
            # Format currency columns
            if col_num in [4, 5, 6]:
                cell.number_format = '#,##0.00'
                cell.alignment = Alignment(horizontal='right', vertical='center')
            
            # Format percentage column
            if col_num == 7:
                cell.number_format = '0.00"%"'
                cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # Alternate row colors
            if row_num % 2 == 0:
                cell.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
        
        row_num += 1
    
    # Summary row
    row_num += 1
    summary_fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
    summary_font = Font(bold=True, size=11)
    
    # Calculate totals
    total_amount = sum(float(b.amount) for b in budgets)
    total_remaining = sum(float(b.remaining_budget) for b in budgets)
    total_allocated = total_amount - total_remaining
    avg_utilization = (total_allocated / total_amount * 100) if total_amount > 0 else 0
    
    ws.merge_cells(f'A{row_num}:C{row_num}')
    summary_label = ws.cell(row=row_num, column=1)
    summary_label.value = "TOTAL / AVERAGE"
    summary_label.font = summary_font
    summary_label.fill = summary_fill
    summary_label.alignment = Alignment(horizontal='right', vertical='center')
    summary_label.border = thin_border
    
    # Total amount
    cell = ws.cell(row=row_num, column=4)
    cell.value = total_amount
    cell.font = summary_font
    cell.fill = summary_fill
    cell.number_format = '#,##0.00'
    cell.alignment = Alignment(horizontal='right', vertical='center')
    cell.border = thin_border
    
    # Total remaining
    cell = ws.cell(row=row_num, column=5)
    cell.value = total_remaining
    cell.font = summary_font
    cell.fill = summary_fill
    cell.number_format = '#,##0.00'
    cell.alignment = Alignment(horizontal='right', vertical='center')
    cell.border = thin_border
    
    # Total allocated
    cell = ws.cell(row=row_num, column=6)
    cell.value = total_allocated
    cell.font = summary_font
    cell.fill = summary_fill
    cell.number_format = '#,##0.00'
    cell.alignment = Alignment(horizontal='right', vertical='center')
    cell.border = thin_border
    
    # Average utilization
    cell = ws.cell(row=row_num, column=7)
    cell.value = round(avg_utilization, 2)
    cell.font = summary_font
    cell.fill = summary_fill
    cell.number_format = '0.00"%"'
    cell.alignment = Alignment(horizontal='center', vertical='center')
    cell.border = thin_border
    
    # Empty cells for remaining columns
    for col in [8, 9]:
        cell = ws.cell(row=row_num, column=col)
        cell.fill = summary_fill
        cell.border = thin_border
    
    # Prepare response
    from datetime import datetime
    filename = f"Approved_Budgets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    wb.save(response)
    return response

@role_required('admin', login_url='/admin/')
def admin_logout(request):
    log_audit_trail(
        request=request,
        action='LOGOUT',
        model_name='User',
        record_id=request.user.id,
        detail=f"User {request.user.username} logged out."
    )
    logout(request)
    return redirect('admin_login')

@role_required('admin', login_url='/admin/')
def audit_trail(request):
    
    # Get all audit records and users
    audit_records = AuditTrail.objects.select_related('user').all()
    departments = User.objects.all().values_list('department', flat=True).distinct()
    
    # Filter by department
    department = request.GET.get('department')
    if department:
        audit_records = audit_records.filter(user__department=department)
    
    # Filter by action if specified
    action_filter = request.GET.get('action')
    if action_filter:
        audit_records = audit_records.filter(action=action_filter)
        
    # Filter by date range if specified
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        audit_records = audit_records.filter(
            timestamp__date__range=[start_date, end_date]
        )
        
    # Pagination
    paginator = Paginator(audit_records, 15)  # 15 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'action_choices': AuditTrail.ACTION_CHOICES,
        'departments': departments,
    }
    return render(request, 'admin_panel/audit_trail.html', context)

@role_required('admin', login_url='/admin/')
def budget_re_alignment(request):
    try:
        re_alignment_request = Budget_Realignment.objects.all()
    except Budget_Realignment.DoesNotExist:
        re_alignment_request = None
    return render(request, 'admin_panel/budget_re-alignment.html', {'re_alignment_request': re_alignment_request})

@role_required('admin', login_url='/admin/')
def handle_re_alignment_request_action(request, pk):
    req = get_object_or_404(Budget_Realignment, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            try:
                with transaction.atomic():
                    source_alloc = BudgetAllocation.objects.select_for_update().get(papp=req.source_papp)
                    target_alloc = BudgetAllocation.objects.select_for_update().get(papp=req.target_papp)
                    
                    if source_alloc.remaining_budget < req.amount:
                        messages.error(request, "Insufficient budget in source PAPP to realign.")
                        return redirect('budget_re_alignment')
                    
                    # Deduct from source and add to target
                    source_alloc.remaining_budget -= req.amount
                    target_alloc.remaining_budget += req.amount
                    
                    # Save both allocations
                    source_alloc.save()
                    target_alloc.save()

                    # Update request status
                    req.status = 'Approved'
                    req.approved_by = request.user
                    req.save()
                    
                    messages.success(request, f'Budget Realignment Request of {req.requested_by.department} has been approved.')
            except BudgetAllocation.DoesNotExist:
                messages.error(request, "Source or Target PAPP not found.")
            except Exception as e:
                messages.error(request, f"Something went wrong: {e}")
        elif action == 'reject':
            req.status = 'rejected'
            req.approved_by = request.user
            req.save()
            messages.error(request, f'Budget Realignment Request of {req.requested_by.department} has been rejected.')

        
        
        # action = request.POST.get('action')
        # if action == 'approve':
        #     req.status = 'Approved'
        #     messages.success(request, f'Budget Realignment Request of {req.requested_by.department} has been approved.')
        # elif action == 'reject':
        #     req.status = 'Rejected'
        #     messages.error(request, f'Budget Realignment Request of {req.requested_by.department} has been rejected.')
        # req.approved_by = request.user
        # req.save()
        
    return redirect('budget_realignment')

@role_required('admin', login_url='/admin/')
def pre_request_page(request):
    # Filter only PREs that were approved by the approving officer
    """
    View for the Admin to view all approved PREs from different departments.

    This view shows a table of all approved PREs, with the ability to filter by department.
    The table shows the department, submitted by, submitted on, budget allocation, and status of each PRE.
    """
    
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Partially Approved', 'Partially Approved'),
        ('Rejected', 'Rejected'),
        ('Approved', 'Approved')
    )
    
    pres = DepartmentPRE.objects.all().select_related('submitted_by', 'budget_allocation__approved_budget').order_by('-created_at')

    # Department filter
    dept = request.GET.get('department')
    if dept:
        pres = pres.filter(department=dept)
        
    # Status filter
    status = request.GET.get('status')
    if status:
        pres = pres.filter(status=status)

    # Distinct department list for filter select
    departments = DepartmentPRE.objects.all().values_list('department', flat=True).distinct()
    
    context = {
        'pres': pres,
        'departments': departments,
        'status_choices': STATUS_CHOICES,
    }

    return render(request, "admin_panel/pre_request.html", context)


@role_required('admin', login_url='/admin/')
def admin_preview_pre(request, pk: int):
    pre = get_object_or_404(DepartmentPRE.objects.select_related('submitted_by', 'budget_allocation__approved_budget'), pk=pk)

    # Reuse the same simple aggregation scheme as AO preview
    from decimal import Decimal

    def to_decimal(value):
        try:
            return Decimal(str(value)) if value not in (None, "") else Decimal('0')
        except Exception:
            return Decimal('0')

    payload = pre.data or {}

    sections_spec = [
        {
            'title': 'Personnel Services',
            'color_class': 'bg-yellow-100',
            'items': [
                {'label': 'Basic Salary', 'name': 'basic_salary'},
                {'label': 'Honoraria', 'name': 'honoraria'},
                {'label': 'Overtime Pay', 'name': 'overtime_pay'},
            ]
        },
        {
            'title': 'Maintenance and Other Operating Expenses',
            'color_class': 'bg-blue-100',
            'items': [
                {'label': 'Travelling Expenses', 'is_group': True},
                {'label': 'Travelling expenses-local', 'name': 'travel_local', 'indent': True},
                {'label': 'Travelling Expenses-foreign', 'name': 'travel_foreign', 'indent': True},
                {'label': 'Training and Scholarship expenses', 'is_group': True},
                {'label': 'Training Expenses', 'name': 'training_expenses', 'indent': True},
                {'label': 'Supplies and materials expenses', 'is_group': True},
                {'label': 'Office Supplies Expenses', 'name': 'office_supplies_expenses', 'indent': True},
                {'label': 'Accountable Form Expenses', 'name': 'accountable_form_expenses', 'indent': True},
                {'label': 'Agricultural and Marine Supplies Expenses', 'name': 'agri_marine_supplies_expenses', 'indent': True},
                {'label': 'Drugs and Medicines', 'name': 'drugs_medicines', 'indent': True},
                {'label': 'Medical, Dental & Laboratory Supplies Expenses', 'name': 'med_dental_lab_supplies_expenses', 'indent': True},
                {'label': 'Food Supplies Expenses', 'name': 'food_supplies_expenses', 'indent': True},
                {'label': 'Fuel, Oil and Lubricants Expenses', 'name': 'fuel_oil_lubricants_expenses', 'indent': True},
                {'label': 'Textbooks and Instructional Materials Expenses', 'name': 'textbooks_instructional_materials_expenses', 'indent': True},
                {'label': 'Construction Materials Expenses', 'name': 'construction_material_expenses', 'indent': True},
                {'label': 'Other Supplies & Materials Expenses', 'name': 'other_supplies_materials_expenses', 'indent': True},
                {'label': 'Semi-expendable Machinery Equipment', 'is_group': True},
                {'label': 'Machinery', 'name': 'semee_machinery', 'indent': True},
                {'label': 'Office Equipment', 'name': 'semee_office_equipment', 'indent': True},
                {'label': 'Information and Communications Technology Equipment', 'name': 'semee_information_communication', 'indent': True},
                {'label': 'Communications Equipment', 'name': 'semee_communications_equipment', 'indent': True},
                {'label': 'Disaster Response and Rescue Equipment', 'name': 'semee_drr_equipment', 'indent': True},
                {'label': 'Medical Equipment', 'name': 'semee_medical_equipment', 'indent': True},
                {'label': 'Printing Equipment', 'name': 'semee_printing_equipment', 'indent': True},
                {'label': 'Sports Equipment', 'name': 'semee_sports_equipment', 'indent': True},
                {'label': 'Technical and Scientific Equipment', 'name': 'semee_technical_scientific_equipment', 'indent': True},
                {'label': 'ICT Equipment', 'name': 'semee_ict_equipment', 'indent': True},
                {'label': 'Other Machinery and Equipment', 'name': 'semee_other_machinery_equipment', 'indent': True},
                {'label': 'Semi-expendable Furnitures and Fixtures', 'is_group': True},
                {'label': 'Furniture and Fixtures', 'name': 'furniture_fixtures', 'indent': True},
                {'label': 'Books', 'name': 'books', 'indent': True},
                {'label': 'Utility Expenses', 'is_group': True},
                {'label': 'Water Expenses', 'name': 'water_expenses', 'indent': True},
                {'label': 'Electricity Expenses', 'name': 'electricity_expenses', 'indent': True},
                {'label': 'Communication Expenses', 'is_group': True},
                {'label': 'Postage and Courier Services', 'name': 'postage_courier_services', 'indent': True},
                {'label': 'Telephone Expenses', 'name': 'telephone_expenses', 'indent': True},
                {'label': 'Telephone Expenses (Landline)', 'name': 'telephone_expenses_landline', 'indent': True},
                {'label': 'Internet Subscription Expenses', 'name': 'internet_subscription_expenses', 'indent': True},
                {'label': 'Cable, Satellite, Telegraph & Radio Expenses', 'name': 'cable_satellite_telegraph_radio_expenses', 'indent': True},
                {'label': 'Awards/Rewards and Prizes', 'is_group': True},
                {'label': 'Awards/Rewards Expenses', 'name': 'awards_rewards_expenses', 'indent': True},
                {'label': 'Prizes', 'name': 'prizes', 'indent': True},
                {'label': 'Survey, Research, Exploration, and Development Expenses', 'is_group': True},
                {'label': 'Survey Expenses', 'name': 'survey_expenses', 'indent': True},
                {'label': 'Survey, Research, Exploration, and Development expenses', 'name': 'survey_research_exploration_development_expenses', 'indent': True},
                {'label': 'Professional Services', 'is_group': True},
                {'label': 'Legal Services', 'name': 'legal_services', 'indent': True},
                {'label': 'Auditing Services', 'name': 'auditing_services', 'indent': True},
                {'label': 'Consultancy Services', 'name': 'consultancy_services', 'indent': True},
                {'label': 'Other Professional Services', 'name': 'other_professional_servies', 'indent': True},
                {'label': 'General Services', 'is_group': True},
                {'label': 'Security Services', 'name': 'security_services', 'indent': True},
                {'label': 'Janitorial Services', 'name': 'janitorial_services', 'indent': True},
                {'label': 'Other General Services', 'name': 'other_general_services', 'indent': True},
                {'label': 'Environment/Sanitary Services', 'name': 'environment/sanitary_services', 'indent': True},
                {'label': 'Repair and Maintenance', 'is_group': True},
                {'label': 'Repair & Maintenance - Land Improvements', 'name': 'repair_maintenance_land_improvements', 'indent': True},
                {'label': 'Repair & Maintenance - Buildings and Structures', 'is_group': True},
                {'label': 'Buildings', 'name': 'buildings', 'indent': True},
                {'label': 'School Buildings', 'name': 'school_buildings', 'indent': True},
                {'label': 'Hostels and Dormitories', 'name': 'hostel_dormitories', 'indent': True},
                {'label': 'Other Structures', 'name': 'other_structures', 'indent': True},
                {'label': 'Repairs and Maintenance - Machinery and Equipment', 'is_group': True},
                {'label': 'Machinery', 'name': 'repair_maintenance_machinery', 'indent': True},
                {'label': 'Office Equipment', 'name': 'repair_maintenance_office_equipment', 'indent': True},
                {'label': 'ICT Equipment', 'name': 'repair_maintenance_ict_equipment', 'indent': True},
                {'label': 'Agricultural and Forestry Equipment', 'name': 'repair_maintenance_agri_forestry_equipment', 'indent': True},
                {'label': 'Marine and Fishery Equipment', 'name': 'repair_maintenance_marine_fishery_equipment', 'indent': True},
                {'label': 'Airport Equipment', 'name': 'repair_maintenance_airport_equipment', 'indent': True},
                {'label': 'Communication Equipment', 'name': 'repair_maintenance_communication_equipment', 'indent': True},
                {'label': 'Disaster, Response and Rescue Equipment', 'name': 'repair_maintenance_drre_equipment', 'indent': True},
                {'label': 'Medical Equipment', 'name': 'repair_maintenance_medical_equipment', 'indent': True},
                {'label': 'Printing Equipment', 'name': 'repair_maintenance_printing_equipment', 'indent': True},
                {'label': 'Sports Equipment', 'name': 'repair_maintenance_sports_equipment', 'indent': True},
                {'label': 'Technical and Scientific Equipment', 'name': 'repair_maintenance_technical_scientific_equipment', 'indent': True},
                {'label': 'Other Machinery and Equipment', 'name': 'repair_maintenance_other_machinery_equipment', 'indent': True},
                {'label': 'Repairs and Maintenance - Transportation Equipment', 'is_group': True},
                {'label': 'Motor Vehicles', 'name': 'repair_maintenance_motor', 'indent': True},
                {'label': 'Other Transportation Equipment', 'name': 'repair_maintenance_other_transportation_equipment', 'indent': True},
                {'label': 'Repairs and Maintenance - Furniture & Fixtures', 'name': 'repair_maintenance_furniture_fixtures'},
                {'label': 'Repairs and Maintenance - Semi-Expendable Machinery and Equipment', 'name': 'repair_maintenance_semi_expendable_machinery_equipment'},
                {'label': 'Repairs and Maintenance - Other Property, Plant and Equipment', 'name': 'repair_maintenance_other_property_plant_equipment'},
                {'label': 'Taxes, Insurance Premiums and Other Fees', 'is_group': True},
                {'label': 'Taxes, Duties and Licenses', 'name': 'taxes_duties_licenses', 'indent': True},
                {'label': 'Fidelity Bond Premiums', 'name': 'fidelity_bond_premiums', 'indent': True},
                {'label': 'Insurance Expenses', 'name': 'insurance_expenses', 'indent': True},
                {'label': 'Labor and Wages', 'is_group': True},
                {'label': 'Labor and Wages', 'name': 'labor_wages', 'indent': True},
                {'label': 'Other Maintenance and Operating Expenses', 'is_group': True},
                {'label': 'Advertising Expenses', 'name': 'advertising_expenses', 'indent': True},
                {'label': 'Printing and Publication Expenses', 'name': 'printing_publication_expenses', 'indent': True},
                {'label': 'Representation Expenses', 'name': 'representation_expenses', 'indent': True},
                {'label': 'Transportation and Delivery Expenses', 'name': 'transportation_delivery_expenses', 'indent': True},
                {'label': 'Rent/Lease Expenses', 'name': 'rent/lease_expenses', 'indent': True},
                {'label': 'Membership Dues and contributions to organizations', 'name': 'membership_dues_contribute_to_org', 'indent': True},
                {'label': 'Subscription Expenses', 'name': 'subscription_expenses', 'indent': True},
                {'label': 'Website Maintenance', 'name': 'website_maintenance', 'indent': True},
                {'label': 'Other Maintenance and Operating Expenses', 'name': 'other_maintenance_operating_expenses', 'indent': True},
            ]
        },
        {
            'title': 'Capital Outlays',
            'color_class': 'bg-green-100',
            'items': [
                # Placeholder; extend as needed
                {'label': 'Land', 'is_group': True},
                {'label': 'Land', 'name': 'land', 'indent': True},
                {'label': 'Land Improvements', 'is_group': True},
                {'label': 'Land Improvements, Aquaculture Structure', 'name': 'land_improvements_aqua_structure', 'indent': True},
                {'label': 'Infrastructure Assets', 'is_group': True},
                {'label': 'Water Supply Systems', 'name': 'water_supply_systems', 'indent': True},
                {'label': 'Power Supply Systems', 'name': 'power_supply_systems', 'indent': True},
                {'label': 'Other Infrastructure Assets', 'name': 'other_infra_assets', 'indent': True},
                {'label': 'Building and Other Structures', 'is_group': True},
                {'label': 'Building', 'name': 'bos_building', 'indent': True},
                {'label': 'School Buildings', 'name': 'bos_school_buildings', 'indent': True},
                {'label': 'Hostels and Dormitories', 'name': 'bos_hostels_dorm', 'indent': True},
                {'label': 'Other Structures', 'name': 'other_structures', 'indent': True},
                {'label': 'Machinery and Equipment', 'is_group': True},
                {'label': 'Machinery', 'name': 'me_machinery', 'indent': True},
                {'label': 'Office Equipment', 'name': 'me_office_equipment', 'indent': True},
                {'label': 'Information and Communication Technology Equipment', 'name': 'me_ict_equipment', 'indent': True},
                {'label': 'Communication Equipment', 'name': 'me_communication_equipment', 'indent': True},
                {'label': 'Disaster Response and Rescue Equipment', 'name': 'me_drre', 'indent': True},
                {'label': 'Medical Equipment', 'name': 'me_medical_equipment', 'indent': True},
                {'label': 'Printing Equipment', 'name': 'me_printing_equipment', 'indent': True},
                {'label': 'Sports Equipment', 'name': 'me_sports_equipment', 'indent': True},
                {'label': 'Technical and Scientific Equipment', 'name': 'me_technical_scientific_equipment', 'indent': True},
                {'label': 'Other Machinery and Equipment', 'name': 'me_other_machinery_equipment', 'indent': True},
                {'label': 'Transportation Equipment', 'is_group': True},
                {'label': 'Motor Vehicles', 'name': 'te_motor', 'indent': True},
                {'label': 'Other Transportation Equipment', 'name': 'te_other_transpo_equipment', 'indent': True},
                {'label': 'Furniture, Fixtures and Books', 'is_group': True},
                {'label': 'Furniture and Fixtures', 'name': 'ffb_furniture_fixtures', 'indent': True},
                {'label': 'Books', 'name': 'ffb_books', 'indent': True},
                {'label': 'Construction in Progress', 'is_group': True},
                {'label': 'Construction in Progress - Land Improvements', 'name': 'cp_land_improvements', 'indent': True},
                {'label': 'Construction in Progress - Infrastructure Assets', 'name': 'cp_infra_assets', 'indent': True},
                {'label': 'Construction in Progress - Buildings and Other Structures', 'name': 'cp_building_other_structures', 'indent': True},
                {'label': 'Construction in Progress - Leased Assets', 'name': 'cp_leased_assets', 'indent': True},
                {'label': 'Construction in Progress - Leased Assets Improvements', 'name': 'cp_leased_assets_improvements', 'indent': True},
                {'label': 'Intangible Assets', 'is_group': True},
                {'label': 'Computer Software', 'name': 'ia_computer_software', 'indent': True},
                {'label': 'Websites', 'name': 'ia_websites', 'indent': True},
                {'label': 'Other Tangible Assets', 'name': 'ia_other_tangible_assets', 'indent': True},
                
            ]
        },
    ]

    sections = []
    for spec in sections_spec:
        items = []
        for row in spec['items']:
            if row.get('is_group'):
                items.append({'is_group': True, 'label': row['label']})
            else:
                name = row['name']
                q1 = to_decimal(payload.get(f"{name}_q1"))
                q2 = to_decimal(payload.get(f"{name}_q2"))
                q3 = to_decimal(payload.get(f"{name}_q3"))
                q4 = to_decimal(payload.get(f"{name}_q4"))
                total = q1 + q2 + q3 + q4
                items.append({'label': row['label'], 'indent': row.get('indent', False), 'q1': q1, 'q2': q2, 'q3': q3, 'q4': q4, 'total': total})
        from decimal import Decimal as _D
        total_q1 = sum((it['q1'] for it in items if not it.get('is_group')), _D('0'))
        total_q2 = sum((it['q2'] for it in items if not it.get('is_group')), _D('0'))
        total_q3 = sum((it['q3'] for it in items if not it.get('is_group')), _D('0'))
        total_q4 = sum((it['q4'] for it in items if not it.get('is_group')), _D('0'))
        total_overall = sum((it['total'] for it in items if not it.get('is_group')), _D('0'))
        sections.append({'title': spec['title'], 'color_class': spec['color_class'], 'items': items, 'total_q1': total_q1, 'total_q2': total_q2, 'total_q3': total_q3, 'total_q4': total_q4, 'total_overall': total_overall})

    from decimal import Decimal as _DD
    grand_total_q1 = sum((sec['total_q1'] for sec in sections), _DD('0'))
    grand_total_q2 = sum((sec['total_q2'] for sec in sections), _DD('0'))
    grand_total_q3 = sum((sec['total_q3'] for sec in sections), _DD('0'))
    grand_total_q4 = sum((sec['total_q4'] for sec in sections), _DD('0'))
    grand_total_overall = sum((sec['total_overall'] for sec in sections), _DD('0'))

    return render(request, 'admin_panel/preview_pre.html', {
        'pre': pre,
        'sections': sections,
        'grand_total_q1': grand_total_q1,
        'grand_total_q2': grand_total_q2,
        'grand_total_q3': grand_total_q3,
        'grand_total_q4': grand_total_q4,
        'grand_total_overall': grand_total_overall,
        'prepared_by': pre.submitted_by.fullname,
        'certified_by': pre.certified_by_name,
        'approved_by': pre.approved_by_name,
    })


@role_required('admin', login_url='/admin/')
def admin_handle_pre_action(request, pk: int):
    pre = get_object_or_404(DepartmentPRE, pk=pk)
    budget_allocation = get_object_or_404(BudgetAllocation, id=pre.budget_allocation_id)
    # budget_allocation = BudgetAllocation.objects.filter(department=pre.department, id=pre.budget_allocation_id).first
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            pre.status = 'Partially Approved'
            pre.approved_by_admin = True
            audit_trail_action = 'Partially APPROVE'
        elif action == 'reject':
            pre.status = 'Rejected'
            pre.approved_by_admin = False
            budget_allocation.is_compiled = False
            budget_allocation.save(update_fields=['is_compiled'])
            audit_trail_action = 'REJECT'
        pre.save()
        log_audit_trail(
            request=request,
            action=audit_trail_action,
            model_name='DepartmentPRE',
            record_id=pre.id,
            detail=f"Admin {action} a PRE with ID {pre.id} from department {pre.department}."
        )
    return redirect('pre_request_page')

@role_required('admin', login_url='/admin/')
def preview_purchase_request(request, pk:int):
    pr = get_object_or_404(PurchaseRequest.objects.select_related('requested_by', 'budget_allocation__approved_budget', 'source_pre'),
        pk=pk,
    )
    
    return render(request, 'admin_panel/preview_purchase_request.html', {
        'pr': pr,
    })
    
@role_required('admin', login_url='/admin/')
def department_activity_design(request):
    STATUS = (
        ('PENDING', 'Pending'),
        ('PARTIALLY APPROVED', 'Partially Approved'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected')
    )
    
    # Get all the activity design request
    activity_designs = ActivityDesign.objects.all().select_related('requested_by', 'budget_allocation__approved_budget')
    
    # Get distinct departments from non-staff, non-approving officer users
    departments = (
        User.objects.filter(is_staff=False, is_approving_officer=False)
        .exclude(department__isnull=True)
        .values_list('department', flat=True)
        .distinct()
    )

    department_filter = request.GET.get('department')
    if department_filter:
        activity_designs = activity_designs.filter(requested_by__department=department_filter)

    status_filter = request.GET.get('status')
    if status_filter:
        activity_designs = activity_designs.filter(status=status_filter)
        
    # Handle possible DoesNotExist gracefully (though .filter() never raises it)
    context = {
        'activity_designs': activity_designs,
        'departments': departments,
        'selected_department': department_filter,
        'status_choices': STATUS,
    }
    return render(request, 'admin_panel/departments_ad_request.html', context)

@role_required('admin', login_url='/admin/')
def admin_preview_activity_design(request, pk: int):
    activity_design = get_object_or_404(ActivityDesign, id=pk)
    return render(request, 'admin_panel/preview_activity_design.html', {'activity': activity_design})

@role_required('admin', login_url='/admin/')
def handle_activity_design_request(request, pk:int):
    """
    View for Admin to approve or reject department activity designs.
    Updates the status of the activity design and associated budget allocation.
    """
    activity_design = get_object_or_404(ActivityDesign, id=pk)

    if request.method == 'POST':
        action = request.POST.get('action')

        allocation = activity_design.budget_allocation
        if action == 'approve':
            if allocation is None:
                messages.error(request, 'No budget allocation linked to this activity design.')
                return redirect('department_activity_design')
            
            activity_design.status = 'Partially Approved'
            activity_design.approved_by_admin = True
            
            log_audit_trail(
                request=request,
                action='APPROVE',
                model_name='ActivityDesign',
                record_id=activity_design.id,
                detail=f'Activity Design id: {activity_design.id} have been Partially Approved by Admin'
            )
        elif action == 'reject':
            try:
                allocations = ActivityDesignAllocations.objects.filter(activity_design=activity_design).select_related('pre_line_item')
                
                total_released = Decimal('0')
                released_details = []
                
                for ad_allocation in allocations:
                    line_item = ad_allocation.pre_line_item
                    allocated_amount = ad_allocation.allocated_amount
                    
                    line_item.consumed_amount -= allocated_amount
                    line_item.save()
                    
                    total_released += allocated_amount
                    released_details.append(f"{line_item.item_key} {line_item.quarter}: ₱{allocated_amount}")
                    
                    print(f"Released ₱{allocated_amount} back to {line_item.item_key} {line_item.quarter}")
                    
                # Delete allocations after reversal
                allocations.delete()
                
            except Exception as e:
                print(f"DEBUG ERROR: {e}")
                messages.error(request, f"Error processing rejection: {e}")
                return redirect('ao_activity_design_page')
            
            activity_design.status = 'Rejected'
            activity_design.approved_by_admin = False
            
            log_audit_trail(
                request=request,
                action='REJECT',
                model_name='ActivityDesign',
                record_id=activity_design.id,
                detail=f'Activity Design id: {activity_design.id} have been Rejected by Admin'
            )

        activity_design.save(update_fields=['status', 'updated_at', 'approved_by_admin'])

    return redirect('department_activity_design')


@role_required('admin', login_url='/admin/')
def pre_budget_realignment_admin(request):
    """Admin view for PRE budget realignment requests"""
    
    # Get all realignment requests
    realignment_requests = PREBudgetRealignment.objects.select_related(
        'requested_by', 'approved_by', 'source_pre', 'target_pre'
    ).order_by('-created_at')
    
    status_counts = {
        'total': realignment_requests.count(),
        'pending': realignment_requests.filter(status='Pending').count(),
        'approved': realignment_requests.filter(status='Approved').count(),
        'partially_approved': realignment_requests.filter(status='Partially Approved').count(),
        'rejected': realignment_requests.filter(status='Rejected').count(),
    }
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        realignment_requests = realignment_requests.filter(status=status_filter)
    
    context = {
        'realignment_requests': realignment_requests,
        'status_filter': status_filter,
        'status_choices': PREBudgetRealignment.STATUS_CHOICES,
        'status_counts': status_counts,
    }
    
    return render(request, 'admin_panel/pre_budget_realignment.html', context)

@role_required('admin', login_url='/admin/')
def handle_pre_realignment_admin_action(request, pk):
    """Handle approve/reject actions for PRE realignment requests"""
    
    realignment = get_object_or_404(PREBudgetRealignment, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'partial_approve':
            realignment.status='Partially Approved'
            realignment.approved_by_admin = True
            realignment.partial_approved_by = request.user
            realignment.save()
            
            # Log audit trail
            log_audit_trail(
                request=request,
                action='PARTIAL_APPROVE',
                model_name='PREBudgetRealignment',
                record_id=realignment.id,
                detail=f'Partially approved budget realignment: {realignment.source_item_display} → {realignment.target_item_display} (₱{realignment.amount:,.2f})',
            )
            
            messages.success(request, f'Budget realignment partially approved.')
        
        elif action == 'reject':
            realignment.status = 'Rejected'
            realignment.approved_by = request.user
            realignment.save()
            
            # Log audit trail
            log_audit_trail(
                request=request,
                action='REJECT',
                model_name='PREBudgetRealignment',
                record_id=realignment.id,
                detail=f'Rejected budget realignment: {realignment.source_item_display} → {realignment.target_item_display} (₱{realignment.amount:,.2f})',
            )
            
            messages.success(request, 'Budget realignment rejected.')
    
    return redirect('pre_budget_realignment_admin')