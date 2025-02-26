from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import redirect
from apps.admin_panel.models import BudgetAllocation

# Create your views here.
@login_required
def user_dashboard(request):
    try:
        # Get the budget allocation of the logged-in user
        budget = BudgetAllocation.objects.get(assigned_user=request.user)
    except BudgetAllocation.DoesNotExist:
        budget = None  # If no budget is assigned to the user
        
    return render(request, 'end_user_app/dashboard.html', {'budget': budget})

@login_required
def view_budget(request):
    try:
        # Get the budget allocation of the logged-in user
        budget = BudgetAllocation.objects.get(assigned_user=request.user)
    except BudgetAllocation.DoesNotExist:
        budget = None  # If no budget is assigned to the user
    
    return render(request, 'end_user_app/view_budget.html', {'budget': budget})

@login_required
def purchase_request(request):
    return render(request, 'end_user_app/purchase_request.html')

@login_required
def settings(request):
    return render(request, 'end_user_app/settings.html')

@login_required
def end_user_logout(request):
    logout(request)
    return redirect('end_user_login') # redirect to the login page
    