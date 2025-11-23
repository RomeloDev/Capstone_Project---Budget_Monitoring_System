# Activity Design PDF Conversion & Budget Consumption Fix - Implementation Plan

## Issues Identified

### Issue 1: No Auto-Convert to PDF for Activity Design Documents
**Current State:**
- Purchase Request (PR) documents are automatically converted to PDF after submission
- Activity Design (AD) documents are NOT converted to PDF after submission
- This affects the Preview AD Documents page where PDFs are expected

**Location in Code:**
- PR conversion happens in `views.py:1090-1134` (purchase_request_upload function)
- AD submission happens in `views.py:4529-4614` (activity_design_upload function)
- AD submission does NOT include PDF conversion logic

### Issue 2: Activity Design Amount Consumed Immediately on Submission (Status="Pending")
**Current State:**
- AD amounts are consumed immediately when submitted (line 4594: `budget_allocation.ad_amount_used += total_amount`)
- PR amounts are consumed only when status changes to "Approved" (via signals.py:81-100)
- This inconsistency causes AD pending submissions to reduce available budget prematurely

**Location in Code:**
- AD: `views.py:4594` - Immediate consumption during submission
- PR: `signals.py:81-100` - Consumption only on approval via signal
- AD Signal: `signals.py:103-130` - Signal exists but amount already consumed during submission

---

## Root Cause Analysis

### PDF Conversion Issue
1. **PR Workflow (CORRECT):**
   ```python
   # Line 1090-1100 in purchase_request_upload
   if pr.uploaded_document:
       from apps.admin_panel.pr_to_pdf_converter import generate_pr_pdf
       pdf_url = generate_pr_pdf(pr)
   ```
   - Converts .docx/.doc to PDF
   - Saves to `original_pr_pdf` field
   - Also converts supporting documents (line 1123-1134)

2. **AD Workflow (MISSING):**
   ```python
   # Line 4529-4614 in activity_design_upload
   activity_design = ActivityDesign.objects.create(...)
   activity_design.uploaded_document.save(...)
   # ❌ NO PDF CONVERSION HERE
   ```
   - AD has `original_ad_pdf` field (models.py:934-939) but it's never populated
   - Supporting documents are copied but not converted to PDF

### Budget Consumption Timing Issue
1. **PR Workflow (CORRECT):**
   ```python
   # views.py:1052-1162
   pr = NewPurchaseRequest.objects.create(status='Pending', ...)
   # ❌ Does NOT modify budget_allocation.pr_amount_used here

   # signals.py:71-100
   @receiver(post_save, sender=PurchaseRequest)
   def update_budget_on_pr_approval(sender, instance, created, **kwargs):
       if instance.status == 'Approved' and instance.final_approved_at:
           allocation.pr_amount_used += instance.total_amount  # ✅ Only on approval
   ```

2. **AD Workflow (INCORRECT):**
   ```python
   # views.py:4593-4595
   activity_design = ActivityDesign.objects.create(status='Pending', ...)
   budget_allocation.ad_amount_used += total_amount  # ❌ WRONG: Immediate consumption
   budget_allocation.update_remaining_balance()

   # signals.py:102-130
   @receiver(post_save, sender=ActivityDesign)
   def update_budget_on_ad_approval(sender, instance, created, **kwargs):
       if instance.status == 'Approved' and instance.final_approved_at:
           allocation.ad_amount_used += instance.total_amount  # ⚠️ DOUBLE COUNTING!
   ```

---

## Implementation Plan

### Phase 1: Create AD PDF Converter Module
**File:** `apps/admin_panel/ad_to_pdf_converter.py` (NEW)

**Implementation:**
1. Copy structure from `pr_to_pdf_converter.py`
2. Adapt for ActivityDesign model:
   - Use `original_ad_pdf` field instead of `original_pr_pdf`
   - Use `ad_number` instead of `pr_number`
   - Handle .docx/.doc to PDF conversion using LibreOffice
   - Handle already-PDF documents (copy as-is)

**Functions:**
- `generate_ad_pdf(ad)` - Main conversion function
- `convert_word_to_pdf(word_path)` - Reuse from PR converter
- `save_pdf_to_ad(ad, pdf_content)` - Save to ActivityDesign model

**Risk:** Low - Copying proven PR converter logic

---

### Phase 2: Add PDF Conversion to AD Submission
**File:** `apps/end_user_app/views.py` (MODIFY)

**Changes in `activity_design_upload` function (line 4529-4614):**

1. **After ActivityDesign creation (around line 4559):**
   ```python
   # Convert AD document to PDF for admin preview
   if activity_design.uploaded_document:
       try:
           from apps.admin_panel.ad_to_pdf_converter import generate_ad_pdf
           pdf_url = generate_ad_pdf(activity_design)
           if pdf_url:
               print(f"✅ AD PDF generated successfully: {pdf_url}")
           else:
               print(f"⚠️ AD PDF generation failed (non-blocking)")
       except Exception as pdf_error:
           print(f"⚠️ AD PDF generation error: {pdf_error}")
   ```

2. **After supporting document creation (around line 4591):**
   ```python
   # Convert Excel/Word supporting documents to PDF
   file_ext = ad_doc.get_file_extension()
   if file_ext in ['xlsx', 'xls', 'docx', 'doc']:
       try:
           from apps.admin_panel.supporting_doc_converter import convert_pre_supporting_doc
           pdf_url = convert_pre_supporting_doc(ad_doc)
           if pdf_url:
               print(f"✅ AD supporting doc converted to PDF: {pdf_url}")
           else:
               print(f"⚠️ Could not convert {ad_doc.file_name} to PDF (non-blocking)")
       except Exception as conv_error:
           print(f"⚠️ PDF conversion error for {ad_doc.file_name}: {conv_error}")
   ```

**Risk:** Low - Non-blocking, won't fail submission if conversion fails

---

### Phase 3: Fix Activity Design Budget Consumption Timing
**File:** `apps/end_user_app/views.py` (MODIFY)

**Critical Change in `activity_design_upload` function (line 4593-4595):**

**REMOVE these lines:**
```python
# Update budget allocation
budget_allocation.ad_amount_used += total_amount  # ❌ DELETE THIS LINE
budget_allocation.update_remaining_balance()      # ❌ DELETE THIS LINE
```

**Reason:**
- The signal `update_budget_on_ad_approval` (signals.py:102-130) already handles this
- Consumption should only happen when status='Approved' AND final_approved_at is set
- Current code causes DOUBLE COUNTING and premature consumption

**Impact:**
- AD submissions with status='Pending' will NOT consume budget
- Budget only consumed when admin approves (status='Approved')
- Matches PR behavior exactly

**Risk:** Medium - Changes budget calculation logic
- Need thorough testing
- Verify dashboard amounts update correctly
- Check existing "Pending" ADs don't cause issues

---

### Phase 4: Testing & Verification

**Test Cases:**

1. **AD PDF Conversion Test:**
   - [ ] Submit AD with .docx document → Check `original_ad_pdf` is populated
   - [ ] Submit AD with .doc document → Check PDF conversion works
   - [ ] Submit AD with .xlsx supporting doc → Check PDF conversion
   - [ ] Submit AD with .docx supporting doc → Check PDF conversion
   - [ ] Verify preview_ad_documents.html shows PDFs correctly

2. **Budget Consumption Test:**
   - [ ] Check initial budget allocation remaining balance
   - [ ] Submit new AD (status='Pending')
   - [ ] Verify `ad_amount_used` does NOT increase
   - [ ] Verify dashboard "Total Used" does NOT include pending AD
   - [ ] Admin partially approves AD
   - [ ] Verify `ad_amount_used` still NOT increased
   - [ ] Admin gives final approval (status='Approved', final_approved_at set)
   - [ ] Verify `ad_amount_used` NOW increases by AD amount
   - [ ] Verify dashboard "Total Used" NOW includes approved AD

3. **Regression Test (PR Workflow):**
   - [ ] Submit new PR (status='Pending')
   - [ ] Verify `pr_amount_used` does NOT increase
   - [ ] Approve PR
   - [ ] Verify `pr_amount_used` increases correctly
   - [ ] Verify PDF conversion still works for PR

4. **Supporting Documents Test:**
   - [ ] Upload .xlsx supporting doc with AD
   - [ ] Verify PDF version is generated
   - [ ] Preview document in admin panel
   - [ ] Verify PDF displays correctly

---

## Rollback Plan

If issues occur:

1. **PDF Conversion Issues:**
   - Non-blocking by design (wrapped in try/except)
   - Can continue without PDF conversion
   - Fix converter and re-run manually for affected records

2. **Budget Consumption Issues:**
   - **Rollback Code:**
     ```python
     # Re-add to views.py:4593-4595
     budget_allocation.ad_amount_used += total_amount
     budget_allocation.update_remaining_balance()
     ```
   - **Data Fix (if needed):**
     ```python
     # Run management command to recalculate all budgets
     python manage.py recalculate_budgets
     ```

---

## Files to Modify

1. **NEW FILE:** `apps/admin_panel/ad_to_pdf_converter.py`
   - Create AD-specific PDF converter

2. **MODIFY:** `apps/end_user_app/views.py`
   - Add PDF conversion after AD creation (line ~4559)
   - Add PDF conversion for supporting docs (line ~4591)
   - Remove immediate budget consumption (line 4594-4595)

3. **NO CHANGES:** `apps/budgets/signals.py`
   - Signal `update_budget_on_ad_approval` already correct
   - Will work properly once views.py is fixed

4. **NO CHANGES:** `apps/budgets/models.py`
   - `original_ad_pdf` field already exists
   - No model changes needed

---

## Deployment Steps

1. Backup database before deployment
2. Create `ad_to_pdf_converter.py`
3. Modify `views.py` with all three changes
4. Run tests in development environment
5. Deploy to production
6. Monitor first AD submission closely
7. Verify budget calculations on dashboard
8. Run `recalculate_budgets` command if any discrepancies found

---

## Success Criteria

- [ ] AD documents automatically convert to PDF on submission
- [ ] AD supporting documents (.docx, .xlsx) convert to PDF
- [ ] PDFs are viewable in preview_ad_documents.html
- [ ] AD status='Pending' does NOT consume budget
- [ ] AD status='Approved' DOES consume budget (via signal)
- [ ] Dashboard Total Used only includes approved ADs (not pending)
- [ ] No double-counting of AD amounts
- [ ] PR workflow continues to work correctly (regression test pass)

---

## Estimated Impact

**Lines of Code:**
- New file: ~150 lines (ad_to_pdf_converter.py)
- Modified: ~30 lines (views.py changes)
- Removed: 2 lines (budget consumption fix)
- Total: ~180 lines changed/added

**Testing Time:** 2-3 hours
**Deployment Time:** 30 minutes
**Total Effort:** 4-5 hours
