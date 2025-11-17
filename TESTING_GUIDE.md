# Budget Savings Feature - Testing Guide

## Quick Start

**Development Server**: Running on `http://127.0.0.1:8000/`

---

## How to Access the Savings Feature

### Method 1: Via Navigation Menu
1. Open browser: `http://127.0.0.1:8000/admin/`
2. Login with admin credentials
3. Look in the left sidebar navigation
4. Click on "Budget Savings" (piggy bank icon 💰)

### Method 2: Direct URL
- Navigate to: `http://127.0.0.1:8000/admin/savings/`

---

## Testing Checklist

### ✅ Phase 1: Visual Inspection

**Navigate to Savings Page**
- [ ] Page loads without errors
- [ ] Header displays correctly (green gradient)
- [ ] Navigation link is highlighted
- [ ] Summary cards show data (Allocated, Used, Savings, Utilization)
- [ ] Filter section visible (Fiscal Year, Department)
- [ ] Data table displays
- [ ] Create Snapshot button visible
- [ ] Export to Excel button visible

### ✅ Phase 2: Filter Testing

**Test Fiscal Year Filter**
1. [ ] Select a fiscal year from dropdown
2. [ ] Click "Apply Filters"
3. [ ] Verify data updates for selected year
4. [ ] Check that summary cards update

**Test Department Filter**
1. [ ] Enter department name in search box
2. [ ] Click "Apply Filters"
3. [ ] Verify filtered results show only matching departments

**Clear Filters**
1. [ ] Click "Clear Filters" link
2. [ ] Verify all data is shown again

### ✅ Phase 3: Create Snapshot

**Open Modal**
1. [ ] Click "Create Snapshot" button
2. [ ] Modal opens with form

**Fill Form**
1. [ ] Select Fiscal Year (required)
2. [ ] Select Quarter (defaults to "Full Year")
3. [ ] Add notes (optional)
4. [ ] Click "Create Snapshot"

**Verify Results**
1. [ ] Success message appears
2. [ ] Page reloads
3. [ ] Snapshot count increases

### ✅ Phase 4: Excel Export

**Export Data**
1. [ ] Click "Export to Excel" button
2. [ ] File downloads automatically
3. [ ] Open the Excel file

**Verify Excel Contents**
- [ ] Headers are bold and colored (blue background)
- [ ] Data is properly formatted with currency
- [ ] Totals row at bottom
- [ ] All columns have appropriate widths
- [ ] Filename includes fiscal year and timestamp

### ✅ Phase 5: Django Admin

**Access Django Admin**
1. [ ] Go to `http://127.0.0.1:8000/admin/`
2. [ ] Login with superuser credentials
3. [ ] Find "Budget Savings" in the left menu

**Verify Admin Interface**
- [ ] List displays all savings snapshots
- [ ] Can filter by fiscal year, department, quarter
- [ ] Can search
- [ ] Currency amounts are formatted
- [ ] Can view individual snapshot details

---

## Expected Results

### Summary Cards (Example Values)

**With Sample Data:**
- **Total Allocated**: ₱5,000,000.00
- **Total Used**: ₱3,500,000.00
  - PR Used: ₱2,000,000.00
  - AD Used: ₱1,500,000.00
- **Total Savings**: ₱1,500,000.00
- **Utilization Rate**: 70.0%

**Without Data:**
- All values should show ₱0.00
- Table shows "No savings data available" message

### Data Table Columns

1. Department
2. Fiscal Year
3. Allocated (₱ formatted)
4. PR Used (₱ formatted)
5. AD Used (₱ formatted)
6. Total Used (₱ formatted)
7. Savings (₱ formatted, green color)
8. Utilization (%, color-coded)
   - Green: < 70%
   - Yellow: 70-90%
   - Red: > 90%

---

## Common Issues & Solutions

### Issue 1: Page Not Loading
**Error**: 404 Not Found
**Solution**:
- Check URL is correct: `/admin/savings/`
- Verify server is running
- Clear browser cache

### Issue 2: No Data Showing
**Cause**: No budget allocations in database
**Solution**:
1. Create an Approved Budget
2. Create Budget Allocations
3. Create some PRs and ADs
4. Refresh savings page

### Issue 3: Modal Not Opening
**Cause**: JavaScript not loaded
**Solution**:
- Check browser console for errors
- Ensure Alpine.js is loaded (look in page source)
- Try hard refresh (Ctrl+F5)

### Issue 4: Excel Export Not Working
**Error**: File not downloading
**Solution**:
- Check browser pop-up settings
- Look in Downloads folder
- Check server logs for errors

---

## Testing with Sample Data

### Option 1: Use Existing Data
If you already have budget allocations in your system, the savings will be calculated automatically!

### Option 2: Create Test Data

**Via Django Shell:**
```python
python manage.py shell

from apps.budgets.models import ApprovedBudget, BudgetAllocation
from apps.users.models import User
from decimal import Decimal

# Get or create admin user
admin = User.objects.filter(is_admin=True).first()
user = User.objects.filter(is_end_user=True).first()

# Create approved budget
budget = ApprovedBudget.objects.create(
    title="Test Budget 2025",
    fiscal_year="2025",
    amount=Decimal('5000000.00'),
    remaining_budget=Decimal('5000000.00'),
    created_by=admin
)

# Create allocation
allocation = BudgetAllocation.objects.create(
    approved_budget=budget,
    department="Information Technology",
    end_user=user,
    allocated_amount=Decimal('1000000.00'),
    remaining_balance=Decimal('1000000.00'),
    pr_amount_used=Decimal('300000.00'),
    ad_amount_used=Decimal('200000.00')
)

print("✅ Test data created!")
print(f"Allocated: ₱{allocation.allocated_amount:,.2f}")
print(f"Used: ₱{allocation.pr_amount_used + allocation.ad_amount_used:,.2f}")
print(f"Savings: ₱{allocation.remaining_balance:,.2f}")
```

**Via Django Admin:**
1. Go to `/admin/`
2. Click "Approved Budgets" → Add
3. Create a budget for 2025
4. Click "Budget Allocations" → Add
5. Link to the budget you created
6. Set amounts (allocated, PR used, AD used)
7. Save

---

## Verification Checklist

### Before Testing
- [x] Model created and migrated
- [x] Views created
- [x] URLs configured
- [x] Template created
- [x] Navigation link added
- [x] Admin registered
- [x] Server running

### After Testing
- [ ] Page accessible
- [ ] Filters work
- [ ] Calculations correct
- [ ] Snapshots created successfully
- [ ] Excel export works
- [ ] No console errors
- [ ] Mobile responsive
- [ ] Admin interface works

---

## Next Steps After Testing

### If Everything Works ✅
1. Mark Day 2 as complete
2. Move to Day 3 tasks:
   - Add more features (optional)
   - Improve UI based on feedback
   - Add quarterly breakdown (optional)

### If Issues Found ❌
1. Note the errors
2. Check browser console (F12)
3. Check server logs
4. Fix issues one by one
5. Re-test

---

## Screenshots Needed for Defense

Take screenshots of:
1. ✅ Savings overview page with data
2. ✅ Summary cards showing totals
3. ✅ Data table with multiple departments
4. ✅ Create snapshot modal
5. ✅ Success message after snapshot
6. ✅ Excel export (open file)
7. ✅ Django admin interface
8. ✅ Navigation menu with savings link

---

## Performance Notes

**Expected Load Times:**
- Page load: < 2 seconds
- Filter application: < 1 second
- Snapshot creation: < 3 seconds
- Excel export: < 2 seconds

**Database Queries:**
- Overview page: ~5-10 queries
- Optimized with `select_related()`
- Should handle 100+ departments easily

---

## Support

**If you encounter issues:**
1. Check this testing guide
2. Review browser console (F12)
3. Check server terminal for errors
4. Verify database has data
5. Try clearing browser cache

**Common URLs:**
- Admin Panel: `/admin/`
- Savings Overview: `/admin/savings/`
- Create Snapshot: `/admin/savings/create-snapshot/` (POST)
- Export Excel: `/admin/savings/export-excel/`

---

**Status**: Ready for Testing
**Server**: Running on port 8000
**Next**: Open browser and start testing!
