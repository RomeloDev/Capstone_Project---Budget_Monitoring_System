# Activity Design Workflow Implementation - Continuation Guide

## Context
This document contains the remaining implementation steps for updating the Activity Design workflow to match the Purchase Request workflow. This is a continuation of the work started on 2025-11-22.

## What Has Been Completed ✅

### 1. Model Updates (COMPLETED)
- ✅ Updated `ActivityDesign` model with new workflow fields:
  - `original_ad_pdf` - stores original AD document
  - `awaiting_verification` - tracks verification status
  - `end_user_uploaded_at` - timestamp for signed doc upload
  - Updated `STATUS_CHOICES` to match PR workflow
  - Updated field relationships

- ✅ Created `ActivityDesignApprovedDocument` model (similar to PurchaseRequestApprovedDocument):
  - File: `apps/budgets/models.py` lines 2160-2243
  - Includes `converted_pdf` field for image-to-PDF conversion
  - Has `get_file_extension()` and `get_file_size_display()` methods

- ✅ Updated `ActivityDesignSupportingDocument` model:
  - Added `converted_pdf` field (line 2131-2137)
  - Added `get_file_extension()` method

- ✅ Created and applied migration: `0033_activitydesign_awaiting_verification_and_more.py`

### 2. End-User Views (COMPLETED)
- ✅ Created `end_user_upload_signed_ad()` view in `apps/end_user_app/views.py:7302-7396`
  - Handles signed AD document uploads
  - Converts images to PDF automatically
  - Updates AD status to "Awaiting Admin Verification"
  - Sends notifications to admins

- ✅ Created `end_user_preview_ad_documents()` view in `apps/end_user_app/views.py:7399-7431`
  - Shows original AD PDF and supporting documents
  - Print-friendly view with embedded PDF previews

### 3. End-User URLs (COMPLETED)
- ✅ Added routes in `apps/end_user_app/urls.py`:
  ```python
  path('ad/<uuid:ad_id>/upload-signed/', views.end_user_upload_signed_ad, name='end_user_upload_signed_ad'),
  path('ad/<uuid:ad_id>/preview-documents/', views.end_user_preview_ad_documents, name='end_user_preview_ad_documents'),
  ```

### 4. End-User Templates (COMPLETED)
- ✅ Created `apps/end_user_app/templates/end_user_app/preview_ad_documents.html`
  - Full preview template with embedded PDF viewers
  - Shows original AD PDF and all supporting documents
  - Includes image previews and converted PDFs
  - Print-friendly styling

---

## What Still Needs to Be Done 🔄

### 1. Update `preview_submitted_ad.html` Template
**Location:** `apps/end_user_app/templates/end_user_app/preview_submitted_ad.html`

**Required Changes:**
Add the following sections by referencing `preview_submitted_pr.html` as a template:

#### A. Add Preview & Print Button (in header section, around line 70)
Currently there's a "Download PDF" button. Add a new button next to it:

```html
<!-- Preview & Print Documents Button (Available for all statuses to verify uploads) -->
{% if ad.status == 'Pending' or ad.status == 'Partially Approved' or ad.status == 'Approved' or ad.status == 'Awaiting Admin Verification' %}
    {% if ad.original_ad_pdf or ad.supporting_documents.all %}
    <a href="{% url 'end_user_preview_ad_documents' ad_id=ad.id %}"
    class="inline-flex items-center px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-md hover:from-blue-700 hover:to-indigo-700 transition-colors font-medium shadow-md gap-2">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
        </svg>
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"></path>
        </svg>
        Preview & Print
    </a>
    {% endif %}
{% endif %}
```

#### B. Add Upload Signed Documents Section (after the download PDF section, around line 180)
Copy the entire "Upload Signed Documents Section" from `preview_submitted_pr.html` (lines 135-203) and adapt it for AD:

```html
<!-- Upload Signed Documents Section (Only for Partially Approved) -->
{% if ad.status == 'Partially Approved' %}
<div class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg shadow-sm border-2 border-blue-200 p-6">
    <div class="flex items-center mb-4">
        <div class="flex-shrink-0">
            <svg class="w-10 h-10 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
        </div>
        <div class="ml-4">
            <h2 class="text-xl font-bold text-gray-900">📄 Documents Ready for Signing</h2>
            <p class="text-sm text-gray-600 mt-1">
                Your Activity Design has been partially approved. Follow the steps below to complete the approval process.
            </p>
        </div>
    </div>

    <!-- Instructions Card -->
    <div class="bg-white border-2 border-blue-300 rounded-lg p-5 mb-4">
        <div class="flex items-start">
            <svg class="w-6 h-6 text-blue-600 mt-0.5 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <div class="flex-1">
                <h4 class="text-sm font-semibold text-blue-900 mb-2">📝 Next Steps:</h4>
                <ol class="text-sm text-blue-800 space-y-2 list-decimal list-inside">
                    <li>Click <strong>"Preview & Print"</strong> button at the top to view all documents</li>
                    <li>Print the documents directly from the preview page</li>
                    <li>Bring the printed documents to the <strong>Approving Officer</strong> for signature</li>
                    <li>After getting the signature, use the form below to <strong>upload the signed documents</strong></li>
                    <li>Wait for admin verification and final approval</li>
                </ol>
            </div>
        </div>
    </div>

    <!-- Upload Form -->
    <div class="bg-white border border-blue-200 rounded-lg p-5">
        <h3 class="text-lg font-semibold text-gray-900 mb-3 flex items-center">
            <svg class="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
            </svg>
            Upload Signed Documents
        </h3>
        <form method="post" action="{% url 'end_user_upload_signed_ad' ad_id=ad.id %}" enctype="multipart/form-data" id="uploadSignedForm">
            {% csrf_token %}
            <div class="mb-4">
                <label class="block text-sm font-medium text-gray-700 mb-2">
                    Select signed documents (PDF, JPG, PNG)
                    <span class="text-red-500">*</span>
                </label>
                <input type="file" name="signed_documents" id="signed_documents" multiple accept=".pdf,.jpg,.jpeg,.png" required
                    class="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none focus:border-blue-500 p-2">
                <p class="text-xs text-gray-500 mt-1">You can select multiple files. Maximum size: 10MB per file.</p>
            </div>

            <div id="filePreview" class="mb-4 space-y-2"></div>

            <button type="submit" id="uploadBtn"
                class="w-full inline-flex justify-center items-center px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white font-semibold rounded-lg hover:from-green-700 hover:to-emerald-700 transition shadow-md">
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
                </svg>
                Upload Signed Documents
            </button>
        </form>
    </div>
</div>
{% endif %}
```

#### C. Add "Awaiting Verification" Status Card
After the upload section, add:

```html
<!-- Awaiting Verification Status Card -->
{% if ad.status == 'Awaiting Admin Verification' %}
<div class="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg shadow-sm border-2 border-indigo-200 p-6">
    <div class="flex items-center mb-4">
        <div class="flex-shrink-0">
            <svg class="w-10 h-10 text-indigo-600 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
        </div>
        <div class="ml-4">
            <h2 class="text-xl font-bold text-gray-900">⏳ Awaiting Admin Verification</h2>
            <p class="text-sm text-gray-600 mt-1">
                Your signed documents have been uploaded successfully. Admin is reviewing them now.
            </p>
        </div>
    </div>

    <div class="bg-white border border-indigo-200 rounded-lg p-5">
        <div class="flex items-start">
            <svg class="w-6 h-6 text-indigo-600 mt-0.5 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
            </svg>
            <div class="flex-1">
                <h4 class="text-sm font-semibold text-indigo-900 mb-2">What happens next?</h4>
                <ul class="text-sm text-indigo-800 space-y-1 list-disc list-inside">
                    <li>Admin will verify your uploaded signed documents</li>
                    <li>If approved, budget will be deducted from your allocation</li>
                    <li>If rejected, you'll be notified to re-upload corrected documents</li>
                </ul>
                <p class="text-xs text-indigo-600 mt-3">
                    📅 Uploaded: {{ ad.end_user_uploaded_at|date:"F d, Y g:i A" }}
                </p>
            </div>
        </div>
    </div>

    <!-- Show uploaded signed documents -->
    {% if ad.signed_approved_documents.all %}
    <div class="mt-4 bg-white border border-indigo-200 rounded-lg p-5">
        <h4 class="text-sm font-semibold text-gray-900 mb-3">Uploaded Signed Documents ({{ ad.signed_approved_documents.count }})</h4>
        <div class="space-y-2">
            {% for doc in ad.signed_approved_documents.all %}
            <div class="flex items-center justify-between p-3 bg-indigo-50 rounded-lg">
                <div class="flex items-center">
                    <svg class="w-5 h-5 text-indigo-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"></path>
                    </svg>
                    <span class="text-sm text-gray-900">{{ doc.file_name }}</span>
                </div>
                <span class="text-xs text-gray-500">{{ doc.file_size|filesizeformat }}</span>
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}
</div>
{% endif %}
```

#### D. Add JavaScript for File Preview (at the bottom of the template)
Copy the JavaScript section from `preview_submitted_pr.html` for file preview functionality.

---

### 2. Create Admin Preview AD Template
**Location:** `apps/admin_panel/templates/admin_panel/preview_ad.html`

**Action:** Copy `apps/admin_panel/templates/admin_panel/preview_pr.html` and adapt it for Activity Design.

**Key Changes Needed:**
- Replace all `pr` variables with `ad`
- Replace `pr.pr_number` with `ad.ad_number`
- Replace URL names:
  - `admin_preview_pr` → `admin_preview_ad`
  - `admin_verify_and_approve_pr` → `admin_verify_and_approve_ad`
- Update title from "Purchase Request" to "Activity Design"
- Update all field references (e.g., `pr.status` → `ad.status`)
- Update the signed documents section to use `ad.signed_approved_documents`

**Important Sections to Include:**
1. Header with AD details (number, department, status, total amount)
2. Supporting Documents section with embedded previews (lines 148-290 in PR template)
3. Signed Documents section with embedded previews (lines 163-291 in PR template)
4. Verify & Approve form section (lines 445-515 in PR template)
5. Download partially approved PDF section

---

### 3. Create Admin Verify & Approve AD View
**Location:** `apps/admin_panel/views.py`

**Action:** Copy the `admin_verify_and_approve_pr` function and adapt it for Activity Design.

**Function to Create:**
```python
@role_required('admin')
def admin_verify_and_approve_ad(request, ad_id):
    """
    Verify uploaded signed AD documents and give final approval.
    This is the final step in the new AD workflow (Phase 4b).

    Workflow:
    1. End user uploads signed documents → AD status: "Awaiting Admin Verification"
    2. Admin verifies signatures → Uses this view
    3. If approved → AD status: "Approved", budget deducted
    4. If rejected → Documents deleted, status back to "Partially Approved"
    """
    from apps.budgets.models import ActivityDesign
    from django.utils import timezone
    from decimal import Decimal

    ad = get_object_or_404(
        ActivityDesign.objects.select_related(
            'budget_allocation',
            'submitted_by'
        ).prefetch_related(
            'signed_approved_documents',
            'pre_allocations__pre_line_item'
        ),
        id=ad_id
    )

    # Can only verify ADs that are awaiting verification
    if ad.status != 'Awaiting Admin Verification':
        messages.error(request, "This Activity Design is not awaiting verification")
        return redirect('admin_preview_ad', ad_id=ad.id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'approve':
            # Verify & Approve
            comment = request.POST.get('comment', '').strip()

            # Update AD status
            ad.status = 'Approved'
            ad.awaiting_verification = False
            ad.admin_approved_by = request.user
            ad.admin_approved_at = timezone.now()
            ad.final_approved_at = timezone.now()
            if comment:
                ad.admin_notes = comment
            ad.save()

            # Deduct budget from allocations
            budget_allocation = ad.budget_allocation

            # Deduct from each PRE line item allocation
            for ad_allocation in ad.pre_allocations.all():
                pre_line_item = ad_allocation.pre_line_item
                pre_line_item.amount_used += ad_allocation.allocated_amount
                pre_line_item.save()

            # Create audit log
            from apps.budgets.models import BudgetTransactionLog
            BudgetTransactionLog.objects.create(
                budget_allocation=budget_allocation,
                transaction_type='AD_APPROVED',
                amount=ad.total_amount,
                description=f'Activity Design {ad.ad_number} approved - Budget deducted',
                performed_by=request.user,
                related_ad=ad
            )

            # Send notification to end user
            from apps.budgets.models import SystemNotification
            SystemNotification.objects.create(
                recipient=ad.submitted_by,
                title='Activity Design Approved',
                message=f'Your Activity Design {ad.ad_number} has been verified and approved! '
                        f'Budget has been deducted from your allocation.',
                content_type='ad',
                object_id=ad.id
            )

            messages.success(request, f"Activity Design {ad.ad_number} has been verified and approved! Budget deducted.")
            return redirect('admin_preview_ad', ad_id=ad.id)

        elif action == 'reject':
            # Reject verification
            reason = request.POST.get('reason', '').strip()

            if not reason:
                messages.error(request, "Please provide a reason for rejection")
                return redirect('admin_preview_ad', ad_id=ad.id)

            # Delete uploaded signed documents
            ad.signed_approved_documents.all().delete()

            # Revert status
            ad.status = 'Partially Approved'
            ad.awaiting_verification = False
            ad.end_user_uploaded_at = None
            ad.rejection_reason = reason
            ad.save()

            # Send notification to end user
            from apps.budgets.models import SystemNotification
            SystemNotification.objects.create(
                recipient=ad.submitted_by,
                title='AD Documents Rejected',
                message=f'Your signed documents for AD {ad.ad_number} were rejected. '
                        f'Reason: {reason}. Please re-upload corrected documents.',
                content_type='ad',
                object_id=ad.id
            )

            messages.warning(request, f"Verification rejected. End user will be notified to re-upload.")
            return redirect('admin_preview_ad', ad_id=ad.id)

    return redirect('admin_preview_ad', ad_id=ad.id)
```

**Find Location:** Search for `def admin_verify_and_approve_pr` and add this function right after it.

---

### 4. Create Admin Preview AD View
**Location:** `apps/admin_panel/views.py`

**Action:** Copy the `admin_preview_pr` function and adapt it.

**Function to Create:**
```python
@role_required('admin')
def admin_preview_ad(request, ad_id):
    """
    Admin preview page for Activity Design
    Shows all details, supporting documents, and signed documents
    Allows verification and approval
    """
    from apps.budgets.models import ActivityDesign

    ad = get_object_or_404(
        ActivityDesign.objects.select_related(
            'budget_allocation',
            'budget_allocation__approved_budget',
            'submitted_by',
            'admin_approved_by'
        ).prefetch_related(
            'supporting_documents',
            'signed_approved_documents',
            'pre_allocations__pre_line_item__category',
            'pre_allocations__pre_line_item__subcategory'
        ),
        id=ad_id
    )

    supporting_documents = ad.supporting_documents.all().order_by('-uploaded_at')
    signed_documents = ad.signed_approved_documents.all().order_by('-uploaded_at')
    pre_allocations = ad.pre_allocations.all()

    context = {
        'ad': ad,
        'supporting_documents': supporting_documents,
        'signed_documents': signed_documents,
        'pre_allocations': pre_allocations,
    }

    return render(request, 'admin_panel/preview_ad.html', context)
```

---

### 5. Add Admin URLs
**Location:** `apps/admin_panel/urls.py`

**Action:** Add these two URL patterns (find the PR URLs and add AD URLs after them):

```python
# Activity Design Workflow URLs (similar to PR)
path('ad/<uuid:ad_id>/preview/', views.admin_preview_ad, name='admin_preview_ad'),
path('ad/<uuid:ad_id>/verify/', views.admin_verify_and_approve_ad, name='admin_verify_and_approve_ad'),
```

---

## Testing Checklist

After implementing the above changes, test the complete workflow:

### End-User Flow:
1. ✅ Submit an Activity Design
2. ✅ Admin partially approves it (should generate PDF)
3. ✅ End user sees "Preview & Print" button on AD details page
4. ✅ End user clicks "Preview & Print" - should see embedded PDF previews
5. ✅ End user sees "Upload Signed Documents" section
6. ✅ End user uploads signed documents (PDF or images)
7. ✅ Images should auto-convert to PDF
8. ✅ AD status changes to "Awaiting Admin Verification"
9. ✅ End user sees "Awaiting Verification" status card

### Admin Flow:
1. ✅ Admin receives notification about AD awaiting verification
2. ✅ Admin opens AD preview page
3. ✅ Admin sees signed documents with embedded previews
4. ✅ Admin clicks "Verify & Approve"
5. ✅ AD status changes to "Approved"
6. ✅ Budget is deducted from PRE line items
7. ✅ End user receives approval notification

### Alternative Flow (Rejection):
1. ✅ Admin clicks "Reject" on verification page
2. ✅ Admin provides rejection reason
3. ✅ Signed documents are deleted
4. ✅ AD status reverts to "Partially Approved"
5. ✅ End user receives rejection notification
6. ✅ End user can re-upload signed documents

---

## Files Modified Summary

### Models:
- ✅ `apps/budgets/models.py` - ActivityDesign, ActivityDesignApprovedDocument, ActivityDesignSupportingDocument

### Migrations:
- ✅ `apps/budgets/migrations/0033_activitydesign_awaiting_verification_and_more.py`

### End-User Views:
- ✅ `apps/end_user_app/views.py` - Added 2 new views

### End-User URLs:
- ✅ `apps/end_user_app/urls.py` - Added 2 new routes

### End-User Templates:
- ✅ `apps/end_user_app/templates/end_user_app/preview_ad_documents.html` - NEW FILE
- 🔄 `apps/end_user_app/templates/end_user_app/preview_submitted_ad.html` - NEEDS UPDATE

### Admin Views:
- 🔄 `apps/admin_panel/views.py` - NEEDS 2 new views

### Admin URLs:
- 🔄 `apps/admin_panel/urls.py` - NEEDS 2 new routes

### Admin Templates:
- 🔄 `apps/admin_panel/templates/admin_panel/preview_ad.html` - NEEDS CREATION

---

## Additional Notes

### Document Conversion:
- The `apps/admin_panel/signed_doc_converter.py` is already created and working
- It automatically converts JPG/PNG images to PDF using Pillow
- The conversion happens during upload in the `end_user_upload_signed_ad` view

### Budget Deduction:
- When AD is approved, budget is deducted from PRE line items via `ad.pre_allocations`
- Each allocation has `pre_line_item.amount_used` which needs to be incremented
- Activity Design can have MULTIPLE PRE line items (unlike PR which has one)

### Key Differences from PR:
- AD has MULTIPLE PRE line item allocations (PR has single source)
- AD uses `ad.ad_number` (PR uses `pr.pr_number`)
- AD model doesn't have `source_line_item` field (uses `pre_allocations` relationship)
- When deducting budget, must loop through ALL `ad.pre_allocations`

---

## Prompt for Claude to Continue

When you're ready to continue, use this prompt:

```
I need to complete the Activity Design workflow implementation.

Context: We've updated the Activity Design model to match the Purchase Request workflow with new fields (awaiting_verification, end_user_uploaded_at, original_ad_pdf, etc.), created the ActivityDesignApprovedDocument model, added end-user views for uploading signed documents, and created the preview_ad_documents.html template.

Remaining tasks:
1. Update preview_submitted_ad.html to add "Preview & Print" button and "Upload Signed Documents" section (reference: preview_submitted_pr.html)
2. Create admin preview_ad.html template (copy from preview_pr.html and adapt for AD)
3. Create admin_preview_ad() view in apps/admin_panel/views.py
4. Create admin_verify_and_approve_ad() view in apps/admin_panel/views.py
5. Add admin URLs for AD preview and verify/approve

Please refer to the file: ACTIVITY_DESIGN_WORKFLOW_CONTINUATION.md for detailed implementation instructions.

Start by updating preview_submitted_ad.html.
```

---

## Reference Files for Copy/Paste

### Key Template Sections Already Completed:
- ✅ End-user AD document preview: `apps/end_user_app/templates/end_user_app/preview_ad_documents.html`

### Templates to Reference:
- For end-user updates: `apps/end_user_app/templates/end_user_app/preview_submitted_pr.html`
- For admin template: `apps/admin_panel/templates/admin_panel/preview_pr.html`

### Views to Reference:
- For admin views: Search `admin_verify_and_approve_pr` in `apps/admin_panel/views.py`

---

## End of Continuation Guide

**Last Updated:** 2025-11-22
**Status:** 60% Complete - Models and end-user views done, admin views and template updates remaining
**Next Step:** Update preview_submitted_ad.html template
