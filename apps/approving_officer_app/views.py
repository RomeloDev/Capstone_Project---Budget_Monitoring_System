from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from apps.end_user_app.models import PurchaseRequest
from apps.admin_panel.models import BudgetAllocation
from django.contrib import messages

# Create your views here.
@login_required
def dashboard(request):
    try:
        pending_request = PurchaseRequest.objects.filter(pr_status='Submitted', submitted_status='Pending').count()
        approved_request = PurchaseRequest.objects.filter(pr_status='Submitted', submitted_status='Approved').count()
        rejected_request = PurchaseRequest.objects.filter(pr_status='Submitted', submitted_status='Rejected').count()
    except PurchaseRequest.DoesNotExist:
        pending_request = 0
        approved_request = 0
        rejected_request = 0
    return render(request, 'approving_officer_app/dashboard.html',{
        'pending_request': pending_request,
        'approved_request': approved_request,
        'rejected_request': rejected_request,
    })

@login_required
def department_request(request):
    request_type = request.GET.get('request_type')
    try:
        purchase_requests = PurchaseRequest.objects.filter(pr_status='Submitted')
    except PurchaseRequest.DoesNotExist:
        purchase_requests = None
    
    print(purchase_requests)
    return render(request, 'approving_officer_app/department_request.html', {'purchase_requests': purchase_requests})

@login_required
def settings(request):
    return render(request, 'approving_officer_app/settings.html')

@login_required
def approving_officer_logout(request):
    logout(request)
    return redirect('end_user_login') # redirect to the login page

@login_required
def handle_request_action(request, pk):
    req = get_object_or_404(PurchaseRequest, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            req.submitted_status = 'Approved'
            messages.success(request, f'Request PR-{req.pr_no} has been approved successfully.')
        elif action == 'reject':
            req.submitted_status = 'Rejected'
            messages.error(request, f'Request PR-{req.pr_no} has been rejected.')
        req.approved_by = request.user
        req.save()
        
    return redirect('cd_department_request')  # Redirect to the department request page after handling the action