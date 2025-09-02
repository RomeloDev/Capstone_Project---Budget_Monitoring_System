from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from apps.users.models import User
from .models import BudgetAllocation, Budget, ApprovedBudget, AuditTrail
from apps.users.models import User
from django.contrib import messages
from decimal import Decimal
from apps.end_user_app.models import PurchaseRequest, Budget_Realignment, DepartmentPRE
from apps.users.models import User
from django.db import transaction
from django.db.models import Sum
from django.template.defaultfilters import floatformat
from django.contrib.humanize.templatetags.humanize import intcomma
from django.utils import timezone
from django.core.paginator import Paginator
from .utils import log_audit_trail



# Create your views here.
@login_required
def admin_dashboard(request):
    try:
        end_users_total = User.objects.filter(is_staff=False, is_approving_officer=True).count()
        total_budget = Budget.objects.aggregate(Sum('total_fund'))['total_fund__sum']
        total_pending_realignment_request = Budget_Realignment.objects.filter(status='pending').count()
        total_approved_realignment_request = Budget_Realignment.objects.filter(status='approved').count()
        budget_allocated = BudgetAllocation.objects.all()
    except:
        end_users_total = 0
        total_budget = 0
        total_pending_realignment_request = 0
        total_approved_realignment_request = 0
        budget_allocated = None



    return render(request, 'admin_panel/dashboard.html', {'end_users_total': end_users_total,
    'total_budget': total_budget, 
    'total_pending_realignment_request': total_pending_realignment_request, 'total_approved_realignment_request': total_approved_realignment_request,
    'budget_allocated': budget_allocated,
    'intcomma': intcomma
    })

@login_required
def client_accounts(request):
    try:
        end_users = User.objects.filter(is_staff=False)
    except User.DoesNotExist:
        end_users = None
    return render(request, 'admin_panel/client_accounts.html', {'end_users': end_users})

@login_required
def register_account(request):
    
    if request.method == "POST":
         # Retrieval of value in input fields
        username = request.POST.get('username')
        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        department = request.POST.get('department')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm-password')
        position = request.POST.get('position')
        
        # Validate password confirmation
        if password != confirm_password:
            return render(request, 'admin_panel/client_accounts.html', {'error': 'Passwords do not match'})
        
        # Check if the department or username or email are already exists
        if User.objects.filter(username=username).exists():
            return render(request, 'admin_panel/client_accounts.html', {'error': 'Username already taken.'})

        if User.objects.filter(email=email).exists():
            return render(request, 'admin_panel/client_accounts.html', {'error': f'Email {email} already registered.'})
        
        if User.objects.filter(department=department).exists():
            return render(request, 'admin_panel/client_accounts.html', {'error': f'Department {department} already registered.'})
        
        if department == 'Approving-Officer':
            approving_officer = User.objects.create_approving_officer(username=username, fullname=fullname, email=email, password=password)
            return render(request, "admin_panel/client_accounts.html", {'success': "Approving Officer Account registered successfully!"})
        else:
            # Create and save the user
            user = User.objects.create_user(username=username, fullname=fullname, email=email, password=password, department=department, position=position)
            
            try:
                end_users = User.objects.filter(is_staff=False)
            except User.DoesNotExist:
                end_users = None
            return render(request, "admin_panel/client_accounts.html", {'success': "Account registered successfully!", 'end_users': end_users})

@login_required
def departments_pr_request(request):
    departments = User.objects.filter(is_staff=False, is_approving_officer=False).values_list('department', flat=True).distinct()
    
    filter_department = request.GET.get('department')
    if filter_department:
        users_purchase_requests = PurchaseRequest.objects.filter(requested_by__department=filter_department, pr_status='Submitted', submitted_status='Pending', approved_by_approving_officer=False).select_related('requested_by', 'budget_allocation__approved_budget', 'source_pre')
    
    try:
        users_purchase_requests = PurchaseRequest.objects.filter(pr_status='Submitted', approved_by_admin=False, approved_by_approving_officer=False).select_related('requested_by', 'budget_allocation__approved_budget', 'source_pre')
    except PurchaseRequest.DoesNotExist:
        users_purchase_requests = None
        
    return render(request, 'admin_panel/departments_pr_request.html', {'users_purchase_requests': users_purchase_requests,                'departments': departments})

@login_required
def handle_departments_request(request, request_id):
    """
    Optional admin handler for PRs. Aligns with model fields and updates allocation.
    Note: Approving Officer flow is canonical; consider removing this view if redundant.
    """
    purchase_request = get_object_or_404(PurchaseRequest, id=request_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        allocation = purchase_request.budget_allocation
        if action == 'approve':
            if allocation is None:
                messages.error(request, 'No budget allocation linked to this request.')
                return redirect('department_pr_request')
            if allocation.remaining_budget < (purchase_request.total_amount or 0):
                messages.error(request, 'Insufficient remaining budget to approve this request.')
                return redirect('department_pr_request')
            allocation.spent = (allocation.spent or 0) + (purchase_request.total_amount or 0)
            allocation.save(update_fields=['spent', 'updated_at'])
            purchase_request.pr_status = 'Submitted'
            purchase_request.submitted_status = 'Partially Approved'
            purchase_request.approved_by_admin = True
        elif action == 'reject':
            purchase_request.pr_status = 'Submitted'
            purchase_request.submitted_status = 'Rejected'

        purchase_request.save(update_fields=['pr_status', 'submitted_status', 'updated_at', 'approved_by_admin'])

    return redirect('department_pr_request')

@login_required
def budget_allocation(request):
    approved_budgets = ApprovedBudget.objects.all()
    departments = User.objects.filter(is_staff=False, is_approving_officer=False).values_list('department', flat=True).distinct()
    
    if request.method == 'POST':
        department = request.POST.get('department')
        approved_budget_id = request.POST.get('approved_budget')
        amount = request.POST.get('amount')
        
        # Validation
        if not department or not approved_budget_id or not amount:
            messages.error(request, "All fields are required.")
            return redirect('budget_allocation')
        
        try:
            amount = float(amount)
            if amount < 0:
                raise ValueError("Amount cannot be negative.")
        except ValueError:
            messages.error(request, "Enter a valid non-negative amount.")
            return redirect('budget_allocation')
        
        try:
            approved_budget = ApprovedBudget.objects.get(id=approved_budget_id)
        except ApprovedBudget.DoesNotExist:
            messages.error(request, "Selected approved budget does not exist.")
            return redirect('budget_allocation')
        
        # Prevent duplicate department allocations for same approved budget
        existing = BudgetAllocation.objects.filter(department=department, approved_budget=approved_budget).exists()
        if existing:
            messages.warning(request, "This department already has an allocation under this budget.")
            return redirect('budget_allocation')

        # Save Allocations
        BudgetAllocation.objects.create(
            department=department,
            approved_budget= approved_budget,
            total_allocated = amount
        )
        
        # Force update the approved budget’s updated_at field
        approved_budget.updated_at = timezone.now()
        approved_budget.save(update_fields=['updated_at'])
        
        
        messages.success(request, "Budget successfully allocated.")
        log_audit_trail(
            request=request,
            action='CREATE',
            model_name='BudgetAllocation',
            record_id=None,  # No specific record ID for creation
            detail=f"Allocated {intcomma(amount)} to {department} from approved budget: {approved_budget.title}."
        )
        return redirect('budget_allocation')
    
    # --- 📊 Load existing allocations for table view ---
    allocations = (
        BudgetAllocation.objects
        .select_related('approved_budget')
        .order_by('-allocated_at')
    )
    
    return render(request, "admin_panel/budget_allocation.html", {'approved_budgets': approved_budgets, 'departments': departments, 'budgets': allocations})
    
# This is the Approved Budget View
@login_required
def institutional_funds(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        period = request.POST.get('period')
        amount = request.POST.get('amount')
        
        # Validation
        if not title or not period or not amount:
            messages.error(request, "All fields are required.")
            return redirect("institutional_funds")
        else:
            try:
                amount = Decimal(amount)
            except (ValueError, TypeError):
                messages.error(request, "Invalid amount entered.")
                return redirect("institutional_funds")
        
            # Create the approved budget
            ApprovedBudget.objects.create(
                title=title,
                period=period,
                amount=amount
            )
            messages.success(request, "Approved budget successfully added.")
            log_audit_trail(
                request=request,
                action='CREATE',
                model_name='ApprovedBudget',
                record_id=None,  # No specific record ID for creation
                detail=f"Created approved budget: {title} for period {period} with amount {intcomma(amount)}."
            )
            return redirect("institutional_funds")
        
    approved_budgets = ApprovedBudget.objects.order_by('-created_at')
    return render(request, 'admin_panel/institutional_funds.html', {'approved_budgets': approved_budgets})

@login_required
def admin_logout(request):
    log_audit_trail(
        request=request,
        action='LOGOUT',
        model_name='User',
        record_id=request.user.id,
        detail=f"User {request.user.username} logged out."
    )
    logout(request)
    return redirect('admin_login')

@login_required
def audit_trail(request):
    # Get all audit records and users
    audit_records = AuditTrail.objects.select_related('user').all()
    departments = User.objects.all().values_list('department', flat=True).distinct()
    
    # Filter by department
    department = request.GET.get('department')
    if department:
        audit_records = audit_records.filter(user__department=department)
    
    # Filter by action if specified
    action_filter = request.GET.get('action')
    if action_filter:
        audit_records = audit_records.filter(action=action_filter)
        
    # Filter by date range if specified
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        audit_records = audit_records.filter(
            timestamp__date__range=[start_date, end_date]
        )
        
    # Pagination
    paginator = Paginator(audit_records, 15)  # 15 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'action_choices': AuditTrail.ACTION_CHOICES,
        'departments': departments
    }
    return render(request, 'admin_panel/audit_trail.html', context)

@login_required
def budget_re_alignment(request):
    try:
        re_alignment_request = Budget_Realignment.objects.all()
    except Budget_Realignment.DoesNotExist:
        re_alignment_request = None
    return render(request, 'admin_panel/budget_re-alignment.html', {'re_alignment_request': re_alignment_request})

@login_required
def handle_re_alignment_request_action(request, pk):
    req = get_object_or_404(Budget_Realignment, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            try:
                with transaction.atomic():
                    source_alloc = BudgetAllocation.objects.select_for_update().get(papp=req.source_papp)
                    target_alloc = BudgetAllocation.objects.select_for_update().get(papp=req.target_papp)
                    
                    if source_alloc.remaining_budget < req.amount:
                        messages.error(request, "Insufficient budget in source PAPP to realign.")
                        return redirect('budget_re_alignment')
                    
                    # Deduct from source and add to target
                    source_alloc.remaining_budget -= req.amount
                    target_alloc.remaining_budget += req.amount
                    
                    # Save both allocations
                    source_alloc.save()
                    target_alloc.save()

                    # Update request status
                    req.status = 'Approved'
                    req.approved_by = request.user
                    req.save()
                    
                    messages.success(request, f'Budget Realignment Request of {req.requested_by.department} has been approved.')
            except BudgetAllocation.DoesNotExist:
                messages.error(request, "Source or Target PAPP not found.")
            except Exception as e:
                messages.error(request, f"Something went wrong: {e}")
        elif action == 'reject':
            req.status = 'rejected'
            req.approved_by = request.user
            req.save()
            messages.error(request, f'Budget Realignment Request of {req.requested_by.department} has been rejected.')

        
        
        # action = request.POST.get('action')
        # if action == 'approve':
        #     req.status = 'Approved'
        #     messages.success(request, f'Budget Realignment Request of {req.requested_by.department} has been approved.')
        # elif action == 'reject':
        #     req.status = 'Rejected'
        #     messages.error(request, f'Budget Realignment Request of {req.requested_by.department} has been rejected.')
        # req.approved_by = request.user
        # req.save()
        
    return redirect('budget_realignment')

@login_required
def pre_request_page(request):
    # Filter only PREs that were approved by the approving officer
    """
    View for the Admin to view all approved PREs from different departments.

    This view shows a table of all approved PREs, with the ability to filter by department.
    The table shows the department, submitted by, submitted on, budget allocation, and status of each PRE.
    """
    pres = DepartmentPRE.objects.filter(approved_by_approving_officer=False, approved_by_admin=False, status='Pending').select_related('submitted_by', 'budget_allocation__approved_budget').order_by('-created_at')

    # Department filter
    dept = request.GET.get('department')
    if dept:
        pres = pres.filter(department=dept)

    # Distinct department list for filter select
    departments = DepartmentPRE.objects.filter(approved_by_approving_officer=False, approved_by_admin=False).values_list('department', flat=True).distinct()

    return render(request, "admin_panel/pre_request.html", {
        'pres': pres,
        'departments': departments,
    })


@login_required
def admin_preview_pre(request, pk: int):
    pre = get_object_or_404(DepartmentPRE.objects.select_related('submitted_by', 'budget_allocation__approved_budget'), pk=pk)

    # Reuse the same simple aggregation scheme as AO preview
    from decimal import Decimal

    def to_decimal(value):
        try:
            return Decimal(str(value)) if value not in (None, "") else Decimal('0')
        except Exception:
            return Decimal('0')

    payload = pre.data or {}

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
        from decimal import Decimal as _D
        total_q1 = sum((it['q1'] for it in items if not it.get('is_group')), _D('0'))
        total_q2 = sum((it['q2'] for it in items if not it.get('is_group')), _D('0'))
        total_q3 = sum((it['q3'] for it in items if not it.get('is_group')), _D('0'))
        total_q4 = sum((it['q4'] for it in items if not it.get('is_group')), _D('0'))
        total_overall = sum((it['total'] for it in items if not it.get('is_group')), _D('0'))
        sections.append({'title': spec['title'], 'color_class': spec['color_class'], 'items': items, 'total_q1': total_q1, 'total_q2': total_q2, 'total_q3': total_q3, 'total_q4': total_q4, 'total_overall': total_overall})

    from decimal import Decimal as _DD
    grand_total_q1 = sum((sec['total_q1'] for sec in sections), _DD('0'))
    grand_total_q2 = sum((sec['total_q2'] for sec in sections), _DD('0'))
    grand_total_q3 = sum((sec['total_q3'] for sec in sections), _DD('0'))
    grand_total_q4 = sum((sec['total_q4'] for sec in sections), _DD('0'))
    grand_total_overall = sum((sec['total_overall'] for sec in sections), _DD('0'))

    return render(request, 'admin_panel/preview_pre.html', {
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


@login_required
def admin_handle_pre_action(request, pk: int):
    pre = get_object_or_404(DepartmentPRE, pk=pk)
    budget_allocation = get_object_or_404(BudgetAllocation, id=pre.budget_allocation_id)
    # budget_allocation = BudgetAllocation.objects.filter(department=pre.department, id=pre.budget_allocation_id).first
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            pre.status = 'Partially Approved'
            pre.approved_by_admin = True
            audit_trail_action = 'Partially APPROVE'
        elif action == 'reject':
            pre.status = 'Rejected'
            pre.approved_by_admin = False
            budget_allocation.is_compiled = False
            budget_allocation.save(update_fields=['is_compiled'])
            audit_trail_action = 'REJECT'
        pre.save()
        log_audit_trail(
            request=request,
            action=audit_trail_action,
            model_name='DepartmentPRE',
            record_id=pre.id,
            detail=f"Admin {action} a PRE with ID {pre.id} from department {pre.department}."
        )
    return redirect('pre_request_page')

@login_required
def preview_purchase_request(request, pk:int):
    pr = get_object_or_404(PurchaseRequest.objects.select_related('requested_by', 'budget_allocation__approved_budget', 'source_pre'),
        pk=pk,
    )
    
    return render(request, 'admin_panel/preview_purchase_request.html', {
        'pr': pr,
    })