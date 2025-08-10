from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from apps.users.models import User
from .models import BudgetAllocation, Budget, ApprovedBudget
from apps.users.models import User
from django.contrib import messages
from decimal import Decimal
from apps.end_user_app.models import PurchaseRequest, Budget_Realignment, DepartmentPRE
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
        total_pending_realignment_request = Budget_Realignment.objects.filter(status='pending').count()
        total_approved_realignment_request = Budget_Realignment.objects.filter(status='approved').count()
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
                return redirect('department_request')
            if allocation.remaining_budget < (purchase_request.total_amount or 0):
                messages.error(request, 'Insufficient remaining budget to approve this request.')
                return redirect('department_request')
            allocation.spent = (allocation.spent or 0) + (purchase_request.total_amount or 0)
            allocation.save(update_fields=['spent', 'updated_at'])
            purchase_request.pr_status = 'submitted'
            purchase_request.submitted_status = 'approved'
        elif action == 'reject':
            purchase_request.pr_status = 'submitted'
            purchase_request.submitted_status = 'rejected'

        purchase_request.save(update_fields=['pr_status', 'submitted_status', 'updated_at'])

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
    # Filter only PREs that were approved by the approving officer
    """
    View for the Admin to view all approved PREs from different departments.

    This view shows a table of all approved PREs, with the ability to filter by department.
    The table shows the department, submitted by, submitted on, budget allocation, and status of each PRE.
    """
    pres = DepartmentPRE.objects.filter(approved_by_approving_officer=True, approved_by_admin=False, status='Approved').select_related('submitted_by', 'budget_allocation__approved_budget').order_by('-created_at')

    # Department filter
    dept = request.GET.get('department')
    if dept:
        pres = pres.filter(department=dept)

    # Distinct department list for filter select
    departments = DepartmentPRE.objects.filter(approved_by_approving_officer=True).values_list('department', flat=True).distinct()

    return render(request, "admin_panel/pre_request.html", {
        'pres': pres,
        'departments': departments,
    })


@login_required
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
        {'title': 'Personnel Services', 'color_class': 'bg-yellow-100', 'items': [
            {'label': 'Basic Salary', 'name': 'basic_salary'},
            {'label': 'Honoraria', 'name': 'honoraria'},
            {'label': 'Overtime Pay', 'name': 'overtime_pay'},
        ]},
        {'title': 'Maintenance and Other Operating Expenses', 'color_class': 'bg-blue-100', 'items': [
            {'label': 'Travelling Expenses', 'is_group': True},
            {'label': 'Travelling expenses-local', 'name': 'travel_local', 'indent': True},
            {'label': 'Travelling Expenses-foreign', 'name': 'travel_foreign', 'indent': True},
        ]},
        {'title': 'Capital Outlays', 'color_class': 'bg-green-100', 'items': [
            {'label': 'Land', 'is_group': True},
            {'label': 'Land', 'name': 'land', 'indent': True},
        ]},
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
        'prepared_by': pre.prepared_by_name,
        'certified_by': pre.certified_by_name,
        'approved_by': pre.approved_by_name,
    })


@login_required
def admin_handle_pre_action(request, pk: int):
    pre = get_object_or_404(DepartmentPRE, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            pre.status = 'Approved'
            pre.approved_by_admin = True
        elif action == 'reject':
            pre.status = 'Rejected'
            pre.approved_by_admin = False
        pre.save()
    return redirect('pre_request_page')