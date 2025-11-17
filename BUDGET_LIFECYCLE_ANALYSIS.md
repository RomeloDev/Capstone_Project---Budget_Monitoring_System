# BISU Budget Lifecycle Analysis

## Part A: Initial Entry

ApprovedBudget is created at institutional_funds() view.

Model: apps/budgets/models.py:58-110
View: apps/admin_panel/views.py:1781-2031

Fields:
- amount: Total budget
- remaining_budget: Available for allocation (initialized = amount)
- fiscal_year: Unique fiscal year
- created_by: Admin user

## Part B: Allocation

BudgetAllocation distributes to departments.

Model: apps/budgets/models.py:184-239
View: apps/admin_panel/views.py:1105-1411

Fields:
- allocated_amount: Department budget
- remaining_balance: allocated - (pr_used + ad_used)
- pre_amount_used, pr_amount_used, ad_amount_used

## Part C: Planning - PRE

DepartmentPRE creates quarterly budget plan.

Model: apps/budgets/models.py:241-476
Status: Draft -> Pending -> Partially Approved -> Approved

Key Method: approve_with_documents() (line 377-400)
When approved: budget_allocation.pre_amount_used += total_amount

## Part D: Quarterly Detail - PRE Line Items

PRELineItem breaks down per quarter.

Model: apps/budgets/models.py:923-1079
Fields: q1_amount, q2_amount, q3_amount, q4_amount

Key Method: get_quarter_consumed(quarter) (line 958-990)
Calculates: sum of PR/AD allocations with status Pending/Partially Approved/Approved

## Part E: Expenditure - PR and AD

PurchaseRequest: apps/budgets/models.py:478-693
ActivityDesign: apps/budgets/models.py:724-879

Budget consumed when status = Pending (not at approval)

## Part F: End States

Fully Spent: remaining_balance = 0
Partially Spent: remaining_balance > 0
Archived: is_archived = True

## Key Insight

Budget is marked consumed when PR/AD reaches Pending status (submitted),
NOT when finally approved.
This ensures accurate tracking of committed funds during approval workflow.
## DETAILED FLOWS AND ANALYSIS

### PRE Approval - Key Method

File: apps/budgets/models.py, line 377-400

def approve_with_documents(self, admin_user):
    was_already_approved = self.status == 'Approved'
    
    self.status = 'Approved'
    self.final_approved_at = timezone.now()
    
    if self.budget_allocation and not was_already_approved:
        correct_total = sum(item.get_total() for item in self.line_items.all())
        
        # KEY UPDATE - FIRST TIME BUDGET CONSUMED
        self.budget_allocation.pre_amount_used += correct_total
        self.budget_allocation.update_remaining_balance()
    
    self.save()

### Quarter Consumption - Real-Time Calculation

File: apps/budgets/models.py, line 958-990

def get_quarter_consumed(self, quarter):
    pr_consumed = PurchaseRequestAllocation.objects.filter(
        pre_line_item=self,
        quarter=quarter
    ).exclude(
        purchase_request__status__in=['Draft', 'Rejected', 'Cancelled']
    ).aggregate(
        total=Coalesce(Sum('allocated_amount'), Decimal('0.00'))
    )['total']
    
    ad_consumed = ActivityDesignAllocation.objects.filter(
        pre_line_item=self,
        quarter=quarter
    ).exclude(
        activity_design__status__in=['Draft', 'Rejected', 'Cancelled']
    ).aggregate(
        total=Coalesce(Sum('allocated_amount'), Decimal('0.00'))
    )['total']
    
    return pr_consumed + ad_consumed

### Key Insight

Budget is consumed when PR/AD status = Pending (submitted).
NOT when finally approved.
This enables:
- Accurate tracking of committed funds
- Visibility of pending amounts
- Rollback if rejected

