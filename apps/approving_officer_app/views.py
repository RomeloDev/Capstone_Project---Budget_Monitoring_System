from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from apps.end_user_app.models import PurchaseRequest, DepartmentPRE, ActivityDesign, PurchaseRequestAllocation
from apps.admin_panel.models import BudgetAllocation
from django.contrib import messages
from django.contrib.humanize.templatetags.humanize import intcomma
from decimal import Decimal
from apps.users.models import User
from apps.admin_panel.utils import log_audit_trail
from apps.users.utils import role_required

# Create your views here.
@role_required('officer', login_url='/')
def dashboard(request):
    try:
        pending_request = PurchaseRequest.objects.filter(pr_status='submitted', submitted_status='pending').count()
        approved_request = PurchaseRequest.objects.filter(pr_status='submitted', submitted_status='approved').count()
        rejected_request = PurchaseRequest.objects.filter(pr_status='submitted', submitted_status='rejected').count()
    except PurchaseRequest.DoesNotExist:
        pending_request = 0
        approved_request = 0
        rejected_request = 0
    return render(request, 'approving_officer_app/dashboard.html',{
        'pending_request': pending_request,
        'approved_request': approved_request,
        'rejected_request': rejected_request,
    })

@role_required('officer', login_url='/')
def department_request(request):
    departments = User.objects.filter(is_staff=False, is_approving_officer=False).values_list('department', flat=True).distinct()
    
    try:
        purchase_requests = PurchaseRequest.objects.filter(pr_status='Submitted', submitted_status='Partially Approved', approved_by_admin=True, approved_by_approving_officer=False).select_related('requested_by', 'budget_allocation__approved_budget', 'source_pre')
    except PurchaseRequest.DoesNotExist:
        purchase_requests = None
    
    filter_department = request.GET.get('department')
    if filter_department:
        purchase_requests = PurchaseRequest.objects.filter(requested_by__department=filter_department, pr_status='Submitted', submitted_status='Partially Approved', approved_by_approving_officer=False, approved_by_admin=True).select_related('requested_by', 'budget_allocation__approved_budget', 'source_pre')
    # else:
    #     purchase_requests = PurchaseRequest.objects.filter(pr_status='submitted')
    
    print(purchase_requests)
    return render(request, 'approving_officer_app/department_request.html', {'purchase_requests': purchase_requests, 'departments': departments})


@role_required('officer', login_url='/')
def department_pre_list(request):
    pres = DepartmentPRE.objects.filter(status='Partially Approved', approved_by_approving_officer=False, approved_by_admin=True).select_related('submitted_by').order_by('-created_at')
    return render(request, 'approving_officer_app/department_pre.html', {
        'pres': pres,
    })


@role_required('officer', login_url='/')
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
        {
            'title': 'Personnel Services',
            'color_class': 'bg-yellow-100',
            'items': [
                {'label': 'Basic Salary', 'name': 'basic_salary'},
                {'label': 'Honoraria', 'name': 'honoraria'},
                {'label': 'Overtime Pay', 'name': 'overtime_pay'},
            ]
        },
        {
            'title': 'Maintenance and Other Operating Expenses',
            'color_class': 'bg-blue-100',
            'items': [
                {'label': 'Travelling Expenses', 'is_group': True},
                {'label': 'Travelling expenses-local', 'name': 'travel_local', 'indent': True},
                {'label': 'Travelling Expenses-foreign', 'name': 'travel_foreign', 'indent': True},
                {'label': 'Training and Scholarship expenses', 'is_group': True},
                {'label': 'Training Expenses', 'name': 'training_expenses', 'indent': True},
                {'label': 'Supplies and materials expenses', 'is_group': True},
                {'label': 'Office Supplies Expenses', 'name': 'office_supplies_expenses', 'indent': True},
                {'label': 'Accountable Form Expenses', 'name': 'accountable_form_expenses', 'indent': True},
                {'label': 'Agricultural and Marine Supplies Expenses', 'name': 'agri_marine_supplies_expenses', 'indent': True},
                {'label': 'Drugs and Medicines', 'name': 'drugs_medicines', 'indent': True},
                {'label': 'Medical, Dental & Laboratory Supplies Expenses', 'name': 'med_dental_lab_supplies_expenses', 'indent': True},
                {'label': 'Food Supplies Expenses', 'name': 'food_supplies_expenses', 'indent': True},
                {'label': 'Fuel, Oil and Lubricants Expenses', 'name': 'fuel_oil_lubricants_expenses', 'indent': True},
                {'label': 'Textbooks and Instructional Materials Expenses', 'name': 'textbooks_instructional_materials_expenses', 'indent': True},
                {'label': 'Construction Materials Expenses', 'name': 'construction_material_expenses', 'indent': True},
                {'label': 'Other Supplies & Materials Expenses', 'name': 'other_supplies_materials_expenses', 'indent': True},
                {'label': 'Semi-expendable Machinery Equipment', 'is_group': True},
                {'label': 'Machinery', 'name': 'semee_machinery', 'indent': True},
                {'label': 'Office Equipment', 'name': 'semee_office_equipment', 'indent': True},
                {'label': 'Information and Communications Technology Equipment', 'name': 'semee_information_communication', 'indent': True},
                {'label': 'Communications Equipment', 'name': 'semee_communications_equipment', 'indent': True},
                {'label': 'Disaster Response and Rescue Equipment', 'name': 'semee_drr_equipment', 'indent': True},
                {'label': 'Medical Equipment', 'name': 'semee_medical_equipment', 'indent': True},
                {'label': 'Printing Equipment', 'name': 'semee_printing_equipment', 'indent': True},
                {'label': 'Sports Equipment', 'name': 'semee_sports_equipment', 'indent': True},
                {'label': 'Technical and Scientific Equipment', 'name': 'semee_technical_scientific_equipment', 'indent': True},
                {'label': 'ICT Equipment', 'name': 'semee_ict_equipment', 'indent': True},
                {'label': 'Other Machinery and Equipment', 'name': 'semee_other_machinery_equipment', 'indent': True},
                {'label': 'Semi-expendable Furnitures and Fixtures', 'is_group': True},
                {'label': 'Furniture and Fixtures', 'name': 'furniture_fixtures', 'indent': True},
                {'label': 'Books', 'name': 'books', 'indent': True},
                {'label': 'Utility Expenses', 'is_group': True},
                {'label': 'Water Expenses', 'name': 'water_expenses', 'indent': True},
                {'label': 'Electricity Expenses', 'name': 'electricity_expenses', 'indent': True},
                {'label': 'Communication Expenses', 'is_group': True},
                {'label': 'Postage and Courier Services', 'name': 'postage_courier_services', 'indent': True},
                {'label': 'Telephone Expenses', 'name': 'telephone_expenses', 'indent': True},
                {'label': 'Telephone Expenses (Landline)', 'name': 'telephone_expenses_landline', 'indent': True},
                {'label': 'Internet Subscription Expenses', 'name': 'internet_subscription_expenses', 'indent': True},
                {'label': 'Cable, Satellite, Telegraph & Radio Expenses', 'name': 'cable_satellite_telegraph_radio_expenses', 'indent': True},
                {'label': 'Awards/Rewards and Prizes', 'is_group': True},
                {'label': 'Awards/Rewards Expenses', 'name': 'awards_rewards_expenses', 'indent': True},
                {'label': 'Prizes', 'name': 'prizes', 'indent': True},
                {'label': 'Survey, Research, Exploration, and Development Expenses', 'is_group': True},
                {'label': 'Survey Expenses', 'name': 'survey_expenses', 'indent': True},
                {'label': 'Survey, Research, Exploration, and Development expenses', 'name': 'survey_research_exploration_development_expenses', 'indent': True},
                {'label': 'Professional Services', 'is_group': True},
                {'label': 'Legal Services', 'name': 'legal_services', 'indent': True},
                {'label': 'Auditing Services', 'name': 'auditing_services', 'indent': True},
                {'label': 'Consultancy Services', 'name': 'consultancy_services', 'indent': True},
                {'label': 'Other Professional Services', 'name': 'other_professional_servies', 'indent': True},
                {'label': 'General Services', 'is_group': True},
                {'label': 'Security Services', 'name': 'security_services', 'indent': True},
                {'label': 'Janitorial Services', 'name': 'janitorial_services', 'indent': True},
                {'label': 'Other General Services', 'name': 'other_general_services', 'indent': True},
                {'label': 'Environment/Sanitary Services', 'name': 'environment/sanitary_services', 'indent': True},
                {'label': 'Repair and Maintenance', 'is_group': True},
                {'label': 'Repair & Maintenance - Land Improvements', 'name': 'repair_maintenance_land_improvements', 'indent': True},
                {'label': 'Repair & Maintenance - Buildings and Structures', 'is_group': True},
                {'label': 'Buildings', 'name': 'buildings', 'indent': True},
                {'label': 'School Buildings', 'name': 'school_buildings', 'indent': True},
                {'label': 'Hostels and Dormitories', 'name': 'hostel_dormitories', 'indent': True},
                {'label': 'Other Structures', 'name': 'other_structures', 'indent': True},
                {'label': 'Repairs and Maintenance - Machinery and Equipment', 'is_group': True},
                {'label': 'Machinery', 'name': 'repair_maintenance_machinery', 'indent': True},
                {'label': 'Office Equipment', 'name': 'repair_maintenance_office_equipment', 'indent': True},
                {'label': 'ICT Equipment', 'name': 'repair_maintenance_ict_equipment', 'indent': True},
                {'label': 'Agricultural and Forestry Equipment', 'name': 'repair_maintenance_agri_forestry_equipment', 'indent': True},
                {'label': 'Marine and Fishery Equipment', 'name': 'repair_maintenance_marine_fishery_equipment', 'indent': True},
                {'label': 'Airport Equipment', 'name': 'repair_maintenance_airport_equipment', 'indent': True},
                {'label': 'Communication Equipment', 'name': 'repair_maintenance_communication_equipment', 'indent': True},
                {'label': 'Disaster, Response and Rescue Equipment', 'name': 'repair_maintenance_drre_equipment', 'indent': True},
                {'label': 'Medical Equipment', 'name': 'repair_maintenance_medical_equipment', 'indent': True},
                {'label': 'Printing Equipment', 'name': 'repair_maintenance_printing_equipment', 'indent': True},
                {'label': 'Sports Equipment', 'name': 'repair_maintenance_sports_equipment', 'indent': True},
                {'label': 'Technical and Scientific Equipment', 'name': 'repair_maintenance_technical_scientific_equipment', 'indent': True},
                {'label': 'Other Machinery and Equipment', 'name': 'repair_maintenance_other_machinery_equipment', 'indent': True},
                {'label': 'Repairs and Maintenance - Transportation Equipment', 'is_group': True},
                {'label': 'Motor Vehicles', 'name': 'repair_maintenance_motor', 'indent': True},
                {'label': 'Other Transportation Equipment', 'name': 'repair_maintenance_other_transportation_equipment', 'indent': True},
                {'label': 'Repairs and Maintenance - Furniture & Fixtures', 'name': 'repair_maintenance_furniture_fixtures'},
                {'label': 'Repairs and Maintenance - Semi-Expendable Machinery and Equipment', 'name': 'repair_maintenance_semi_expendable_machinery_equipment'},
                {'label': 'Repairs and Maintenance - Other Property, Plant and Equipment', 'name': 'repair_maintenance_other_property_plant_equipment'},
                {'label': 'Taxes, Insurance Premiums and Other Fees', 'is_group': True},
                {'label': 'Taxes, Duties and Licenses', 'name': 'taxes_duties_licenses', 'indent': True},
                {'label': 'Fidelity Bond Premiums', 'name': 'fidelity_bond_premiums', 'indent': True},
                {'label': 'Insurance Expenses', 'name': 'insurance_expenses', 'indent': True},
                {'label': 'Labor and Wages', 'is_group': True},
                {'label': 'Labor and Wages', 'name': 'labor_wages', 'indent': True},
                {'label': 'Other Maintenance and Operating Expenses', 'is_group': True},
                {'label': 'Advertising Expenses', 'name': 'advertising_expenses', 'indent': True},
                {'label': 'Printing and Publication Expenses', 'name': 'printing_publication_expenses', 'indent': True},
                {'label': 'Representation Expenses', 'name': 'representation_expenses', 'indent': True},
                {'label': 'Transportation and Delivery Expenses', 'name': 'transportation_delivery_expenses', 'indent': True},
                {'label': 'Rent/Lease Expenses', 'name': 'rent/lease_expenses', 'indent': True},
                {'label': 'Membership Dues and contributions to organizations', 'name': 'membership_dues_contribute_to_org', 'indent': True},
                {'label': 'Subscription Expenses', 'name': 'subscription_expenses', 'indent': True},
                {'label': 'Website Maintenance', 'name': 'website_maintenance', 'indent': True},
                {'label': 'Other Maintenance and Operating Expenses', 'name': 'other_maintenance_operating_expenses', 'indent': True},
            ]
        },
        {
            'title': 'Capital Outlays',
            'color_class': 'bg-green-100',
            'items': [
                # Placeholder; extend as needed
                {'label': 'Land', 'is_group': True},
                {'label': 'Land', 'name': 'land', 'indent': True},
                {'label': 'Land Improvements', 'is_group': True},
                {'label': 'Land Improvements, Aquaculture Structure', 'name': 'land_improvements_aqua_structure', 'indent': True},
                {'label': 'Infrastructure Assets', 'is_group': True},
                {'label': 'Water Supply Systems', 'name': 'water_supply_systems', 'indent': True},
                {'label': 'Power Supply Systems', 'name': 'power_supply_systems', 'indent': True},
                {'label': 'Other Infrastructure Assets', 'name': 'other_infra_assets', 'indent': True},
                {'label': 'Building and Other Structures', 'is_group': True},
                {'label': 'Building', 'name': 'bos_building', 'indent': True},
                {'label': 'School Buildings', 'name': 'bos_school_buildings', 'indent': True},
                {'label': 'Hostels and Dormitories', 'name': 'bos_hostels_dorm', 'indent': True},
                {'label': 'Other Structures', 'name': 'other_structures', 'indent': True},
                {'label': 'Machinery and Equipment', 'is_group': True},
                {'label': 'Machinery', 'name': 'me_machinery', 'indent': True},
                {'label': 'Office Equipment', 'name': 'me_office_equipment', 'indent': True},
                {'label': 'Information and Communication Technology Equipment', 'name': 'me_ict_equipment', 'indent': True},
                {'label': 'Communication Equipment', 'name': 'me_communication_equipment', 'indent': True},
                {'label': 'Disaster Response and Rescue Equipment', 'name': 'me_drre', 'indent': True},
                {'label': 'Medical Equipment', 'name': 'me_medical_equipment', 'indent': True},
                {'label': 'Printing Equipment', 'name': 'me_printing_equipment', 'indent': True},
                {'label': 'Sports Equipment', 'name': 'me_sports_equipment', 'indent': True},
                {'label': 'Technical and Scientific Equipment', 'name': 'me_technical_scientific_equipment', 'indent': True},
                {'label': 'Other Machinery and Equipment', 'name': 'me_other_machinery_equipment', 'indent': True},
                {'label': 'Transportation Equipment', 'is_group': True},
                {'label': 'Motor Vehicles', 'name': 'te_motor', 'indent': True},
                {'label': 'Other Transportation Equipment', 'name': 'te_other_transpo_equipment', 'indent': True},
                {'label': 'Furniture, Fixtures and Books', 'is_group': True},
                {'label': 'Furniture and Fixtures', 'name': 'ffb_furniture_fixtures', 'indent': True},
                {'label': 'Books', 'name': 'ffb_books', 'indent': True},
                {'label': 'Construction in Progress', 'is_group': True},
                {'label': 'Construction in Progress - Land Improvements', 'name': 'cp_land_improvements', 'indent': True},
                {'label': 'Construction in Progress - Infrastructure Assets', 'name': 'cp_infra_assets', 'indent': True},
                {'label': 'Construction in Progress - Buildings and Other Structures', 'name': 'cp_building_other_structures', 'indent': True},
                {'label': 'Construction in Progress - Leased Assets', 'name': 'cp_leased_assets', 'indent': True},
                {'label': 'Construction in Progress - Leased Assets Improvements', 'name': 'cp_leased_assets_improvements', 'indent': True},
                {'label': 'Intangible Assets', 'is_group': True},
                {'label': 'Computer Software', 'name': 'ia_computer_software', 'indent': True},
                {'label': 'Websites', 'name': 'ia_websites', 'indent': True},
                {'label': 'Other Tangible Assets', 'name': 'ia_other_tangible_assets', 'indent': True},
                
            ]
        },
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
        'prepared_by': pre.submitted_by.fullname,
        'certified_by': pre.certified_by_name,
        'approved_by': pre.approved_by_name,
    })


@role_required('officer', login_url='/')
def handle_pre_action(request, pk: int):
    pre = get_object_or_404(DepartmentPRE, pk=pk)
    budget_allocation = get_object_or_404(BudgetAllocation, id=pre.budget_allocation_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            pre.status = 'Approved'
            pre.approved_by_approving_officer = True
            
            if pre.approved_by_admin and pre.approved_by_approving_officer:
                pre.create_line_item_budgets()
        elif action == 'reject':
            pre.status = 'Rejected'
            pre.approved_by_approving_officer = False
            budget_allocation.is_compiled = False
            budget_allocation.save(update_fields=['is_compiled'])
        pre.save()
        log_audit_trail(
            request=request,
            action=action.upper(),
            model_name='DepartmentPRE',
            record_id=pre.id,
            detail=f"Approving Officer {action} a PRE with ID {pre.id} from department {pre.department}."
        )
    return redirect('ao_department_pre_list')

@role_required('officer', login_url='/')
def settings(request):
    return render(request, 'approving_officer_app/settings.html')

@role_required('officer', login_url='/')
def approving_officer_logout(request):
    logout(request)
    return redirect('end_user_login') # redirect to the login page

@role_required('officer', login_url='/')
def handle_request_action(request, pk):
    req = get_object_or_404(PurchaseRequest, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Ensure there is an associated budget allocation
        allocation = req.budget_allocation
        if action == 'approve':
            # Ensure there is an associated budget allocation
            # allocation = req.budget_allocation
            if allocation is None:
                messages.error(request, 'No budget allocation linked to this request.')
                return redirect('cd_department_request')

            # Check remaining budget before approval
            remaining_budget = allocation.remaining_budget
            if remaining_budget is not None and remaining_budget < (req.total_amount or 0):
                messages.error(request, 'Insufficient remaining budget to approve this request.')
                return redirect('cd_department_request')

            # Apply spend
            allocation.spent = (allocation.spent or 0) + (req.total_amount or 0)
            allocation.save(update_fields=['spent', 'updated_at'])

            req.submitted_status = 'Approved'
            req.approved_by_approving_officer = True
            req.approved_by = request.user
            req.save(update_fields=['submitted_status', 'approved_by', 'updated_at', 'approved_by_approving_officer'])
            
            log_audit_trail(
                request=request,
                action='APPROVE',
                model_name='PurchaseRequest',
                record_id=req.id,
                detail=f'Purchase Request {req.pr_no} have been Approved by Approving Officer'
            )
            
            messages.success(request, f'Request PR-{req.pr_no} has been approved successfully.')
        elif action == 'reject':
            try:
                allocations = PurchaseRequestAllocation.objects.filter(purchase_request=req).select_related('pre_line_item')
                
                total_released = Decimal('0')
                released_details = []
                
                for pr_allocation in allocations:
                    line_item = pr_allocation.pre_line_item
                    allocated_amount = pr_allocation.allocated_amount
                    
                    line_item.consumed_amount -= allocated_amount
                    line_item.save()
                    
                    total_released += allocated_amount
                    released_details.append(f"{line_item.item_key} {line_item.quarter}: ₱{allocated_amount}")
                    
                    print(f"Released ₱{allocated_amount} back to {line_item.item_key} {line_item.quarter}")
                    
                # Delete allocations after reversal
                allocations.delete()
                
                # Update Purchase Request Status
                req.submitted_status = 'Rejected'
                req.save(update_fields=['submitted_status', 'updated_at'])
                
                # Log in Audit Trail
                log_audit_trail(
                    request=request,
                    action='REJECT',
                    model_name='PurchaseRequest',
                    record_id=req.id,
                    detail=f'Rejected PR {req.pr_no} and released ₱{total_released} budget. Details: {", ".join(released_details)}'
                )
                
                messages.error(request, f'Request PR-{req.pr_no} has been rejected.')
                messages.success(request, f'Released ₱{total_released:,.2f} back to budget.')
            except Exception as e:
                print(f"DEBUG ERROR: {e}")
                messages.error(request, f"Error processing rejection: {e}")
                return redirect('cd_department_request')

    return redirect('cd_department_request')  # Redirect to the department request page after handling the action

@role_required('officer', login_url='/')
def preview_purchase_request(request, pk:int):
    pr = get_object_or_404(PurchaseRequest.objects.select_related('requested_by', 'budget_allocation__approved_budget', 'source_pre'),
        pk=pk,
    )
    
    return render(request, 'approving_officer_app/preview_purchase_request.html', {
        'pr': pr,
    })
    
@role_required('officer', login_url='/')
def activity_design_page(request):
    STATUS = (
        ('Pending', 'Pending'),
        ('Partially Approved', 'Partially Approved'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )
    
    departments = User.objects.filter(is_staff=False, is_approving_officer=False).values_list('department', flat=True).distinct()
    
    try:
        activity_design = ActivityDesign.objects.all().select_related('requested_by', 'budget_allocation__approved_budget', 'source_pre')
    except ActivityDesign.DoesNotExist:
        activity_design = None
    
    filter_department = request.GET.get('department')
    if filter_department:
        activity_design = ActivityDesign.objects.all().select_related('requested_by', 'budget_allocation__approved_budget', 'source_pre')
        
    status_filter = request.GET.get('status')
    if status_filter:
        activity_design = activity_design.filter(status=status_filter)
        
    context = {
        'activity_design': activity_design,
        'departments': departments,
        'status_choices': STATUS
    }
    return render(request, 'approving_officer_app/activity_design_page.html', context)

@role_required('officer', login_url='/')
def ao_preview_activity_design(request, pk: int):
    activity = get_object_or_404(ActivityDesign.objects.prefetch_related('sessions', 'signatories').select_related('campus_approval', 'university_approval'), pk=pk)
    
    return render(request, 'approving_officer_app/preview_activity_design.html', {
        'activity': activity,
    })
    
@role_required('officer', login_url='/')
def handle_activity_design_action(request, pk: int):
    activity = get_object_or_404(ActivityDesign, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            activity.status = 'Approved'
            activity.approved_by_approving_officer = True
            messages.success(request, f'Activity Design with ID {activity.id} has been approved successfully.')
        elif action == 'reject':
            activity.status = 'Rejected'
            activity.approved_by_approving_officer = False
            messages.error(request, f'Activity Design with ID {activity.id} has been rejected.')
        activity.save()
        log_audit_trail(
            request=request,
            action=action.upper(),
            model_name='ActivityDesign',
            record_id=activity.id,
            detail=f"Approving Officer {action} an Activity Design with ID {activity.id} from department {activity.requested_by.department}."
        )
    return redirect('ao_activity_design_page')