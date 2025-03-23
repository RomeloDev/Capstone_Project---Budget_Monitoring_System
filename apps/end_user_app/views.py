from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import redirect, get_object_or_404
from apps.admin_panel.models import BudgetAllocation
from .models import PurchaseRequest, PurchaseRequestItems
from decimal import Decimal
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse

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
    try:
        purchase_requests = PurchaseRequest.objects.filter(requested_by=request.user, pr_status="Submitted")
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
    # Get or create draft purchase request
    purchase_request, created = PurchaseRequest.objects.get_or_create(
        requested_by=request.user,
        pr_status='draft',
        defaults={
            'entity_name': 'Draft Entity',
            'pr_no': 'TEMP',
            'pr_status': 'draft'
        }
    )
    
    if request.method == 'POST' and 'submit_pr' in request.POST:
        # Handle final form submission
        # Update purchase request details
        # Generate proper PR number here
        purchase_request.pr_status = 'Submitted'
        purchase_request.submitted_status = 'Pending'
        purchase_request.entity_name = request.POST.get('entity_name')
        purchase_request.fund_cluster = request.POST.get('fund_cluster')
        purchase_request.office_section = request.POST.get('office_section')
        purchase_request.pr_no = request.POST.get('pr_no')
        purchase_request.responsibility_center_code = request.POST.get('responsibility_code')
        purchase_request.purpose = request.POST.get('purpose')
        purchase_request.save()
        
        print("Purchase Request Submitted Sucessfully")
        return redirect('purchase_request_form')
    
    context = {
        'purchase_request': purchase_request,
        'purchase_items': purchase_request.items.all()
    }
    
    return render(request, "end_user_app/purchase_request_form.html", context)
    
@require_http_methods(["POST"])
@login_required
def add_purchase_request_items(request):
    # Get or create draft purchase request
    purchase_request, created = PurchaseRequest.objects.get_or_create(
        requested_by=request.user,
        pr_status='draft',
        defaults={
            'entity_name': 'Draft Entity',
            'pr_no': 'TEMP',
            'pr_status': 'draft'
        }
    )
    
    print(request.POST)  # Debugging: Check what data is being sent
    
    # Create item
    item = PurchaseRequestItems.objects.create(
        purchase_request=purchase_request,
        stock_property_no=request.POST.get('stock_no'),
        unit=request.POST.get('unit'),
        item_description=request.POST.get('item_desc'),
        quantity=int(request.POST.get('quantity', 0)),
        unit_cost=float(request.POST.get('unit_cost', 0)),
    )
    
    return render(request, "end_user_app/partials/item_row.html", {"item": item})
    
    # return JsonResponse({
    #     'success': True,
    #     'item': {
    #         'stock_property_no': item.stock_property_no,
    #         'unit': item.unit,
    #         'item_description': item.item_description,
    #         'quantity': item.quantity,
    #         'unit_cost': float(item.unit_cost),
    #         'total_cost': float(item.total_cost),
    #     }
    # })
    
    
@require_http_methods(["DELETE"])
def remove_purchase_item(request, item_id):
    remove_item = get_object_or_404(PurchaseRequestItems, id=item_id)
    remove_item.delete()
    return JsonResponse({"success": True})
    
