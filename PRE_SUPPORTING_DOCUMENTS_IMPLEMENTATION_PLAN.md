# PRE Supporting Documents Feature - Implementation Plan

## Executive Summary
**Issue:** Supporting documents uploaded by users are not displaying in the Documents section of the PRE Details Page (`admin_panel/pre_detail.html`).

**Root Cause:** The system is missing the `DepartmentPRESupportingDocument` model and related functionality. While other document types (PR, AD) have supporting document models, PRE documents do not.

**Impact:** Medium - Administrators cannot view supporting documents submitted with PRE requests, which may be needed for approval decisions.

**Complexity:** Low-Medium - Straightforward database model addition and template updates.

---

## Current System Analysis

### ✅ What Exists
1. **Documents Currently Displayed in PRE Detail Page:**
   - Original Excel File (`uploaded_excel_file`)
   - Partially Approved PDF (`partially_approved_pdf`)
   - Approved Document (`approved_documents`)
   - Final Approved Scan (`final_approved_scan`)

2. **Similar Supporting Document Models:**
   - `SupportingDocument` (for ApprovedBudget)
   - `PurchaseRequestSupportingDocument` (for Purchase Requests)
   - `ActivityDesignSupportingDocument` (for Activity Designs)
   - `PRDraftSupportingDocument` (for PR Drafts)
   - `ADDraftSupportingDocument` (for AD Drafts)

### ❌ What's Missing
1. **Model:** `DepartmentPRESupportingDocument` or `PRESupportingDocument`
2. **View Logic:** Fetching and passing supporting documents to template
3. **Template Section:** Display of supporting documents in the Documents section
4. **Upload Functionality:** (May or may not exist in end user app - needs verification)

---

## Implementation Plan

### Phase 1: Database Model Creation

#### Step 1.1: Create PRESupportingDocument Model
**File:** `apps/budgets/models.py`
**Location:** After line ~1417 (after PurchaseRequestSupportingDocument)

```python
class DepartmentPRESupportingDocument(models.Model):
    """Supporting documents for Department PRE submissions"""
    department_pre = models.ForeignKey(
        'DepartmentPRE',
        on_delete=models.CASCADE,
        related_name='supporting_documents',
        help_text='Link to PRE submission'
    )
    document = models.FileField(
        upload_to='pre_supporting_docs/%Y/%m/',
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'docx', 'doc', 'xlsx', 'xls', 'jpg', 'jpeg', 'png']
        )],
        help_text='Supporting document file (PDF, Word, Excel, Images)'
    )
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField(help_text='File size in bytes', editable=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='User who uploaded this document'
    )
    description = models.CharField(
        max_length=500,
        blank=True,
        help_text='Optional description of the document'
    )

    class Meta:
        db_table = 'department_pre_supporting_documents'
        ordering = ['-uploaded_at']
        verbose_name = 'PRE Supporting Document'
        verbose_name_plural = 'PRE Supporting Documents'

    def __str__(self):
        return f"{self.file_name} for PRE {str(self.department_pre.id)[:8]}"

    def get_file_extension(self):
        """Get file extension in lowercase"""
        return self.file_name.split('.')[-1].lower() if '.' in self.file_name else ''

    def get_file_size_display(self):
        """Return human-readable file size"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def save(self, *args, **kwargs):
        """Auto-calculate file size before saving"""
        if self.document and not self.file_size:
            self.file_size = self.document.size
        super().save(*args, **kwargs)
```

#### Step 1.2: Create and Run Migration
```bash
python manage.py makemigrations budgets
python manage.py migrate budgets
```

**Expected Output:**
```
Migrations for 'budgets':
  apps/budgets/migrations/0XXX_departmentpresupportingdocument.py
    - Create model DepartmentPRESupportingDocument
```

---

### Phase 2: Admin Panel View Update

#### Step 2.1: Update admin_pre_detail View
**File:** `apps/admin_panel/views.py`
**Function:** `admin_pre_detail` (Line 3530)

**Changes:**
1. Add prefetch for supporting documents in queryset
2. Pass supporting documents to context

```python
def admin_pre_detail(request, pre_id):
    """
    Admin view to see detailed PRE information with budget tracking breakdown
    """
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')

    pre = get_object_or_404(
        NewDepartmentPRE.objects.select_related(
            'submitted_by',
            'budget_allocation__approved_budget'
        ).prefetch_related(
            'line_items__category',
            'line_items__subcategory',
            'receipts',
            'supporting_documents'  # 🔥 NEW: Prefetch supporting documents
        ),
        id=pre_id
    )

    # Get approval history
    approval_history = RequestApproval.objects.filter(
        content_type='pre',
        object_id=pre.id
    ).select_related('approved_by').order_by('-approved_at')

    # Calculate totals by category
    from django.db.models import Sum
    category_totals = pre.line_items.values(
        'category__name'
    ).annotate(
        total=Sum('q1_amount') + Sum('q2_amount') + Sum('q3_amount') + Sum('q4_amount')
    ).order_by('category__sort_order')

    # Calculate budget tracking breakdown for each line item
    line_items_with_breakdown = []
    for item in pre.line_items.all():
        item_data = {
            'item': item,
            'quarters': []
        }

        for quarter in ['Q1', 'Q2', 'Q3', 'Q4']:
            breakdown = item.get_quarter_breakdown(quarter)
            item_data['quarters'].append(breakdown)

        line_items_with_breakdown.append(item_data)

    # 🔥 NEW: Get supporting documents
    supporting_documents = pre.supporting_documents.all().order_by('-uploaded_at')

    context = {
        'pre': pre,
        'approval_history': approval_history,
        'category_totals': category_totals,
        'line_items_with_breakdown': line_items_with_breakdown,
        'supporting_documents': supporting_documents,  # 🔥 NEW
    }

    return render(request, 'admin_panel/pre_detail.html', context)
```

---

### Phase 3: Template Update

#### Step 3.1: Update pre_detail.html Documents Section
**File:** `apps/admin_panel/templates/admin_panel/pre_detail.html`
**Section:** Documents Section (Lines 153-244)

**Add this after line 238 (after final_approved_scan section):**

```django
<!-- Supporting Documents (NEW) -->
{% if supporting_documents %}
<div class="mt-4 border-t pt-4">
  <h3 class="text-lg font-semibold text-gray-800 mb-3 flex items-center">
    <svg class="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path>
    </svg>
    Supporting Documents ({{ supporting_documents.count }})
  </h3>
  <div class="space-y-2">
    {% for doc in supporting_documents %}
    <div class="flex items-center justify-between p-3 bg-gray-50 rounded border hover:bg-gray-100 transition">
      <div class="flex items-center flex-1">
        <!-- File Icon based on extension -->
        {% with ext=doc.get_file_extension %}
          {% if ext == 'pdf' %}
            <svg class="w-8 h-8 text-red-600 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path>
            </svg>
          {% elif ext == 'docx' or ext == 'doc' %}
            <svg class="w-8 h-8 text-blue-600 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
            </svg>
          {% elif ext == 'xlsx' or ext == 'xls' %}
            <svg class="w-8 h-8 text-green-600 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
            </svg>
          {% elif ext == 'jpg' or ext == 'jpeg' or ext == 'png' %}
            <svg class="w-8 h-8 text-purple-600 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
            </svg>
          {% else %}
            <svg class="w-8 h-8 text-gray-600 mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path>
            </svg>
          {% endif %}
        {% endwith %}

        <div class="flex-1 min-w-0">
          <p class="font-medium text-gray-800 truncate">{{ doc.file_name }}</p>
          <div class="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-gray-500 mt-1">
            <span class="flex items-center">
              <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"></path>
              </svg>
              {{ doc.uploaded_at|date:"M d, Y g:i A" }}
            </span>
            <span class="flex items-center">
              <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4 4a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V8a2 2 0 00-2-2h-5L9 4H4zm7 5a1 1 0 10-2 0v1H8a1 1 0 100 2h1v1a1 1 0 102 0v-1h1a1 1 0 100-2h-1V9z" clip-rule="evenodd"></path>
              </svg>
              {{ doc.get_file_size_display }}
            </span>
            {% if doc.uploaded_by %}
            <span class="flex items-center">
              <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"></path>
              </svg>
              {{ doc.uploaded_by.get_full_name|default:doc.uploaded_by.username }}
            </span>
            {% endif %}
          </div>
          {% if doc.description %}
          <p class="text-xs text-gray-600 italic mt-1">{{ doc.description }}</p>
          {% endif %}
        </div>
      </div>

      <a href="{{ doc.document.url }}" target="_blank" download="{{ doc.file_name }}"
        class="ml-3 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition text-sm flex-shrink-0">
        Download
      </a>
    </div>
    {% endfor %}
  </div>
</div>
{% endif %}
```

**Update the "No documents available" condition (line 240):**
```django
{% if not pre.uploaded_excel_file and not pre.partially_approved_pdf and not pre.approved_documents and not pre.final_approved_scan and not supporting_documents %}
<p class="text-gray-500 italic text-center py-4">No documents available</p>
{% endif %}
```

---

### Phase 4: Admin Registration (Optional but Recommended)

#### Step 4.1: Register Model in Admin Panel
**File:** `apps/budgets/admin.py`

```python
from .models import DepartmentPRESupportingDocument

@admin.register(DepartmentPRESupportingDocument)
class DepartmentPRESupportingDocumentAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'department_pre', 'uploaded_by', 'file_size', 'uploaded_at']
    list_filter = ['uploaded_at', 'uploaded_by']
    search_fields = ['file_name', 'description', 'department_pre__id']
    readonly_fields = ['uploaded_at', 'file_size']
    date_hierarchy = 'uploaded_at'
```

---

## Testing Plan

### Test Case 1: Model Creation ✅
- [ ] Migration runs successfully
- [ ] No migration conflicts
- [ ] Database table created correctly
- [ ] Model appears in Django admin

### Test Case 2: View Integration ✅
- [ ] View fetches supporting documents without errors
- [ ] Supporting documents are properly prefetched (check query count)
- [ ] Context contains `supporting_documents` key

### Test Case 3: Template Display ✅
- [ ] Documents section displays all document types
- [ ] Supporting documents show correct file icons
- [ ] Download links work correctly
- [ ] File metadata displays correctly (name, size, date, uploader)
- [ ] "No documents available" shows only when truly empty

### Test Case 4: Edge Cases ✅
- [ ] PRE with no supporting documents displays properly
- [ ] PRE with multiple supporting documents (5+) displays properly
- [ ] Large file names are truncated properly
- [ ] Special characters in file names handled correctly
- [ ] Missing `uploaded_by` doesn't crash the page

### Test Case 5: Backward Compatibility ✅
- [ ] Existing PREs without supporting documents still display correctly
- [ ] Other document types (Excel, PDF, etc.) still work
- [ ] No breakage in PRE list page
- [ ] No breakage in PRE approval workflow

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Migration conflicts | Low | High | Review existing migrations before creating new one |
| Template rendering errors | Low | Medium | Test with various PRE states (with/without docs) |
| Performance degradation | Low | Medium | Use `prefetch_related` for supporting documents |
| File upload issues | Medium | High | Verify upload functionality exists in end user app |
| Broken existing features | Low | High | Comprehensive testing of all PRE workflows |

---

## Rollback Plan

If issues occur after deployment:

1. **Immediate:** Comment out template changes
   ```django
   {% comment %}
   <!-- Supporting Documents section -->
   {% endcomment %}
   ```

2. **Short-term:** Revert view changes
   - Remove `supporting_documents` from prefetch
   - Remove from context

3. **Long-term:** Rollback migration (if necessary)
   ```bash
   python manage.py migrate budgets <previous_migration_number>
   ```

---

## Dependencies & Assumptions

### Dependencies
- ✅ Django ORM
- ✅ Existing `DepartmentPRE` model
- ✅ Existing template structure
- ✅ File storage configuration

### Assumptions
1. **Upload Functionality:** Assumes end user app has (or will have) functionality to upload supporting documents when creating PREs
2. **File Storage:** Assumes adequate storage space for supporting documents
3. **Permissions:** Assumes current user permissions don't need modification
4. **File Types:** Supports PDF, Word, Excel, and images as per validator

---

## Future Enhancements (Out of Scope)

1. **Inline Document Preview:** Show PDF/image previews without downloading
2. **Bulk Download:** Allow downloading all supporting documents as ZIP
3. **Document Versioning:** Track multiple versions of the same document
4. **Document Categories:** Categorize documents (Budget Justification, Approval Memo, etc.)
5. **File Size Limits:** Implement max file size validation
6. **Virus Scanning:** Add antivirus scanning for uploaded files

---

## Implementation Checklist

### Pre-Implementation
- [x] Analyze current code structure
- [x] Review similar implementations (PR, AD supporting docs)
- [x] Create detailed implementation plan
- [ ] Get stakeholder approval

### Implementation
- [ ] Create `DepartmentPRESupportingDocument` model
- [ ] Create and run migration
- [ ] Update `admin_pre_detail` view
- [ ] Update `pre_detail.html` template
- [ ] Register model in admin panel
- [ ] Test all scenarios

### Post-Implementation
- [ ] Code review
- [ ] QA testing
- [ ] Documentation update
- [ ] Deployment to staging
- [ ] Production deployment
- [ ] Monitor for issues

---

## Estimated Effort

| Phase | Estimated Time |
|-------|----------------|
| Model Creation | 30 minutes |
| Migration | 10 minutes |
| View Update | 20 minutes |
| Template Update | 45 minutes |
| Testing | 60 minutes |
| Documentation | 30 minutes |
| **TOTAL** | **~3 hours** |

---

## Conclusion

This implementation plan provides a comprehensive approach to adding supporting documents display functionality to the PRE Details page in the admin panel. The solution:

- ✅ Follows existing code patterns
- ✅ Maintains backward compatibility
- ✅ Includes comprehensive testing
- ✅ Has clear rollback procedures
- ✅ Low risk, medium effort

**Recommendation:** Proceed with implementation. The feature is well-scoped and follows established patterns in the codebase.

---

## Notes

- **Coordination Required:** If end user app doesn't have upload functionality for PRE supporting documents, that needs to be implemented separately
- **File Cleanup:** Consider implementing a cleanup job for orphaned files if PREs are deleted
- **Access Control:** Verify that only authorized users can download supporting documents

**Plan Created:** 2025-11-13
**Plan Version:** 1.0
**Status:** Ready for Implementation
