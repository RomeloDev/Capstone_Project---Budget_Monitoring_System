from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import redirect, get_object_or_404
from apps.admin_panel.models import BudgetAllocation
from .models import PurchaseRequest, PurchaseRequestItems, Budget_Realignment, DepartmentPRE
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
        budget = BudgetAllocation.objects.filter(department=request.user.department)
        total_budget = sum(a.total_allocated for a in budget)
        total_spent = sum(a.spent for a in budget)
        remaining_balance = total_budget - total_spent
        purchase_requests = PurchaseRequest.objects.filter(requested_by=request.user, pr_status="Submitted")
        approved_requests_count = PurchaseRequest.objects.filter(requested_by=request.user, submitted_status="Approved").count()
    except BudgetAllocation.DoesNotExist or PurchaseRequest.DoesNotExist:
        budget = None
        total_budget = None
        remaining_balance = None
        purchase_requests = None
        approved_requests_count = 0
        
    spent = total_budget - remaining_balance
    if total_budget > 0:
        usage_percentage = (spent / total_budget) * 100
    else:
        usage_percentage = 0

    return render(request, 'end_user_app/dashboard.html', {
        "total_budget": total_budget,
        "remaining_balance": remaining_balance,
        'purchase_requests': purchase_requests,
        'approved_requests_count': approved_requests_count,
        "spent": spent,
        "usage_percentage": usage_percentage,
        })

@login_required
def view_budget(request):
    try:
        # Fetch all budget allocations for the logged-in user and include related approved_budget
        budget = BudgetAllocation.objects.select_related('approved_budget').filter(department=request.user.department)

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
def department_pre_form(request):
    context = {
        'personnel_services': [
            {'label': 'Basic Salary', 'name': 'basic_salary'},
            {'label': 'Honoraria', 'name': 'honoraria'},
            {'label': 'Overtime Pay', 'name': 'overtime_pay'},
        ],
        'MOOE_traveling_expenses': [
            {'label': 'Traveling Expenses - Local', 'name': 'travel_local'},
            {'label': 'Traveling Expenses - Foreign', 'name': 'travel_foreign'},
        ],
        'MOOE_training_and_scholarship_expenses': [
            {'label': 'Training Expenses', 'name': 'training_expenses'},
        ],
        'MOOE_supplies_and_materials_expenses': [
            {'label': 'Office Supplies Expenses', 'name': 'office_supplies_expenses'},
            {'label': 'Accountable Form Expenses', 'name': 'accountable_form_expenses'},
            {'label': 'Agricultural and Marine Supplies Expenses', 'name': 'agri_marine_supplies_expenses'},
            {'label': 'Drugs and Medicines', 'name': 'drugs_medicines'},
            {'label': 'Medical, Dental & Laboratory Supplies Expenses', 'name': 'med_dental_lab_supplies_expenses'},
            {'label': 'Food Supplies Expenses', 'name': 'food_supplies_expenses'},
            {'label': 'Fuel, Oil and Lubricants Expenses', 'name': 'fuel_oil_lubricants_expenses'},
            {'label': 'Textbooks and Instructional Materials Expenses', 'name': 'textbooks_instructional_materials_expenses'},
            {'label': 'Construction Materials Expenses', 'name': 'construction_material_expenses'},
            {'label': 'Other Supplies & Materials Expenses', 'name': 'other_supplies_materials_expenses'},
        ],
        'MOOE_semi_expendable_machinery_equipment_expenses': [
            {'label': 'Machinery', 'name': 'semee_machinery'},
            {'label': 'Office Equipment', 'name': 'semee_office_equipment'},
            {'label': 'Information and Communications Technology Equipment', 'name': 'semee_information_communication'},
            {'label': 'Communications Equipment', 'name': 'semee_communications_equipment'},
            {'label': 'Disaster Response and Rescue Equipment', 'name': 'semee_drr_equipment'},
            {'label': 'Medical Equipment', 'name': 'semee_medical_equipment'},
            {'label': 'Printing Equipment', 'name': 'semee_printing_equipment'},
            {'label': 'Sports Equipment', 'name': 'semee_sports_equipment'},
            {'label': 'Technical and Scientific Equipment', 'name': 'semee_technical_scientific_equipment'},
            {'label': 'ICT Equipment', 'name': 'semee_ict_equipment'},
            {'label': 'Other Machinery and Equipment', 'name': 'semee_other_machinery_equipment'},
        ],
        'MOOE_semi_expendable_furnitures_fixtures_books_expenses': [
            {'label': 'Furniture and Fixtures', 'name': 'furniture_fixtures'},
            {'label': 'Books', 'name': 'books'},
        ],
        'MOOE_utility_expenses': [
            {'label': 'Water Expenses', 'name': 'water_expenses'},
            {'label': 'Electricity Expenses', 'name': 'electricity_expenses'},
        ],
        'MOOE_communication_expenses': [
            {'label': 'Postage and Courier Services', 'name': 'postage_courier_services'},
            {'label': 'Telephone Expenses', 'name': 'telephone_expenses'},
            {'label': 'Telephone Expenses (Landline)', 'name': 'telephone_expenses_landline'},
            {'label': 'Internet Subscription Expenses', 'name': 'internet_subscription_expenses'},
            {'label': 'Cable, Satellite, Telegraph & Radio Expenses', 'name': 'cable_satellite_telegraph_radio_expenses'},
        ],
        'MOOE_awards_rewards_prizes': [
            {'label': 'Awards/Rewards Expenses', 'name': 'awards_rewards_expenses'},
            {'label': 'Prizes', 'name': 'prizes'},
        ],
        'MOOE_survey_research_exploration_development': [
            {'label': 'Survey Expenses', 'name': 'survey_expenses'},
            {'label': 'Survey, Research, Exploration, and Development expenses', 'name': 'survey_research_exploration_development_expenses'},
        ],
        'MOOE_professional_services': [
            {'label': 'Legal Services', 'name': 'legal_services'},
            {'label': 'Auditing Services', 'name': 'auditing_services'},
            {'label': 'Consultancy Services', 'name': 'consultancy_services'},
            {'label': 'Other Professional Services', 'name': 'other_professional_servies'},
        ],
        'MOOE_general_services': [
            {'label': 'Security Services', 'name': 'security_services'},
            {'label': 'Janitorial Services', 'name': 'janitorial_services'},
            {'label': 'Other General Services', 'name': 'other_general_services'},
            {'label': 'Other General Services', 'name': 'other_general_services_2'},
            {'label': 'Environment/Sanitary Services', 'name': 'environment/sanitary_services'},
        ],
        'repair_land_improvements': [
            {'label': 'Repair & Maintenance - Land Improvements', 'name': 'repair_maintenance_land_improvements'},
        ],
        'repair_buildings_structures': [
            {'label': 'Buildings', 'name': 'buildings'},
            {'label': 'School Buildings', 'name': 'school_buildings'},
            {'label': 'Hostels and Dormitories', 'name': 'hostel_dormitories'},
            {'label': 'Other Structures', 'name': 'other_structures'},
        ],
        'repair_machinery_equipment': [
            {'label': 'Machinery', 'name': 'repair_maintenance_machinery'},
            {'label': 'Office Equipment', 'name': 'repair_maintenance_office_equipment'},
            {'label': 'ICT Equipment', 'name': 'repair_maintenance_ict_equipment'},
            {'label': 'Agricultural and Forestry Equipment', 'name': 'repair_maintenance_agri_forestry_equipment'},
            {'label': 'Marine and Fishery Equipment', 'name': 'repair_maintenance_marine_fishery_equipment'},
            {'label': 'Airport Equipment', 'name': 'repair_maintenance_airport_equipment'},
            {'label': 'Communication Equipment', 'name': 'repair_maintenance_communication_equipment'},
            {'label': 'Disaster, Response and Rescue Equipment', 'name': 'repair_maintenance_drre_equipment'},
            {'label': 'Medical Equipment', 'name': 'repair_maintenance_medical_equipment'},
            {'label': 'Printing Equipment', 'name': 'repair_maintenance_printing_equipment'},
            {'label': 'Sports Equipment', 'name': 'repair_maintenance_sports_equipment'},
            {'label': 'Technical and Scientific Equipment', 'name': 'repair_maintenance_technical_scientific_equipment'},
            {'label': 'Other Machinery and Equipment', 'name': 'repair_maintenance_other_machinery_equipment'},
        ],
        'repair_transportation_equipment': [
            {'label': 'Motor Vehicles', 'name': 'repair_maintenance_motor'},
            {'label': 'Other Transportation Equipment', 'name': 'repair_maintenance_other_transportation_equipment'},
        ],
        'repair_furniture_fixtures': [
            {'label': 'Repairs and Maintenance - Furniture & Fixtures', 'name': 'repair_maintenance_furniture_fixtures'},
        ],
        'repair_semi_expendable_me': [
            {'label': 'Repairs and Maintenance - Semi-Expendable Machinery and Equipment', 'name': 'repair_maintenance_semi_expendable_machinery_equipment'},
        ],
        'repair_other_property_plant_equipment': [
            {'label': 'Repairs and Maintenance - Other Property, Plant and Equipment', 'name': 'repair_maintenance_other_property_plant_equipment'},
        ],
        'taxes_insurance_fees': [
            {'label': 'Taxes, Duties and Licenses', 'name': 'taxes_duties_licenses'},
            {'label': 'Fidelity Bond Premiums', 'name': 'fidelity_bond_premiums'},
            {'label': 'Insurance Expenses', 'name': 'insurance_expenses'},
        ],
        'labor_wages_list': [
            {'label': 'Labor and Wages', 'name': 'labor_wages'},
        ],
        'other_mooe': [
            {'label': 'Advertising Expenses', 'name': 'advertising_expenses'},
            {'label': 'Printing and Publication Expenses', 'name': 'printing_publication_expenses'},
            {'label': 'Representation Expenses', 'name': 'representation_expenses'},
            {'label': 'Transportation and Delivery Expenses', 'name': 'transportation_delivery_expenses'},
            {'label': 'Rent/Lease Expenses', 'name': 'rent/lease_expenses'},
            {'label': 'Membership Dues and contributions to organizations', 'name': 'membership_dues_contribute_to_org'},
            {'label': 'Subscription Expenses', 'name': 'subscription_expenses'},
            {'label': 'Website Maintenance', 'name': 'website_maintenance'},
            {'label': 'Other Maintenance and Operating Expenses', 'name': 'other_maintenance_operating_expenses'},
        ],
        'cap_land': [
            {'label': 'Land', 'name': 'land'},
        ],
        'cap_land_improvements': [
            {'label': 'Land Improvements, Aquaculture Structure', 'name': 'land_improvements_aqua_structure'},
        ],
        'cap_infrastructure_assets': [
            {'label': 'Water Supply Systems', 'name': 'water_supply_systems'},
            {'label': 'Power Supply Systems', 'name': 'power_supply_systems'},
            {'label': 'Other Infrastructure Assets', 'name': 'other_infra_assets'},
        ],
        'cap_bos': [
            {'label': 'Building', 'name': 'bos_building'},
            {'label': 'School Buildings', 'name': 'bos_school_buildings'},
            {'label': 'Hostels and Dormitories', 'name': 'bos_hostels_dorm'},
            {'label': 'Other Structures', 'name': 'other_structures'},
        ],
        'cap_me': [
            {'label': 'Machinery', 'name': 'me_machinery'},
            {'label': 'Office Equipment', 'name': 'me_office_equipment'},
            {'label': 'Information and Communication Technology Equipment', 'name': 'me_ict_equipment'},
            {'label': 'Communication Equipment', 'name': 'me_communication_equipment'},
            {'label': 'Disaster Response and Rescue Equipment', 'name': 'me_drre'},
            {'label': 'Medical Equipment', 'name': 'me_medical_equipment'},
            {'label': 'Printing Equipment', 'name': 'me_printing_equipment'},
            {'label': 'Sports Equipment', 'name': 'me_sports_equipment'},
            {'label': 'Technical and Scientific Equipment', 'name': 'me_technical_scientific_equipment'},
            {'label': 'Other Machinery and Equipment', 'name': 'me_other_machinery_equipment'},
        ],
        'cap_te': [
            {'label': 'Motor Vehicles', 'name': 'te_motor'},
            {'label': 'Other Transportation Equipment', 'name': 'te_other_transpo_equipment'},
        ],
        'cap_ffb': [
            {'label': 'Furniture and Fixtures', 'name': 'ffb_furniture_fixtures'},
            {'label': 'Books', 'name': 'ffb_books'},
        ],
        'cap_cp': [
            {'label': 'Construction in Progress - Land Improvements', 'name': 'cp_land_improvements'},
            {'label': 'Construction in Progress - Infrastructure Assets', 'name': 'cp_infra_assets'},
            {'label': 'Construction in Progress - Buildings and Other Structures', 'name': 'cp_building_other_structures'},
            {'label': 'Construction in Progress - Leased Assets', 'name': 'cp_leased_assets'},
            {'label': 'Construction in Progress - Leased Assets Improvements', 'name': 'cp_leased_assets_improvements'},
        ],
        'cap_ia': [
            {'label': 'Computer Software', 'name': 'ia_computer_software'},
            {'label': 'Websites', 'name': 'ia_websites'},
            {'label': 'Other Tangible Assets', 'name': 'ia_other_tangible_assets'},
        ],
    }

    if request.method == 'POST':
        numeric_suffixes = ('_q1', '_q2', '_q3', '_q4', '_total')
        invalid_fields = []
        for key, value in request.POST.items():
            if key == 'csrfmiddlewaretoken':
                continue
            if key in ('prepared_by', 'certified_by', 'approved_by'):
                continue
            if any(key.endswith(suf) for suf in numeric_suffixes):
                if value.strip() == '':
                    continue
                try:
                    num = Decimal(value)
                    if num < 0:
                        invalid_fields.append(key)
                except Exception:
                    invalid_fields.append(key)
        if invalid_fields:
            messages.error(request, f"Please enter valid non-negative numbers for: {', '.join(invalid_fields[:5])}{'…' if len(invalid_fields) > 5 else ''}")
            return render(request, "end_user_app/department_pre_form.html", context)

        payload = {k: v for k, v in request.POST.items() if k not in ['csrfmiddlewaretoken', 'prepared_by', 'certified_by', 'approved_by']}

        pre = DepartmentPRE.objects.create(
            submitted_by=request.user,
            department=getattr(request.user, 'department', ''),
            data=payload,
            prepared_by_name=request.POST.get('prepared_by') or None,
            certified_by_name=request.POST.get('certified_by') or None,
            approved_by_name=request.POST.get('approved_by') or None,
        )

        messages.success(request, "PRE submitted successfully.")
        return render(request, "end_user_app/department_pre_form.html", {'pre_id': pre.id, 'success': True, **context}) 
        # return redirect('preview_pre', pk=pre.id)
    
    return render(request, "end_user_app/department_pre_form.html", context)

@login_required
def department_pre_page(request):
    
    user = request.user
    user_dept = user.department
    
    has_budget = BudgetAllocation.objects.filter(department=user_dept).exists()
    return render(request, "end_user_app/department_pre_page.html", {
        'has_budget': has_budget,
    })


@login_required
def preview_pre(request, pk: int):
    pre = get_object_or_404(DepartmentPRE.objects.select_related('submitted_by'), pk=pk)
    # Security: ensure user can only view their own PRE (unless you allow admins)
    if pre.submitted_by != request.user:
        messages.error(request, "You do not have permission to view this PRE.")
        return redirect('department_pre_page')

    # Pass the raw data and signatories to the template for read-only rendering
    context = {
        'pre': pre,
        'data': pre.data,
        'prepared_by': pre.prepared_by_name,
        'certified_by': pre.certified_by_name,
        'approved_by': pre.approved_by_name,
    }
    return render(request, "end_user_app/preview_pre.html", context)
    