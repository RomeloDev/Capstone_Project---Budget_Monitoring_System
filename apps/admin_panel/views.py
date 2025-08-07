from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from apps.users.models import User
from .models import BudgetAllocation, Budget, ApprovedBudget
from apps.users.models import User
from django.contrib import messages
from decimal import Decimal
from apps.end_user_app.models import PurchaseRequest, Budget_Realignment
from apps.users.models import User
from django.db import transaction
from django.db.models import Sum
from django.template.defaultfilters import floatformat
from django.contrib.humanize.templatetags.humanize import intcomma
from django.utils import timezone



# Create your views here.
@login_required
def admin_dashboard(request):
    try:
        end_users_total = User.objects.filter(is_staff=False, is_approving_officer=True).count()
        total_budget = Budget.objects.aggregate(Sum('total_fund'))['total_fund__sum']
        total_pending_realignment_request = Budget_Realignment.objects.filter(status='Pending').count()
        total_approved_realignment_request = Budget_Realignment.objects.filter(status='Approved').count()
        budget_allocated = BudgetAllocation.objects.all()
    except:
        end_users_total = 0
        total_budget = 0
        total_pending_realignment_request = 0
        total_approved_realignment_request = 0
        budget_allocated = None



    return render(request, 'admin_panel/dashboard.html', {'end_users_total': end_users_total,
    'total_budget': total_budget, 
    'total_pending_realignment_request': total_pending_realignment_request, 'total_approved_realignment_request': total_approved_realignment_request,
    'budget_allocated': budget_allocated,
    'intcomma': intcomma
    })

@login_required
def client_accounts(request):
    try:
        end_users = User.objects.filter(is_staff=False)
    except User.DoesNotExist:
        end_users = None
    return render(request, 'admin_panel/client_accounts.html', {'end_users': end_users})

@login_required
def register_account(request):
    if request.method == "POST":
         # Retrieval of value in input fields
        username = request.POST.get('username')
        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        department = request.POST.get('department')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm-password')
        
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
            user = User.objects.create_user(username=username, fullname=fullname, email=email, password=password, department=department)
            return render(request, "admin_panel/client_accounts.html", {'success': "Account registered successfully!"})

@login_required
def departments_request(request):
    try:
        users_purchase_requests = PurchaseRequest.objects.all()
    except PurchaseRequest.DoesNotExist:
        users_purchase_requests = None
        
    return render(request, 'admin_panel/department_request.html', {'users_purchase_requests': users_purchase_requests})

@login_required
def handle_departments_request(request, request_id):
    purchase_request = get_object_or_404(PurchaseRequest, id=request_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        budget_allocated = BudgetAllocation.objects.get(assigned_user=purchase_request.user)
        
        if action == "approve":
            purchase_request.status = "Approved"
        elif action == "reject":
            budget_allocated.remaining_budget += purchase_request.amount
            budget_allocated.save()
            purchase_request.status = "Rejected"
        
        purchase_request.save()
        
    return redirect('department_request')

@login_required
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
        return redirect('budget_allocation')
    
    # --- 📊 Load existing allocations for table view ---
    allocations = (
        BudgetAllocation.objects
        .select_related('approved_budget')
        .order_by('-allocated_at')
    )
    
    return render(request, "admin_panel/budget_allocation.html", {'approved_budgets': approved_budgets, 'departments': departments, 'budgets': allocations})
    
# This is the Approved Budget View
@login_required
def institutional_funds(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        period = request.POST.get('period')
        amount = request.POST.get('amount')
        
        # Validation
        if not title or not period or not amount:
            messages.error(request, "All fields are required.")
            return redirect("institutional_funds")
        else:
            try:
                amount = Decimal(amount)
            except (ValueError, TypeError):
                messages.error(request, "Invalid amount entered.")
                return redirect("institutional_funds")
        
            # Create the approved budget
            ApprovedBudget.objects.create(
                title=title,
                period=period,
                amount=amount
            )
            messages.success(request, "Approved budget successfully added.")
            return redirect("institutional_funds")
        
    approved_budgets = ApprovedBudget.objects.order_by('-created_at')
    return render(request, 'admin_panel/institutional_funds.html', {'approved_budgets': approved_budgets})

@login_required
def admin_logout(request):
    logout(request)
    return redirect('admin_login')

@login_required
def audit_trail(request):
    return render(request, 'admin_panel/audit_trail.html')

@login_required
def budget_re_alignment(request):
    try:
        re_alignment_request = Budget_Realignment.objects.all()
    except Budget_Realignment.DoesNotExist:
        re_alignment_request = None
    return render(request, 'admin_panel/budget_re-alignment.html', {'re_alignment_request': re_alignment_request})

@login_required
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

@login_required
def pre_request_page(request):
    return render(request, "admin_panel/pre_request.html")