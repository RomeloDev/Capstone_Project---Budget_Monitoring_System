from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import redirect, get_object_or_404
from apps.admin_panel.models import BudgetAllocation
from .models import PurchaseRequest, PurchaseRequestItems, Budget_Realignment
from decimal import Decimal
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from decimal import Decimal
from django.db.models import Sum
from django.contrib.humanize.templatetags.humanize import intcomma

# Create your views here.
@login_required
def user_dashboard(request):
    try:
        # Get the budget allocation of the logged-in user
        budget = BudgetAllocation.objects.filter(assigned_user=request.user)
        user_total_allocated = budget.aggregate(Sum('total_allocated'))['total_allocated__sum'] or 0
        user_remaining_budget = budget.aggregate(Sum('remaining_budget'))['remaining_budget__sum'] or 0
        purchase_requests = PurchaseRequest.objects.filter(requested_by=request.user, pr_status="Submitted")
        approved_requests_count = PurchaseRequest.objects.filter(requested_by=request.user, submitted_status="Approved").count()
    except BudgetAllocation.DoesNotExist or PurchaseRequest.DoesNotExist:
        budget = None
        user_total_allocated = None
        user_remaining_budget = None
        purchase_request = None
        approved_requests_count = 0
    
    return render(request, 'end_user_app/dashboard.html', {
        'budget': budget, 
        'user_total_allocated': user_total_allocated,
        'user_remaining_budget': user_remaining_budget,
        'purchase_requests': purchase_requests,
        'approved_requests_count': approved_requests_count,
        })

@login_required
def view_budget(request):
    try:
        # Get the budget allocation of the logged-in user
        budget = BudgetAllocation.objects.filter(assigned_user=request.user)
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
    try:
        papps = BudgetAllocation.objects.filter(assigned_user=request.user).values_list('papp', flat=True)
    except BudgetAllocation.DoesNotExist:
        papps = None
    
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
        try:
            remaining_budget = BudgetAllocation.objects.filter(assigned_user=request.user, papp=request.POST.get('papp')).values_list('remaining_budget', flat=True)
        except BudgetAllocation.DoesNotExist:
            remaining_budget = None
            
        if remaining_budget is None:
            messages.error(request, "No Remaining Budget Found.")
            return redirect('purchase_request_form')
        
        if purchase_request.total_amount > remaining_budget[0]:
            messages.error(request, "Insufficient Remaining Budget.")
            return redirect('purchase_request_form')
        
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
        purchase_request.papp = request.POST.get('papp')
        purchase_request.save()
        
        # Update Remaining Budget
        try:
            budget = BudgetAllocation.objects.get(assigned_user=request.user, papp=purchase_request.papp)
            print("Remaining Budget Before: ", budget.remaining_budget) # Debugging line
            budget.remaining_budget -= purchase_request.total_amount
            budget.spent += purchase_request.total_amount
            print("Remaining Budget After: ", budget.remaining_budget) # Debugging line
            budget.save()
        except BudgetAllocation.DoesNotExist:
            messages.error(request, "Budget allocation not found.")
            return redirect('purchase_request_form')
        
        print("Purchase Request Submitted Sucessfully")
        messages.success(request, f"Purchase Request Submitted Sucessfully.")
        return redirect('purchase_request_form')
    
    context = {
        'purchase_request': purchase_request,
        'purchase_items': purchase_request.items.all(),
        'papps': papps,
    }
    
    return render(request, "end_user_app/purchase_request_form.html", context)

def papp_list(request, papp):
    try:
        papp = BudgetAllocation.objects.filter(assigned_user=request.user).values_list('papp', flat=True)
    except BudgetAllocation.DoesNotExist:
        papp = None
    return papp

@login_required
def re_alignment(request):
    target_papp = papp_list(request, papp="target_papp")
    source_papp = papp_list(request, papp="source_papp")
    
    
    
    if request.method == 'POST':
        # Get the form data from the request
        get_target_papp = request.POST.get('target_papp')
        get_source_papp = request.POST.get('source_papp')
        amount = request.POST.get('amount')
        reason = request.POST.get('reason')
        
        if not get_target_papp or not get_source_papp:
            messages.error(request, "Target PAPP and Source PAPP is required")
            return redirect('re_alignment')
        
        if get_target_papp == get_source_papp:
            messages.error(request, "Target PAPP and Source PAPP should not equal.")
            return redirect('re_alignment')
        
        # Check if the user has sufficient budget in the source PAPP
        try:
            source_budget = BudgetAllocation.objects.get(assigned_user=request.user, papp=get_source_papp)
            if source_budget.remaining_budget < Decimal(amount):
                messages.error(request, "Insufficient budget in the source PAPP.")
                return redirect('re_alignment')
        except BudgetAllocation.DoesNotExist:
            messages.error(request, "Source PAPP not found.")
            return redirect('re_alignment')
        
        re_alignment = Budget_Realignment.objects.create(
                    requested_by=request.user,
                    target_papp=get_target_papp,
                    source_papp=get_source_papp,
                    amount=Decimal(amount),
                    reason=reason
                )
        
        messages.success(request, "Budget for Realignment has been requested successfully")
        return redirect('re_alignment')
            
    return render(request, "end_user_app/re_alignment.html", {"target_papp": target_papp, "source_papp": source_papp})
    
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
        unit_cost=Decimal(request.POST.get('unit_cost', 0)),
    )
    
    return render(request, "end_user_app/partials/item_with_total_row.html", {"item": item, "purchase_request": purchase_request})
    
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
    purchase_request = remove_item.purchase_request  # ✅ This was missing

    # Delete the item
    remove_item.delete()

    # Update total amount
    total = sum(item.total_cost for item in purchase_request.items.all())
    purchase_request.total_amount = total
    purchase_request.save()

    # Render updated total row with OOB swap
    html = render_to_string("end_user_app/partials/deleted_row_and_total.html", {
        "item_id": item_id,
        "purchase_request": purchase_request
    })

    return HttpResponse(html)

    # return HttpResponse(status=200)  # Empty response with 200 OK
    #return JsonResponse({"success": True})
    
@login_required
def department_pre(request):
    return render(request, "end_user_app/department_pre.html")
    