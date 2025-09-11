from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import redirect, get_object_or_404
from apps.admin_panel.models import BudgetAllocation
from .models import PurchaseRequest, PurchaseRequestItems, Budget_Realignment, DepartmentPRE, ActivityDesign, Session, Signatory, CampusApproval, UniversityApproval, PRELineItemBudget
from decimal import Decimal
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from decimal import Decimal
from django.db.models import Sum
from django.contrib.humanize.templatetags.humanize import intcomma
from datetime import datetime
from apps.admin_panel.utils import log_audit_trail
from apps.users.utils import role_required

# Create your views here.
@role_required('end_user', login_url='/')
def user_dashboard(request):
    try:
        # Get the budget allocation of the logged-in user
        budget = BudgetAllocation.objects.filter(department=request.user.department)
        total_budget = sum(a.total_allocated for a in budget)
        total_spent = sum(a.spent for a in budget)
        remaining_balance = total_budget - total_spent
        purchase_requests = PurchaseRequest.objects.filter(requested_by=request.user, pr_status='submitted')
        approved_requests_count = PurchaseRequest.objects.filter(requested_by=request.user, submitted_status='approved').count()
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

@role_required('end_user', login_url='/')
def view_budget(request):
    try:
        # Fetch all budget allocations for the logged-in user and include related approved_budget
        budget = BudgetAllocation.objects.select_related('approved_budget').filter(department=request.user.department)

    except BudgetAllocation.DoesNotExist:
        budget = None  # If no budget is assigned to the user
    
    return render(request, 'end_user_app/view_budget.html', {'budget': budget})

@role_required('end_user', login_url='/')
def purchase_request(request):
    try:
        purchase_requests = PurchaseRequest.objects.filter(requested_by=request.user, pr_status="Submitted").select_related('source_pre')
    except PurchaseRequest.DoesNotExist:
        purchase_requests = None
    return render(request, 'end_user_app/purchase_request.html', {'purchase_requests': purchase_requests})

@role_required('end_user', login_url='/')
def settings(request):
    return render(request, 'end_user_app/settings.html')

@role_required('end_user', login_url='/')
def end_user_logout(request):
    log_audit_trail(
        request=request,
        action='LOGOUT',
        model_name='User',
        detail=f'User {request.user} logged out',
    )
    logout(request)
    return redirect('end_user_login') # redirect to the login page

@role_required('end_user', login_url='/')
def purchase_request_form(request):
    # Ensure a draft PR exists for the user to accumulate items prior to submission
    purchase_request_obj, _created = PurchaseRequest.objects.get_or_create(
        requested_by=request.user,
        pr_status='draft',
        defaults={
            'entity_name': 'Draft Entity',
            'pr_no': 'TEMP',
        }
    )

    # Budget Allocation options (limit to user's department)
    budget_allocations = BudgetAllocation.objects.select_related('approved_budget').filter(
        department=getattr(request.user, 'department', '')
    )

    # Build Source-of-Fund options from approved PRE entries with positive amounts
    def build_pre_source_options(user):
        options = []
        approved_pres = DepartmentPRE.objects.filter(
            submitted_by=user,
            approved_by_approving_officer=True,
            approved_by_admin=True,
        )

        # Friendly labels for known PRE item keys (fallback to humanized key)
        friendly_labels = {
            'travel_local': 'Traveling Expenses - Local',
            'travel_foreign': 'Traveling Expenses - Foreign',
            'training_expenses': 'Training Expenses',
            'office_supplies_expenses': 'Office Supplies Expenses',
            'accountable_form_expenses': 'Accountable Form Expenses',
            'agri_marine_supplies_expenses': 'Agricultural and Marine Supplies Expenses',
            'drugs_medicines': 'Drugs and Medicines',
            'med_dental_lab_supplies_expenses': 'Medical, Dental & Laboratory Supplies Expenses',
            'food_supplies_expenses': 'Food Supplies Expenses',
            'fuel_oil_lubricants_expenses': 'Fuel, Oil and Lubricants Expenses',
            'textbooks_instructional_materials_expenses': 'Textbooks and Instructional Materials Expenses',
            'construction_material_expenses': 'Construction Materials Expenses',
            'other_supplies_materials_expenses': 'Other Supplies & Materials Expenses',
            'semee_machinery': 'Semi-expendable - Machinery',
            'semee_office_equipment': 'Semi-expendable - Office Equipment',
            'semee_information_communication': 'Semi-expendable - ICT Equipment',
            'semee_communications_equipment': 'Semi-expendable - Communications Equipment',
            'semee_drr_equipment': 'Semi-expendable - Disaster Response and Rescue Equipment',
            'semee_medical_equipment': 'Semi-expendable - Medical Equipment',
            'semee_printing_equipment': 'Semi-expendable - Printing Equipment',
            'semee_sports_equipment': 'Semi-expendable - Sports Equipment',
            'semee_technical_scientific_equipment': 'Semi-expendable - Technical and Scientific Equipment',
            'semee_ict_equipment': 'Semi-expendable - ICT Equipment',
            'semee_other_machinery_equipment': 'Semi-expendable - Other Machinery and Equipment',
            'furniture_fixtures': 'Furniture and Fixtures',
            'books': 'Books',
            'water_expenses': 'Water Expenses',
            'electricity_expenses': 'Electricity Expenses',
            'postage_courier_services': 'Postage and Courier Services',
            'telephone_expenses': 'Telephone Expenses',
            'telephone_expenses_landline': 'Telephone Expenses (Landline)',
            'internet_subscription_expenses': 'Internet Subscription Expenses',
            'cable_satellite_telegraph_radio_expenses': 'Cable, Satellite, Telegraph & Radio Expenses',
            'awards_rewards_expenses': 'Awards/Rewards Expenses',
            'prizes': 'Prizes',
            'survey_expenses': 'Survey Expenses',
            'survey_research_exploration_development_expenses': 'Survey, Research, Exploration, and Development expenses',
            'legal_services': 'Legal Services',
            'auditing_services': 'Auditing Services',
            'consultancy_services': 'Consultancy Services',
            'other_professional_servies': 'Other Professional Services',
            'security_services': 'Security Services',
            'janitorial_services': 'Janitorial Services',
            'other_general_services': 'Other General Services',
            'environment/sanitary_services': 'Environment/Sanitary Services',
            'repair_maintenance_land_improvements': 'Repair & Maintenance - Land Improvements',
            'buildings': 'Buildings',
            'school_buildings': 'School Buildings',
            'hostel_dormitories': 'Hostels and Dormitories',
            'other_structures': 'Other Structures',
            'repair_maintenance_machinery': 'Repair & Maintenance - Machinery',
            'repair_maintenance_office_equipment': 'Repair & Maintenance - Office Equipment',
            'repair_maintenance_ict_equipment': 'Repair & Maintenance - ICT Equipment',
            'repair_maintenance_agri_forestry_equipment': 'Repair & Maintenance - Agricultural and Forestry Equipment',
            'repair_maintenance_marine_fishery_equipment': 'Repair & Maintenance - Marine and Fishery Equipment',
            'repair_maintenance_airport_equipment': 'Repair & Maintenance - Airport Equipment',
            'repair_maintenance_communication_equipment': 'Repair & Maintenance - Communication Equipment',
            'repair_maintenance_drre_equipment': 'Repair & Maintenance - Disaster, Response and Rescue Equipment',
            'repair_maintenance_medical_equipment': 'Repair & Maintenance - Medical Equipment',
            'repair_maintenance_printing_equipment': 'Repair & Maintenance - Printing Equipment',
            'repair_maintenance_sports_equipment': 'Repair & Maintenance - Sports Equipment',
            'repair_maintenance_technical_scientific_equipment': 'Repair & Maintenance - Technical and Scientific Equipment',
            'repair_maintenance_other_machinery_equipment': 'Repair & Maintenance - Other Machinery and Equipment',
            'repair_maintenance_motor': 'Repair & Maintenance - Motor Vehicles',
            'repair_maintenance_other_transportation_equipment': 'Repair & Maintenance - Other Transportation Equipment',
            'repair_maintenance_furniture_fixtures': 'Repair & Maintenance - Furniture & Fixtures',
            'repair_maintenance_semi_expendable_machinery_equipment': 'Repair & Maintenance - Semi-Expendable Machinery and Equipment',
            'repair_maintenance_other_property_plant_equipment': 'Repair & Maintenance - Other Property, Plant and Equipment',
            'taxes_duties_licenses': 'Taxes, Duties and Licenses',
            'fidelity_bond_premiums': 'Fidelity Bond Premiums',
            'insurance_expenses': 'Insurance Expenses',
            'labor_wages': 'Labor and Wages',
            'advertising_expenses': 'Advertising Expenses',
            'printing_publication_expenses': 'Printing and Publication Expenses',
            'representation_expenses': 'Representation Expenses',
            'transportation_delivery_expenses': 'Transportation and Delivery Expenses',
            'rent/lease_expenses': 'Rent/Lease Expenses',
            'membership_dues_contribute_to_org': 'Membership Dues and contributions to organizations',
            'subscription_expenses': 'Subscription Expenses',
            'website_maintenance': 'Website Maintenance',
            'other_maintenance_operating_expenses': 'Other Maintenance and Operating Expenses',
        }

        for pre in approved_pres:
            payload = pre.data or {}
            for key, value in payload.items():
                if not isinstance(value, (int, float, Decimal)):
                    try:
                        value = Decimal(str(value))
                    except Exception:
                        continue
                if value and value > 0 and (key.endswith('_q1') or key.endswith('_q2') or key.endswith('_q3') or key.endswith('_q4')):
                    base_key, quarter = key.rsplit('_', 1)
                    quarter = quarter.upper()
                    label_base = friendly_labels.get(base_key, base_key.replace('_', ' ').title())
                    display_amount = f"{intcomma(value)}"
                    display = f"{label_base} {quarter} - {display_amount}"
                    # Encode value for round-trip on submit
                    encoded = f"{pre.id}|{base_key}|{quarter}|{value}"
                    options.append({'value': encoded, 'label': display})
        return options

    source_of_fund_options = build_pre_source_options(request.user)

    if request.method == 'POST':
        # Parse and save header fields
        purchase_request_obj.entity_name = request.POST.get('entity_name') or purchase_request_obj.entity_name
        purchase_request_obj.fund_cluster = request.POST.get('fund_cluster') or purchase_request_obj.fund_cluster
        purchase_request_obj.office_section = request.POST.get('office_section') or purchase_request_obj.office_section
        pr_no_input = request.POST.get('pr_no')
        if pr_no_input and purchase_request_obj.pr_no == 'TEMP':
            purchase_request_obj.pr_no = pr_no_input
        purchase_request_obj.responsibility_center_code = request.POST.get('responsibility_code') or purchase_request_obj.responsibility_center_code
        purchase_request_obj.purpose = request.POST.get('purpose') or purchase_request_obj.purpose

        # Budget Allocation linkage
        ba_id = request.POST.get('budget_allocation')
        if ba_id:
            try:
                purchase_request_obj.budget_allocation = BudgetAllocation.objects.select_related('approved_budget').get(id=ba_id)
            except BudgetAllocation.DoesNotExist:
                print("No such budget allocation for this user.")
                purchase_request_obj.budget_allocation = None

        # Source of fund linkage (encoded as preId|itemKey|QUARTER|amount)
        sof_encoded = request.POST.get('source_of_fund')
        if sof_encoded:
            try:
                # pre_id_str, item_key, quarter, amount_str = sof_encoded.split('|', 3)
                # pre_obj = DepartmentPRE.objects.get(id=int(pre_id_str), submitted_by=request.user)
                # purchase_request_obj.source_pre = pre_obj
                # purchase_request_obj.source_item_key = item_key
                # purchase_request_obj.source_quarter = quarter
                # purchase_request_obj.source_amount = Decimal(amount_str)
                
                parts = sof_encoded.split('|', 2)
                if len(parts) >= 3:
                    pre_id_str, item_key, quarters_data = parts
                    pre_obj = DepartmentPRE.objects.get(id=int(pre_id_str), submitted_by=request.user)
                    
                    # Parse quarters data to get the first available quarter and amount
                    quarters = quarters_data.split('|')
                    if quarters:
                        first_quarter_data = quarters[0].split(':')
                        if len(first_quarter_data) == 2:
                            quarter, amount_str = first_quarter_data
                            
                            purchase_request_obj.source_pre = pre_obj
                            purchase_request_obj.source_item_key = item_key
                            purchase_request_obj.source_quarter = quarter
                            purchase_request_obj.source_amount = Decimal(amount_str)
            except Exception as e:
                print(f"Error parsing source of fund: {e}")
                pass

        # Mark as submitted
        purchase_request_obj.pr_status = 'Submitted'
        purchase_request_obj.submitted_status = 'Pending'
        purchase_request_obj.save()
        
        log_audit_trail(
            request=request,
            action='CREATE',
            model_name='PurchaseRequest',
            record_id=purchase_request_obj.id,
            detail=f'Created a new purchase request {purchase_request_obj.pr_no}',
        )

        from django.urls import reverse
        preview_url = reverse('end_user_preview_purchase_request', args=[purchase_request_obj.id])
        return JsonResponse({'success': True, 'redirect_url': preview_url})

    # GET request
    # Items to render in the table
    items = purchase_request_obj.items.all()

    return render(
        request,
        "end_user_app/purchase_request_form.html",
        {
            'purchase_request': purchase_request_obj,
            'purchase_items': items,
            'budget_allocations': budget_allocations,
            'source_of_fund_options': source_of_fund_options,
        }
    )

@role_required('end_user', login_url='/')
def preview_purchase_request(request, pk: int):
    pr = get_object_or_404(
        PurchaseRequest.objects.select_related('requested_by', 'budget_allocation__approved_budget', 'source_pre'),
        pk=pk,
        requested_by=request.user,
    )
    return render(request, 'end_user_app/preview_purchase_request.html', {'pr': pr})

@role_required('end_user', login_url='/')
def papp_list(request, papp):
    try:
        papp = BudgetAllocation.objects.filter(assigned_user=request.user).values_list('papp', flat=True)
    except BudgetAllocation.DoesNotExist:
        papp = None
    return papp

@role_required('end_user', login_url='/')
def re_alignment(request):
    """
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
            source_budget = BudgetAllocation.objects.get(department=request.user, papp=get_source_papp)
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
        """
            
    return render(request, "end_user_app/re_alignment.html")
    
@require_http_methods(["POST"])
@role_required('end_user', login_url='/')
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
    

@role_required('end_user', login_url='/')
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
    
@role_required('end_user', login_url='/')
def department_pre_form(request, pk:int):
    budget_allocation = BudgetAllocation.objects.filter(department=request.user.department, id=pk).first()
    context = {
        'budget': budget_allocation,
        
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

        # Link to the latest Budget Allocation for this department, if any
        # dept_alloc = BudgetAllocation.objects.filter(department=getattr(request.user, 'department', '')).order_by('-allocated_at').first()
        
        dept_alloc = BudgetAllocation.objects.filter(
            department=getattr(request.user, 'department', ''),
            id=pk
        ).first()

        if not dept_alloc:
            messages.error(request, "No budget allocation found for this department.")
            return render(request, "end_user_app/department_pre_form.html", context)

        print(dept_alloc)

        pre = DepartmentPRE.objects.create(
            submitted_by=request.user,
            department=getattr(request.user, 'department', ''),
            data=payload,
            prepared_by_name=request.user.username,
            certified_by_name= None,
            approved_by_name= None,
            budget_allocation=dept_alloc,
        )
        
        dept_alloc.is_compiled = True
        dept_alloc.save(update_fields=['is_compiled'])

        messages.success(request, "PRE submitted successfully.")
        return render(request, "end_user_app/department_pre_form.html", {'pre_id': pre.id, 'success': True, **context}) 
        # return redirect('preview_pre', pk=pre.id)
    
    return render(request, "end_user_app/department_pre_form.html", context)

@role_required('end_user', login_url='/')
def department_pre_page(request):
    user = request.user
    user_dept = user.department
    # has_budget = BudgetAllocation.objects.filter(department=request.user.department).exists()
    
    is_has_budget = BudgetAllocation.objects.filter(department=user_dept, is_compiled=False).exists()
    
    if is_has_budget:
        has_budget = True
    else:
        has_budget = False
        
    budget_allocations = BudgetAllocation.objects.filter(department=request.user.department, is_compiled=False).select_related('approved_budget').order_by('-allocated_at')

    # Load submitted PREs for this user/department
    pres = DepartmentPRE.objects.filter(submitted_by=user).order_by('-created_at')

    return render(request, "end_user_app/department_pre_page.html", {
        'has_budget': has_budget,
        'pres': pres,
        'budget_allocations': budget_allocations,
    })


@role_required('end_user', login_url='/')
def preview_pre(request, pk: int):
    pre = get_object_or_404(DepartmentPRE.objects.select_related('submitted_by'), pk=pk)
    # Security: ensure user can only view their own PRE (unless you allow admins)
    if pre.submitted_by != request.user:
        messages.error(request, "You do not have permission to view this PRE.")
        return redirect('department_pre_page')

    # Build grouped sections for Excel-like table
    def to_decimal(value):
        try:
            return Decimal(str(value)) if value not in (None, "") else Decimal('0')
        except Exception:
            return Decimal('0')

    payload = pre.data or {}

    # Define mapping of sections and items (subset reflecting provided screenshot)
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
                items.append({
                    'label': row['label'],
                    'indent': row.get('indent', False),
                    'q1': q1,
                    'q2': q2,
                    'q3': q3,
                    'q4': q4,
                    'total': total,
                })

        # Compute section totals excluding group rows
        total_q1 = sum((it['q1'] for it in items if not it.get('is_group')), Decimal('0'))
        total_q2 = sum((it['q2'] for it in items if not it.get('is_group')), Decimal('0'))
        total_q3 = sum((it['q3'] for it in items if not it.get('is_group')), Decimal('0'))
        total_q4 = sum((it['q4'] for it in items if not it.get('is_group')), Decimal('0'))
        total_overall = sum((it['total'] for it in items if not it.get('is_group')), Decimal('0'))

        sections.append({
            'title': spec['title'],
            'color_class': spec['color_class'],
            'items': items,
            'total_q1': total_q1,
            'total_q2': total_q2,
            'total_q3': total_q3,
            'total_q4': total_q4,
            'total_overall': total_overall,
        })

    # Compute grand totals across all sections
    grand_total_q1 = sum((sec['total_q1'] for sec in sections), Decimal('0'))
    grand_total_q2 = sum((sec['total_q2'] for sec in sections), Decimal('0'))
    grand_total_q3 = sum((sec['total_q3'] for sec in sections), Decimal('0'))
    grand_total_q4 = sum((sec['total_q4'] for sec in sections), Decimal('0'))
    grand_total_overall = sum((sec['total_overall'] for sec in sections), Decimal('0'))

    # Pass the grouped table, raw data and signatories
    context = {
        'pre': pre,
        'data': payload,
        'sections': sections,
        'grand_total_q1': grand_total_q1,
        'grand_total_q2': grand_total_q2,
        'grand_total_q3': grand_total_q3,
        'grand_total_q4': grand_total_q4,
        'grand_total_overall': grand_total_overall,
        'prepared_by': pre.prepared_by_name,
        'certified_by': pre.certified_by_name,
        'approved_by': pre.approved_by_name,
    }
    return render(request, "end_user_app/preview_pre.html", context)
    
# Activity Design Form Logic
@role_required('end_user', login_url='/')
def activity_design_form(request):
    budget_allocations = BudgetAllocation.objects.select_related('approved_budget').filter(department=getattr(request.user, 'department', ''))
    
    if request.method == 'POST':
        # Save the main acitivity design data
        
        # Initialize variable to avoid scope issues
        item_key = None
        quarter = None
        source_amount_decimal = None
        source_pre_instance = None
        
        ba_id = request.POST.get('budget_allocation')
        budget_allocation_instance = None
        if ba_id:
            try:
                budget_allocation_instance = BudgetAllocation.objects.select_related('approved_budget').get(id=ba_id)
            except BudgetAllocation.DoesNotExist:
                messages.error(request, "No such budget allocation for this user.")
                budget_allocation_instance = None
        
        # Extracting the source of fund from the encoded string
        sof_encoded = request.POST.get('source_of_fund')
        if sof_encoded:
            try:
                pre_id_str, item_key, quarter, amount_str = sof_encoded.split('|', 3)
                source_amount_decimal = Decimal(amount_str)
                if source_amount_decimal <= 0:
                    raise Exception
                source_pre_instance = DepartmentPRE.objects.get(id=int(pre_id_str))
            except (Exception, ValueError, DepartmentPRE.DoesNotExist):
                source_pre_instance = None
                messages.error(request, f"Invalid source of fund format or {Exception.message}.")
                return redirect('activity_design_form')
                
        
        activity = ActivityDesign.objects.create(
            title_of_activity=request.POST.get('title_of_activity'),
            schedule_date=request.POST.get('schedule_date'),
            venue=request.POST.get('venue'),
            rationale=request.POST.get('rationale'),
            objectives=request.POST.get('objectives'),
            methodology=request.POST.get('methodology'),
            participants=request.POST.get('participants'),
            resource_persons=request.POST.get('resource_persons'),
            materials_needed=request.POST.get('materials_needed'),
            budget_allocation=budget_allocation_instance,
            evaluation_plan=request.POST.get('evaluation_outcomes'),
            source_pre=source_pre_instance if sof_encoded else None,
            source_item_key=item_key if sof_encoded else None,
            source_quarter=quarter if sof_encoded else None,
            source_amount=source_amount_decimal if sof_encoded else None,
            requested_by=request.user,
        )
        
        
        # Save sessions (many-to-one)
        session_contents = request.POST.getlist('sessions[]')
        for order, content in enumerate(session_contents, start=1):
            if content.strip():
                Session.objects.create(
                    activity=activity,
                    content=content,
                    order=order
                )
             
        # Temporary commented this code for form enhancing   
        # Save signatories (many-to-many)
        # names = request.POST.getlist('signatory_name[]')
        # positions = request.POST.getlist('signatory_position[]')
        # dates = request.POST.getlist('signatory_date[]')
        
        # for name, position, date_str in zip(names, positions, dates):
        #     if name.strip():
        #         date_obj = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else None
        #         Signatory.objects.create(
        #             activity=activity,
        #             name=name,
        #             position=position,
        #             date=date_obj
        #         )
                
        # # Save campus approval (one-to-one)
        # campus_approval = CampusApproval.objects.create(
        #     activity=activity,
        #     name=request.POST.get('campus_name'),
        #     position=request.POST.get('campus_position'),
        #     date=datetime.strptime(request.POST.get('campus_date'), "%Y-%m-%d").date() if request.POST.get('campus_date') else None,
        #     remarks=request.POST.get('campus_remarks')
        # )
        
        # # Save University Approval (one-to-one)
        # university_approval = UniversityApproval.objects.create(
        #     activity=activity,
        #     name=request.POST.get('univ_name'),
        #     position=request.POST.get('univ_position'),
        #     date=datetime.strptime(request.POST.get('univ_date'), "%Y-%m-%d").date() if request.POST.get('univ_date') else None,
        #     remarks=request.POST.get('univ_remarks')
        # )
        
        # Show message success 
        messages.success(request, "Activity Design submitted successfully.")
        
        return render(request, "end_user_app/activity_design_form.html", {'ad_id': activity.id, 'success': True})  # Redirect to the same form or a success page
        
    return render(request, "end_user_app/activity_design_form.html", {
        'budget_allocations': budget_allocations,
    })

@role_required('end_user', login_url='/')
def preview_activity_design(request, pk):
    activity = get_object_or_404(ActivityDesign.objects.prefetch_related('sessions', 'signatories').select_related('campus_approval', 'university_approval'), pk=pk)
    context = {
        "activity": activity,
    }
    return render(request, "end_user_app/preview_activity_design.html", context)

def build_pre_source_options(pres_queryset):
        options = []
        # approved_pres = DepartmentPRE.objects.filter(
        #     submitted_by=request,
        #     approved_by_approving_officer=True,
        #     approved_by_admin=True,
        # )

        # Friendly labels for known PRE item keys (fallback to humanized key)
        friendly_labels = {
            'travel_local': 'Traveling Expenses - Local',
            'travel_foreign': 'Traveling Expenses - Foreign',
            'training_expenses': 'Training Expenses',
            'office_supplies_expenses': 'Office Supplies Expenses',
            'accountable_form_expenses': 'Accountable Form Expenses',
            'agri_marine_supplies_expenses': 'Agricultural and Marine Supplies Expenses',
            'drugs_medicines': 'Drugs and Medicines',
            'med_dental_lab_supplies_expenses': 'Medical, Dental & Laboratory Supplies Expenses',
            'food_supplies_expenses': 'Food Supplies Expenses',
            'fuel_oil_lubricants_expenses': 'Fuel, Oil and Lubricants Expenses',
            'textbooks_instructional_materials_expenses': 'Textbooks and Instructional Materials Expenses',
            'construction_material_expenses': 'Construction Materials Expenses',
            'other_supplies_materials_expenses': 'Other Supplies & Materials Expenses',
            'semee_machinery': 'Semi-expendable - Machinery',
            'semee_office_equipment': 'Semi-expendable - Office Equipment',
            'semee_information_communication': 'Semi-expendable - ICT Equipment',
            'semee_communications_equipment': 'Semi-expendable - Communications Equipment',
            'semee_drr_equipment': 'Semi-expendable - Disaster Response and Rescue Equipment',
            'semee_medical_equipment': 'Semi-expendable - Medical Equipment',
            'semee_printing_equipment': 'Semi-expendable - Printing Equipment',
            'semee_sports_equipment': 'Semi-expendable - Sports Equipment',
            'semee_technical_scientific_equipment': 'Semi-expendable - Technical and Scientific Equipment',
            'semee_ict_equipment': 'Semi-expendable - ICT Equipment',
            'semee_other_machinery_equipment': 'Semi-expendable - Other Machinery and Equipment',
            'furniture_fixtures': 'Furniture and Fixtures',
            'books': 'Books',
            'water_expenses': 'Water Expenses',
            'electricity_expenses': 'Electricity Expenses',
            'postage_courier_services': 'Postage and Courier Services',
            'telephone_expenses': 'Telephone Expenses',
            'telephone_expenses_landline': 'Telephone Expenses (Landline)',
            'internet_subscription_expenses': 'Internet Subscription Expenses',
            'cable_satellite_telegraph_radio_expenses': 'Cable, Satellite, Telegraph & Radio Expenses',
            'awards_rewards_expenses': 'Awards/Rewards Expenses',
            'prizes': 'Prizes',
            'survey_expenses': 'Survey Expenses',
            'survey_research_exploration_development_expenses': 'Survey, Research, Exploration, and Development expenses',
            'legal_services': 'Legal Services',
            'auditing_services': 'Auditing Services',
            'consultancy_services': 'Consultancy Services',
            'other_professional_servies': 'Other Professional Services',
            'security_services': 'Security Services',
            'janitorial_services': 'Janitorial Services',
            'other_general_services': 'Other General Services',
            'environment/sanitary_services': 'Environment/Sanitary Services',
            'repair_maintenance_land_improvements': 'Repair & Maintenance - Land Improvements',
            'buildings': 'Buildings',
            'school_buildings': 'School Buildings',
            'hostel_dormitories': 'Hostels and Dormitories',
            'other_structures': 'Other Structures',
            'repair_maintenance_machinery': 'Repair & Maintenance - Machinery',
            'repair_maintenance_office_equipment': 'Repair & Maintenance - Office Equipment',
            'repair_maintenance_ict_equipment': 'Repair & Maintenance - ICT Equipment',
            'repair_maintenance_agri_forestry_equipment': 'Repair & Maintenance - Agricultural and Forestry Equipment',
            'repair_maintenance_marine_fishery_equipment': 'Repair & Maintenance - Marine and Fishery Equipment',
            'repair_maintenance_airport_equipment': 'Repair & Maintenance - Airport Equipment',
            'repair_maintenance_communication_equipment': 'Repair & Maintenance - Communication Equipment',
            'repair_maintenance_drre_equipment': 'Repair & Maintenance - Disaster, Response and Rescue Equipment',
            'repair_maintenance_medical_equipment': 'Repair & Maintenance - Medical Equipment',
            'repair_maintenance_printing_equipment': 'Repair & Maintenance - Printing Equipment',
            'repair_maintenance_sports_equipment': 'Repair & Maintenance - Sports Equipment',
            'repair_maintenance_technical_scientific_equipment': 'Repair & Maintenance - Technical and Scientific Equipment',
            'repair_maintenance_other_machinery_equipment': 'Repair & Maintenance - Other Machinery and Equipment',
            'repair_maintenance_motor': 'Repair & Maintenance - Motor Vehicles',
            'repair_maintenance_other_transportation_equipment': 'Repair & Maintenance - Other Transportation Equipment',
            'repair_maintenance_furniture_fixtures': 'Repair & Maintenance - Furniture & Fixtures',
            'repair_maintenance_semi_expendable_machinery_equipment': 'Repair & Maintenance - Semi-Expendable Machinery and Equipment',
            'repair_maintenance_other_property_plant_equipment': 'Repair & Maintenance - Other Property, Plant and Equipment',
            'taxes_duties_licenses': 'Taxes, Duties and Licenses',
            'fidelity_bond_premiums': 'Fidelity Bond Premiums',
            'insurance_expenses': 'Insurance Expenses',
            'labor_wages': 'Labor and Wages',
            'advertising_expenses': 'Advertising Expenses',
            'printing_publication_expenses': 'Printing and Publication Expenses',
            'representation_expenses': 'Representation Expenses',
            'transportation_delivery_expenses': 'Transportation and Delivery Expenses',
            'rent/lease_expenses': 'Rent/Lease Expenses',
            'membership_dues_contribute_to_org': 'Membership Dues and contributions to organizations',
            'subscription_expenses': 'Subscription Expenses',
            'website_maintenance': 'Website Maintenance',
            'other_maintenance_operating_expenses': 'Other Maintenance and Operating Expenses',
        }
        
        line_item_groups = {}
        
        for pre in pres_queryset:
            # Get line item budgets instead of parsing JSON
            line_items = PRELineItemBudget.objects.filter(pre=pre)
            
            for line_item in line_items:
                if line_item.remaining_amount > 0:
                    key = f"{pre.id}|{line_item.item_key}"
                    
                    if key not in line_item_groups:
                        line_item_groups[key] = {
                            'pre_id': pre.id,
                            'item_key': line_item.item_key,
                            'label': friendly_labels.get(line_item.item_key, line_item.item_key.replace('_', ' ').title()),
                            'total_remaining': Decimal('0'),
                            'total_allocated': Decimal('0'),
                            'quarters': []
                        }
                        
                    line_item_groups[key]['total_remaining'] += line_item.remaining_amount
                    line_item_groups[key]['total_allocated'] += line_item.allocated_amount
                    line_item_groups[key]['quarters'].append({
                        'quarter': line_item.quarter,
                        'remaining': line_item.remaining_amount
                    })   
                                     
        # Create options from grouped data
        for group_key, group_data in line_item_groups.items():
            display = f"{group_data['label']} - ₱{intcomma(group_data['total_remaining'])}"
            
            # Encode all quarters for this line item
            quarters_data = "|".join([f"{q['quarter']}:{q['remaining']}" for q in group_data['quarters']])
            encoded = f"{group_data['pre_id']}|{group_data['item_key']}|{quarters_data}"
            
            options.append({'value': encoded, 'label': display})
        return options
    
@role_required('end_user', login_url='/')
def load_source_of_fund(request):
    ba_id = request.GET.get("budget_allocation")
    source_of_fund_options = []

    if ba_id:
        print("budget allocation ID:", ba_id)
        try:
            allocation = BudgetAllocation.objects.get(
                id=ba_id,
                department=getattr(request.user, 'department', '')
            )

            # ✅ filter PREs linked to that allocation
            approved_pres = DepartmentPRE.objects.filter(
                budget_allocation=allocation,
                submitted_by=request.user.id,
                approved_by_approving_officer=True,
                approved_by_admin=True,
            )

            # ✅ reuse your builder
            source_of_fund_options = build_pre_source_options(approved_pres)

        except BudgetAllocation.DoesNotExist:
            print("No such budget allocation for this user.")
            source_of_fund_options = []
        
    else:
        print("No budget allocation ID provided.")

    return render(
        request,
        "end_user_app/partials/source_of_fund_options.html",
        {"source_of_fund_options": source_of_fund_options}
    )
