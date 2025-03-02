from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from apps.users.models import User
from .models import BudgetAllocation, Budget
from apps.users.models import User
from django.contrib import messages
from decimal import Decimal
from apps.end_user_app.models import PurchaseRequest

# Create your views here.
@login_required
def admin_dashboard(request):
    return render(request, 'admin_panel/dashboard.html')

@login_required
def client_accounts(request):
    try:
        end_users = User.objects.filter(is_staff=False)
    except User.DoesNotExist:
        end_users = None
    return render(request, 'admin_panel/client_accounts.html', {'end_users': end_users})

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
        
        if action == "approve":
            purchase_request.status = "Approved"
        elif action == "reject":
            purchase_request.status = "Rejected"
        
        purchase_request.save()
        
    return redirect('department_request')

@login_required
def budget_allocation(request):
    if request.method == 'POST':
        department = request.POST.get('department')
        amount = request.POST.get('amount')
        
        # Convert amount to decimal
        try:
            amount = Decimal(amount)
        except (ValueError, TypeError):
            messages.error(request, "Invalid amount entered.")
            return redirect("budget_allocation")

        # Find the user assigned to the department (assuming one user per department)
        assigned_user = User.objects.filter(department=department, is_staff=False).first()
        
        # Get the current remaining fund (assuming only one budget exists)
        budget_instance = Budget.objects.first()
        if not budget_instance:
            messages.error(request, "No institutional budget found")
            return redirect("budget_allocation")
        
        remaining_fund = budget_instance.remaining_budget
        
        if remaining_fund >= amount:
            # Get or create budget for the department
            budget, created = BudgetAllocation.objects.get_or_create(department=department)
            
            # Update values
            budget.total_allocated += amount
            budget.remaining_budget = budget.total_allocated - budget.spent
            budget.assigned_user = assigned_user  # Automatically assign based on department
            budget.save()
            
            # Update the remaining balance of total fund of the institution
            budget_instance.remaining_budget -= amount
            budget_instance.save()

            return redirect("budget_allocation")  # Reload the page after saving
        else:
            messages.error(request, "Insufficient Budget")

    # Fetch all budget allocations
    budgets = BudgetAllocation.objects.all()

    # Fetch distinct department names (only for selection)
    departments = User.objects.filter(is_staff=False).values_list('department', flat=True).distinct()
    
    return render(request, "admin_panel/budget_allocation.html", {
        "budgets": budgets,
        "departments": departments
    })
    
@login_required
def institutional_funds(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        total_budget = request.POST.get('total_budget')
        
        add_budget = Budget.objects.create(
            title = title,
            total_fund = total_budget,
            remaining_budget = total_budget
        )
        add_budget.save()
        
        return redirect('institutional_funds')
    data_funds = Budget.objects.all()
    return render(request, 'admin_panel/institutional_funds.html', {"data_funds": data_funds})

@login_required
def admin_logout(request):
    logout(request)
    return redirect('admin_login')