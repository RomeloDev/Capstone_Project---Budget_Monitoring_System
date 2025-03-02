from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import redirect
from apps.admin_panel.models import BudgetAllocation
from .models import PurchaseRequest
from decimal import Decimal
from django.contrib import messages

# Create your views here.
@login_required
def user_dashboard(request):
    try:
        # Get the budget allocation of the logged-in user
        budget = BudgetAllocation.objects.get(assigned_user=request.user)
        # Get the purchase requests of the logged in user
        purchase_requests = PurchaseRequest.objects.filter(user=request.user)
        approved_requests_count = purchase_requests.filter(status="Approved").count()
    except BudgetAllocation.DoesNotExist or PurchaseRequest.DoesNotExist:
        budget = None  # If no budget is assigned to the user
        purchase_requests = None  # If no purchase requests are made by the user
        approved_requests_count = 0  # No pending requests
        
    return render(request, 'end_user_app/dashboard.html', {
        'budget': budget, 
        'purchase_requests': purchase_requests,
        'approved_requests_count': approved_requests_count,
        })

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
    try:
        purchase_requests = PurchaseRequest.objects.filter(user=request.user)
    except PurchaseRequest.DoesNotExist:
        purchase_requests = None
    return render(request, 'end_user_app/purchase_request.html', {'purchase_requests': purchase_requests})

@login_required
def settings(request):
    return render(request, 'end_user_app/settings.html')

@login_required
def end_user_logout(request):
    logout(request)
    return redirect('end_user_login') # redirect to the login page

@login_required 
def purchase_request_form(request):
    if request.method == 'POST':
        item_name = request.POST.get('item_name')
        amount = request.POST.get('amount')
        reason = request.POST.get('reason')
        
        # Convert amount to decimal
        try:
            amount = Decimal(amount)
        except (ValueError, TypeError):
            messages.error(request, "Invalid amount entered.")
            return redirect("purchase_request_form")
        
        budget_allocated = BudgetAllocation.objects.filter(assigned_user = request.user).first()
        if not budget_allocated:
            messages.error(request, "No allocated budget.")
            return redirect("purchase_request_form")
        
        remaining_budget = budget_allocated.remaining_budget
        
        if remaining_budget >= amount:
            create_purchase_request = PurchaseRequest.objects.create(
                item_name = item_name,
                amount = amount,
                reason = reason,
                user = request.user
            )
            create_purchase_request.save()
            
            budget_allocated.remaining_budget -= amount
            budget_allocated.spent += amount
            budget_allocated.save()
            
            return redirect('user_purchase_request')
        
        else:
            messages.error(request, "Insufficient budget.")
        
    return render(request, 'end_user_app/purchase_request_form.html')