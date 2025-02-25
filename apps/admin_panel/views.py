from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from apps.users.models import User
from .models import BudgetAllocation

# Create your views here.
@login_required
def admin_dashboard(request):
    return render(request, 'admin_panel/dashboard.html')

@login_required
def client_accounts(request):
    return render(request, 'admin_panel/client_accounts.html')

@login_required
def departments_request(request):
    return render(request, 'admin_panel/department_request.html')

@login_required
def budget_allocation(request):
    if request.method == 'POST':
        department = request.POST.get('department')
        amount = request.POST.get('amount')

        # Find the user assigned to the department (assuming one user per department)
        assigned_user = User.objects.filter(department=department, is_staff=False).first()

        # Get or create budget for the department
        budget, created = BudgetAllocation.objects.get_or_create(department=department)
        
        # Update values
        budget.total_allocated = amount
        budget.assigned_user = assigned_user  # Automatically assign based on department
        budget.save()

        return redirect("budget_allocation")  # Reload the page after saving

    # Fetch all budget allocations
    budgets = BudgetAllocation.objects.all()

    # Fetch distinct department names (only for selection)
    departments = User.objects.filter(is_staff=False).values_list('department', flat=True).distinct()
    
    return render(request, "admin_panel/budget_allocation.html", {
        "budgets": budgets,
        "departments": departments
    })


@login_required
def admin_logout(request):
    logout(request)
    return redirect('admin_login')