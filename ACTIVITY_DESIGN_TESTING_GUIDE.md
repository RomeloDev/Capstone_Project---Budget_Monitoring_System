# Activity Design Fix - Testing Guide

## Changes Implemented

### 1. New File Created
- **File:** `apps/admin_panel/ad_to_pdf_converter.py`
- **Purpose:** Convert Activity Design documents (.docx, .doc) to PDF
- **Lines:** 147 lines

### 2. Modified File
- **File:** `apps/end_user_app/views.py`
- **Changes:**
  - Line 4561-4571: Added AD document PDF conversion
  - Line 4605-4616: Added supporting documents PDF conversion
  - Line 4618-4620: Removed immediate budget consumption (critical fix)

### 3. Files NOT Changed (Already Correct)
- `apps/budgets/signals.py` - Signal already handles budget consumption on approval
- `apps/budgets/models.py` - Model already has `original_ad_pdf` field

---

## Testing Checklist

### Test 1: PDF Conversion for AD Document ✓

**Steps:**
1. Log in as end user
2. Navigate to "PR & AD Request" > "Upload Activity Design"
3. Upload a .docx Activity Design document
4. Fill in all required fields (select PRE line items, enter amounts, purpose)
5. Submit the Activity Design

**Expected Results:**
- [ ] AD submitted successfully with status "Pending"
- [ ] Console shows: "✅ AD PDF generated successfully: [URL]"
- [ ] Check database: ActivityDesign record has `original_ad_pdf` field populated
- [ ] File exists in `media/ad/original_pdfs/` directory
- [ ] PDF filename format: `AD_[AD_NUMBER]_[TIMESTAMP].pdf`

**Verification:**
```python
# In Django shell
from apps.budgets.models import ActivityDesign
ad = ActivityDesign.objects.latest('created_at')
print(f"AD Number: {ad.ad_number}")
print(f"Original Doc: {ad.uploaded_document}")
print(f"PDF: {ad.original_ad_pdf}")  # Should be populated
print(f"PDF URL: {ad.original_ad_pdf.url if ad.original_ad_pdf else 'None'}")
```

---

### Test 2: PDF Conversion for Supporting Documents ✓

**Steps:**
1. When submitting AD, upload supporting documents:
   - Upload .xlsx file (e.g., "Budget_Breakdown.xlsx")
   - Upload .docx file (e.g., "Supporting_Letter.docx")
   - Upload .pdf file (e.g., "Reference.pdf")

**Expected Results:**
- [ ] Console shows: "✅ AD supporting doc converted to PDF: [URL]" for .xlsx and .docx
- [ ] No conversion message for .pdf (already PDF)
- [ ] Check database: ActivityDesignSupportingDocument records have `pdf_version` field populated
- [ ] PDF files exist in `media/ad_supporting_docs/pdfs/` directory

**Verification:**
```python
# In Django shell
from apps.budgets.models import ActivityDesign, ActivityDesignSupportingDocument
ad = ActivityDesign.objects.latest('created_at')
for doc in ad.supporting_documents.all():
    print(f"File: {doc.file_name}")
    print(f"  Extension: {doc.get_file_extension()}")
    print(f"  PDF Version: {doc.pdf_version.url if doc.pdf_version else 'None'}")
```

---

### Test 3: Budget Consumption - Pending Status (Critical Fix) ✓

**Steps:**
1. Before submitting AD, record current budget values:
   - Go to Budget Monitoring Dashboard
   - Note: "Total Used", "Total Remaining", "AD Amount Used"
2. Submit new Activity Design with amount ₱50,000.00
3. AD should have status "Pending"

**Expected Results:**
- [ ] AD created with status "Pending"
- [ ] Budget Monitoring Dashboard shows:
  - **Total Used:** SAME as before (no change)
  - **Total Remaining:** SAME as before (no change)
  - **AD Amount Used:** SAME as before (no change)
- [ ] Console does NOT show budget consumption messages

**Verification:**
```python
# In Django shell
from apps.budgets.models import ActivityDesign, BudgetAllocation
from decimal import Decimal

# Get latest AD
ad = ActivityDesign.objects.latest('created_at')
print(f"AD Number: {ad.ad_number}")
print(f"Status: {ad.status}")  # Should be "Pending"
print(f"Amount: ₱{ad.total_amount:,.2f}")

# Get budget allocation
allocation = ad.budget_allocation
print(f"\nBudget Allocation: {allocation.approved_budget.title}")
print(f"AD Amount Used: ₱{allocation.ad_amount_used:,.2f}")
print(f"Total Used: ₱{allocation.get_total_used():,.2f}")
print(f"Remaining: ₱{allocation.remaining_balance:,.2f}")

# IMPORTANT: AD Amount Used should NOT include the pending AD
```

---

### Test 4: Budget Consumption - Approval (Signal Trigger) ✓

**Steps:**
1. As admin, approve the Activity Design (final approval):
   - Set status to "Approved"
   - Set `final_approved_at` timestamp
2. Check budget values after approval

**Expected Results:**
- [ ] AD status changed to "Approved"
- [ ] Budget Monitoring Dashboard shows:
  - **Total Used:** INCREASED by AD amount
  - **AD Amount Used:** INCREASED by AD amount
  - **Total Remaining:** DECREASED by AD amount
- [ ] Signal executed successfully (check console/logs)

**Verification:**
```python
# In Django shell (after approval)
from apps.budgets.models import ActivityDesign, BudgetAllocation

# Get the AD
ad = ActivityDesign.objects.get(ad_number='AD-2025-0001')  # Use actual AD number
print(f"AD Number: {ad.ad_number}")
print(f"Status: {ad.status}")  # Should be "Approved"
print(f"Amount: ₱{ad.total_amount:,.2f}")
print(f"Final Approved At: {ad.final_approved_at}")

# Get budget allocation
allocation = ad.budget_allocation
print(f"\nBudget Allocation: {allocation.approved_budget.title}")
print(f"AD Amount Used: ₱{allocation.ad_amount_used:,.2f}")
print(f"Total Used: ₱{allocation.get_total_used():,.2f}")
print(f"Remaining: ₱{allocation.remaining_balance:,.2f}")

# AD Amount Used should NOW include this AD
```

---

### Test 5: Preview AD Documents Page ✓

**Steps:**
1. After submitting AD, navigate to preview page
2. Check if AD document PDF is displayed
3. Check if supporting document PDFs are displayed

**Expected Results:**
- [ ] AD document preview shows PDF version
- [ ] Supporting documents show PDF previews (for .docx, .xlsx)
- [ ] Original documents are still downloadable
- [ ] No errors on preview page

---

### Test 6: Purchase Request Regression Test ✓

**Purpose:** Ensure PR workflow still works correctly after changes

**Steps:**
1. Submit new Purchase Request with .docx document
2. Upload supporting documents (.xlsx, .docx)
3. Check budget consumption (should NOT increase for Pending)
4. Approve PR
5. Check budget consumption (should increase on Approved)

**Expected Results:**
- [ ] PR PDF conversion still works
- [ ] PR supporting doc conversion still works
- [ ] PR budget consumption timing unchanged (only on approval)
- [ ] No errors or issues with PR workflow

---

### Test 7: Multiple AD Submissions ✓

**Purpose:** Test signal doesn't cause double-counting

**Steps:**
1. Submit AD #1: ₱30,000 → Status Pending
2. Submit AD #2: ₱20,000 → Status Pending
3. Check budget: Should NOT include either AD
4. Approve AD #1 → Status Approved
5. Check budget: Should include only AD #1 (₱30,000)
6. Approve AD #2 → Status Approved
7. Check budget: Should include both (₱50,000 total)

**Expected Results:**
- [ ] Budget increases only when each AD is approved
- [ ] No double-counting
- [ ] Amounts match exactly

---

## Database Verification Queries

### Check AD PDF Fields
```sql
SELECT
    ad_number,
    status,
    total_amount,
    uploaded_document,
    original_ad_pdf,
    created_at
FROM budgets_activitydesign
ORDER BY created_at DESC
LIMIT 5;
```

### Check Budget Allocation
```sql
SELECT
    ba.id,
    ab.title,
    ba.allocated_amount,
    ba.ad_amount_used,
    ba.pr_amount_used,
    ba.remaining_balance
FROM budgets_budgetallocation ba
JOIN budgets_approvedbudget ab ON ba.approved_budget_id = ab.id
WHERE ba.end_user_id = [USER_ID];
```

### Check AD Supporting Documents
```sql
SELECT
    ad.ad_number,
    asd.file_name,
    asd.document,
    asd.pdf_version
FROM budgets_activitydesignsupportingdocument asd
JOIN budgets_activitydesign ad ON asd.activity_design_id = ad.id
ORDER BY asd.uploaded_at DESC;
```

---

## Common Issues & Troubleshooting

### Issue: PDF Conversion Failed
**Symptoms:** Console shows "⚠️ AD PDF generation failed (non-blocking)"

**Possible Causes:**
1. LibreOffice not installed or not at `C:\Program Files\LibreOffice\program\soffice.exe`
2. Document is corrupted
3. File permissions issue

**Solutions:**
1. Check LibreOffice installation path
2. Try uploading a different .docx file
3. Check media folder permissions

**Impact:** Non-critical - AD still submitted, just no PDF preview

---

### Issue: Budget Not Updating on Approval
**Symptoms:** After approving AD, `ad_amount_used` doesn't increase

**Possible Causes:**
1. `final_approved_at` not set
2. Signal not firing
3. Status not exactly "Approved"

**Solutions:**
```python
# Manual fix in Django shell
from apps.budgets.models import ActivityDesign
from django.utils import timezone

ad = ActivityDesign.objects.get(ad_number='AD-2025-0001')
ad.status = 'Approved'
ad.final_approved_at = timezone.now()
ad.save()  # This should trigger the signal

# Check budget
allocation = ad.budget_allocation
print(f"AD Amount Used: {allocation.ad_amount_used}")
```

---

### Issue: Double-Counting of Budget
**Symptoms:** Budget consumed twice for single AD

**Cause:** Old code not properly removed

**Solution:** Check views.py line 4618-4620, ensure budget consumption lines are removed

---

## Success Criteria Summary

All tests pass when:

- [x] AD documents convert to PDF automatically
- [x] Supporting documents convert to PDF (for .docx, .xlsx)
- [x] PDFs viewable in preview page
- [x] Budget NOT consumed when AD status="Pending"
- [x] Budget consumed when AD status="Approved"
- [x] No double-counting of amounts
- [x] PR workflow unaffected (regression test pass)
- [x] Dashboard shows correct "Total Used" amounts

---

## Rollback Instructions

If critical issues occur:

1. **Stop accepting new AD submissions**
2. **Restore views.py backup:**
   ```bash
   git diff HEAD apps/end_user_app/views.py
   git checkout HEAD -- apps/end_user_app/views.py
   ```
3. **Delete ad_to_pdf_converter.py:**
   ```bash
   rm apps/admin_panel/ad_to_pdf_converter.py
   ```
4. **Recalculate budgets:**
   ```bash
   python manage.py recalculate_budgets
   ```

---

## Post-Deployment Monitoring

**First 24 Hours:**
- Monitor console/logs for PDF conversion errors
- Check first 3-5 AD submissions manually
- Verify budget calculations on dashboard
- Compare with PR submissions (should behave identically)

**First Week:**
- Review all AD submissions
- Check for any budget discrepancies
- Verify PDFs are accessible in preview pages
- Collect user feedback

---

## Contact for Issues

If issues persist:
1. Check `ACTIVITY_DESIGN_PDF_FIX_PLAN.md` for detailed implementation notes
2. Review signal logs in `apps/budgets/signals.py`
3. Run `python manage.py recalculate_budgets` to fix budget discrepancies
