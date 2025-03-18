from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import redirect, get_object_or_404
from apps.admin_panel.models import BudgetAllocation
from .models import PurchaseRequest, PurchaseRequestItems
from decimal import Decimal
from django.contrib import messages

# Create your views here.
@login_required
def user_dashboard(request):
    try:
        # Get the budget allocation of the logged-in user
        budget = BudgetAllocation.objects.get(assigned_user=request.user)
        # Get the purchase requests of the logged in user
        # purchase_requests = PurchaseRequest.objects.filter(user=request.user)
        # approved_requests_count = purchase_requests.filter(status="Approved").count()
    except BudgetAllocation.DoesNotExist or PurchaseRequest.DoesNotExist:
        budget = None  # If no budget is assigned to the user
        # purchase_requests = None  # If no purchase requests are made by the user
        # approved_requests_count = 0  # No pending requests
        
    # return render(request, 'end_user_app/dashboard.html', {
    #     'budget': budget, 
    #     'purchase_requests': purchase_requests,
    #     'approved_requests_count': approved_requests_count,
    #     })
    
    return render(request, 'end_user_app/dashboard.html', {
        'budget': budget, 
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
    # try:
    #     purchase_requests = PurchaseRequest.objects.filter(user=request.user)
    # except PurchaseRequest.DoesNotExist:
    #     purchase_requests = None
    return render(request, 'end_user_app/purchase_request.html')

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
        # Purchase Request Headings Logic
        if 'entity_name' in request.POST:
            entity_name = request.POST.get('entity_name')
            fund_cluster = request.POST.get('fund_cluster')
            office_section = request.POST.get('office_section')
            pr_no = request.POST.get('pr_no')
            responsibility_center_code = request.POST.get('responsiblity_center_code')
            purpose = request.POST.get('purpose')
            
            purchase_request, created = PurchaseRequest.objects.get_or_create(
                pr_no=pr_no,
                defaults={
                    "requested_by": request.user,
                    "entity_name": entity_name,
                    "fund_cluster": fund_cluster,
                    "office_section": office_section,
                    "responsibility_center_code": responsibility_center_code,
                    "purpose": purpose
                }
            )

            
            messages.success(request, "PR Headings has been added successfully")
            return redirect('purchase_request_form')
        elif 'purchase_request_id' in request.POST:
            purchase_request_id = request.POST.get('purchase_request_id')
            stock_property_no = request.POST.get('stock_property_no')
            unit = request.POST.get('unit')
            item_description = request.POST.get('item_description')
            quantity = int(request.POST.get('quantity', 0))
            unit_cost = Decimal(request.POST.get('unit_cost', 0))
            
            # Validate kung valid nga Purchase Request ID
            purchase_request = get_object_or_404(PurchaseRequest, id=purchase_request_id)
            
            # Create new PurchaseRequestItem
            PurchaseRequestItems.objects.create(
                purchase_request=purchase_request,
                stock_property_no=stock_property_no,
                unit=unit,
                item_description=item_description,
                quantity=quantity,
                unit_cost=unit_cost
            )
            
            messages.success(request, "Item added Successfully!")
            return redirect('purchase_request_form')
        
        elif "submit_pr" in request.POST:  # Purchase Request Submission
            print("POST data received:", request.POST)
            purchase_request_id = request.POST.get("latest_purchase_request_id")
            purchase_request = get_object_or_404(PurchaseRequest, id=purchase_request_id)

            purchase_request.pr_status = "Submitted"
            purchase_request.submitted_status = "Pending"
            purchase_request.save()

            print("Purchase Request Submitted Successfully!")
            messages.success(request, "Purchase Request Submitted Successfully!")
            return redirect("purchase_request_form")
        
    latest_purchase_request = PurchaseRequest.objects.filter(requested_by=request.user).last()
    purchase_items = latest_purchase_request.items.all() if latest_purchase_request else []
      
    
    return render(request, 'end_user_app/purchase_request_form.html', {
        'latest_purchase_request': latest_purchase_request,
        'purchase_items': purchase_items,
    })
