from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from apps.end_user_app.models import PurchaseRequest, DepartmentPRE
from apps.admin_panel.models import BudgetAllocation
from django.contrib import messages
from django.contrib.humanize.templatetags.humanize import intcomma
from decimal import Decimal

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
def department_pre_list(request):
    pres = DepartmentPRE.objects.filter(status='Pending').select_related('submitted_by').order_by('-created_at')
    return render(request, 'approving_officer_app/department_pre.html', {
        'pres': pres,
    })


@login_required
def preview_pre(request, pk: int):
    pre = get_object_or_404(DepartmentPRE.objects.select_related('submitted_by'), pk=pk)

    def to_decimal(value):
        try:
            return Decimal(str(value)) if value not in (None, "") else Decimal('0')
        except Exception:
            return Decimal('0')

    payload = pre.data or {}

    # Minimal sections: reuse same structure as end_user preview for consistency
    from apps.end_user_app.views import preview_pre as _eu_preview
    # Import to reuse the sections_spec definition, but since it's inside function, duplicate minimal spec for AO
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
        total_q1 = sum((it['q1'] for it in items if not it.get('is_group')), Decimal('0'))
        total_q2 = sum((it['q2'] for it in items if not it.get('is_group')), Decimal('0'))
        total_q3 = sum((it['q3'] for it in items if not it.get('is_group')), Decimal('0'))
        total_q4 = sum((it['q4'] for it in items if not it.get('is_group')), Decimal('0'))
        total_overall = sum((it['total'] for it in items if not it.get('is_group')), Decimal('0'))
        sections.append({'title': spec['title'], 'color_class': spec['color_class'], 'items': items, 'total_q1': total_q1, 'total_q2': total_q2, 'total_q3': total_q3, 'total_q4': total_q4, 'total_overall': total_overall})

    grand_total_q1 = sum((sec['total_q1'] for sec in sections), Decimal('0'))
    grand_total_q2 = sum((sec['total_q2'] for sec in sections), Decimal('0'))
    grand_total_q3 = sum((sec['total_q3'] for sec in sections), Decimal('0'))
    grand_total_q4 = sum((sec['total_q4'] for sec in sections), Decimal('0'))
    grand_total_overall = sum((sec['total_overall'] for sec in sections), Decimal('0'))

    return render(request, 'approving_officer_app/preview_pre.html', {
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
def handle_pre_action(request, pk: int):
    pre = get_object_or_404(DepartmentPRE, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            pre.status = 'Approved'
            pre.approved_by_approving_officer = True
        elif action == 'reject':
            pre.status = 'Rejected'
            pre.approved_by_approving_officer = False
        pre.save()
    return redirect('ao_department_pre_list')

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