# Revised Implementation Plan - BISU Header for Budget Reports

## Overview

Based on client feedback, we will use the **PERFECT_Budget_Report_BISU_Header.xlsx** approach as the foundation. This version has the best overall layout and structure.

---

## ✅ What Works Well (PERFECT version)

1. **Text is centered** - Good readability
2. **Logos are positioned** - Left and right sides
3. **Row height is correct** - 84.75 matches template
4. **Column widths match** - A through I
5. **Medium bottom border** - Professional appearance
6. **Sample data tables** - Well formatted and clear

---

## 🔧 Small Tweaks Needed

Based on comparing PERFECT version with Departmental-PRE.xlsx template:

### 1. Logo Positioning Fine-tuning
- **Current:** Logos are placed but may need position adjustments
- **Need:** Fine-tune the exact pixel offsets to match template positions
- **Solution:** Use anchor cell positions + pixel offsets

### 2. Text Formatting Enhancement
While the current single-font approach works, we can optionally enhance with:
- Line 2 "BOHOL ISLAND STATE UNIVERSITY" → Slightly larger/bolder
- Line 5 "Balance | Integrity..." → Italic formatting

**Decision:** Keep simple for now, can enhance later if client requests

### 3. Logo Sizing Optimization
- **Current:** 100x100 and 85x85 pixels
- **May need:** Slight adjustments to match template visual appearance
- **Solution:** Test with 90x90, 95x95, 80x80 variations

---

## 📋 Revised Implementation Strategy

### Phase 1: Create Reusable BISU Header Module ✨
**File:** `apps/end_user_app/utils/bisu_header.py` (NEW)

**Purpose:** Centralized BISU header generation for all export formats

```python
def add_bisu_header_to_excel(worksheet, start_row=1):
    """
    Add BISU header to Excel worksheet using PERFECT approach

    Returns: Next available row after header
    """
    # 1. Merge cells A1:I1
    # 2. Add 5-line text (centered, wrapped)
    # 3. Set row height to 84.75
    # 4. Add medium bottom border
    # 5. Copy column widths from template
    # 6. Add 3 logos with proper positioning
    # 7. Return next row (2)
```

**Key Features:**
- Uses extracted logo files (logo_1.png, logo_2.png, logo_3.png)
- Exact measurements from template
- Works with any worksheet
- Configurable logo paths

---

### Phase 2: Integrate into Excel Export Functions 📊
**Files to Modify:**
- `apps/end_user_app/views.py` - `export_budget_excel()` function

**Changes:**
```python
from apps.end_user_app.utils.bisu_header import add_bisu_header_to_excel

def export_budget_excel(request):
    # ... existing code ...

    wb = Workbook()
    ws = wb.active

    # ADD BISU HEADER - NEW CODE
    current_row = add_bisu_header_to_excel(ws, start_row=1)
    current_row += 1  # Blank row after header

    # Add report title at current_row
    # ... rest of existing code adjusted for row offset ...
```

**Impact:**
- All Excel exports automatically get BISU header
- No changes to data logic
- Just row number offsets adjustment

---

### Phase 3: Copy Logo Files to Project 📁

**Create Directory:**
```
apps/end_user_app/static/logos/
├── bisu_seal.png (logo_1.png)
├── bagong_pilipinas.png (logo_2.png)
└── iso_cert.png (logo_3.png)
```

**Why:**
- Make logos accessible to all modules
- Production-ready location
- Easy to update if logos change

---

### Phase 4: Create Report Preview Feature 👁️
**New Files:**
- `apps/end_user_app/templates/end_user_app/preview_budget_report.html`
- `apps/end_user_app/views.py` - `preview_budget_report()` function (NEW)

**Preview Flow:**
```
User clicks "Preview Report"
    ↓
Opens preview_budget_report view
    ↓
Renders HTML with:
    - BISU header (HTML/CSS version)
    - Report data in tables
    - Print button (browser print dialog)
    - Download buttons (Excel, PDF, CSV)
    ↓
User can print to PDF or download
```

**HTML Preview Template Structure:**
```html
<!-- BISU Header Section -->
<div class="bisu-header">
    <img src="{% static 'logos/bisu_seal.png' %}" class="logo-left">
    <div class="header-text">
        <div>Republic of the Philippines</div>
        <div class="university">BOHOL ISLAND STATE UNIVERSITY</div>
        <div>Magsija, Balilihan, 6342, Bohol, Philippines</div>
        <div>Office of the Administration and Finance</div>
        <div class="values">Balance I Integrity I Stewardship I Uprightness</div>
    </div>
    <img src="{% static 'logos/iso_cert.png' %}" class="logo-right-1">
    <img src="{% static 'logos/bagong_pilipinas.png' %}" class="logo-right-2">
</div>

<!-- Report Content -->
<div class="report-content">
    <!-- Data tables here -->
</div>

<!-- Print CSS -->
<style>
@media print {
    .no-print { display: none; }
    .bisu-header { page-break-after: avoid; }
    /* ... print styles ... */
}
</style>
```

---

### Phase 5: Update Report UI 🎨
**File:** `apps/end_user_app/templates/end_user_app/budget_reports.html`

**Changes:**
```html
<!-- Current buttons -->
<button onclick="exportExcel()">Export to Excel</button>
<button onclick="exportPDF()">Export to PDF</button>
<button onclick="exportCSV()">Export to CSV</button>

<!-- ADD NEW BUTTON -->
<button onclick="previewReport()" class="btn-primary">
    <i class="icon-eye"></i> Preview Report
</button>
```

**JavaScript:**
```javascript
function previewReport() {
    const reportType = document.getElementById('report_type').value;
    const year = document.getElementById('year_filter').value;
    // ... other filters ...

    const url = `/budget/preview/?type=${reportType}&year=${year}...`;
    window.open(url, '_blank');
}
```

---

## 📊 Detailed Implementation Steps

### Step 1: Setup Logo Files (15 minutes)
1. Copy logo_1.png, logo_2.png, logo_3.png from sample_reports/
2. Rename appropriately (bisu_seal.png, etc.)
3. Place in `apps/end_user_app/static/logos/`
4. Verify files load correctly

### Step 2: Create BISU Header Module (1 hour)
**File:** `apps/end_user_app/utils/bisu_header.py`

```python
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.drawing.image import Image
import os
from django.conf import settings

def add_bisu_header_to_excel(ws, start_row=1):
    """Add BISU header using PERFECT approach"""

    # Header text
    header_text = """Republic of the Philippines
BOHOL ISLAND STATE UNIVERSITY
Magsija, Balilihan, 6342, Bohol, Philippines
Office of the Administration and Finance
Balance I Integrity I Stewardship I Uprightness"""

    # Merge cells
    ws.merge_cells(f'A{start_row}:I{start_row}')

    # Set value and formatting
    cell = ws[f'A{start_row}']
    cell.value = header_text
    cell.font = Font(name='Arial', size=11)
    cell.alignment = Alignment(
        horizontal='center',
        vertical='center',
        wrap_text=True
    )

    # Border
    border = Border(bottom=Side(style='medium', color='FF000000'))
    for col in range(1, 10):
        ws.cell(start_row, col).border = border

    # Row height
    ws.row_dimensions[start_row].height = 84.75

    # Column widths (from template)
    widths = {
        'A': 13.14, 'B': 8.43, 'C': 10.57, 'D': 10.71,
        'E': 10.71, 'F': 10.71, 'G': 10.71, 'H': 13.71, 'I': 10.71
    }
    for col, width in widths.items():
        ws.column_dimensions[col].width = width

    # Add logos
    logo_path = os.path.join(settings.BASE_DIR, 'apps', 'end_user_app', 'static', 'logos')

    # Left logo
    img1 = Image(os.path.join(logo_path, 'bisu_seal.png'))
    img1.width = 90
    img1.height = 90
    ws.add_image(img1, 'A1')

    # Right logos
    img2 = Image(os.path.join(logo_path, 'bagong_pilipinas.png'))
    img2.width = 90
    img2.height = 90
    ws.add_image(img2, 'I1')

    img3 = Image(os.path.join(logo_path, 'iso_cert.png'))
    img3.width = 80
    img3.height = 80
    ws.add_image(img3, 'H1')

    return start_row + 1
```

### Step 3: Modify export_budget_excel (1 hour)
**Location:** Line ~5403 in `apps/end_user_app/views.py`

**Current code:**
```python
wb = Workbook()
ws = wb.active
ws.title = "Budget Summary Report"

# Immediately starts adding data at row 1
current_row = 1
```

**New code:**
```python
from apps.end_user_app.utils.bisu_header import add_bisu_header_to_excel

wb = Workbook()
ws = wb.active
ws.title = "Budget Summary Report"

# ADD BISU HEADER FIRST
current_row = add_bisu_header_to_excel(ws, start_row=1)

# Blank row after header
current_row += 1

# Now add report title at current_row (will be row 3)
ws.merge_cells(f'A{current_row}:I{current_row}')
# ... rest of existing code with adjusted row numbers ...
```

**Testing:**
- Generate all 5 report types
- Verify header appears correctly
- Check data doesn't overlap
- Test with different filters

### Step 4: Create Preview View (2 hours)
**New function in views.py:**

```python
def preview_budget_report(request):
    """
    Preview budget report in HTML format with BISU header
    Similar to preview_ad_documents but for budget reports
    """
    from apps.end_user_app.utils.report_helpers import get_budget_data

    # Get parameters
    report_type = request.GET.get('type', 'summary')
    year_filter = request.GET.get('year', 'all')

    # Get data using existing helpers
    data = get_budget_data(request.user, year_filter)

    context = {
        'report_type': report_type,
        'year': year_filter,
        'data': data,
        # Pass export URLs for download buttons
        'excel_url': f'/budget/export/excel/?type={report_type}&year={year_filter}',
        'pdf_url': f'/budget/export/pdf/?type={report_type}&year={year_filter}',
        'csv_url': f'/budget/export/csv/?type={report_type}&year={year_filter}',
    }

    return render(request, 'end_user_app/preview_budget_report.html', context)
```

### Step 5: Create Preview Template (2 hours)
**File:** `apps/end_user_app/templates/end_user_app/preview_budget_report.html`

Key sections:
- BISU header with logos (using static files)
- Report title and metadata
- Data tables
- Print button (calls window.print())
- Download buttons
- Print CSS for PDF generation

### Step 6: Add Preview Route (5 minutes)
**File:** `apps/end_user_app/urls.py`

```python
path('budget/preview/', views.preview_budget_report, name='preview_budget_report'),
```

### Step 7: Update Budget Reports Page (30 minutes)
**File:** `apps/end_user_app/templates/end_user_app/budget_reports.html`

- Add "Preview Report" button
- Add click handler
- Style button to match existing UI

---

## 🧪 Testing Checklist

### Excel Export Testing
- [ ] Summary report has BISU header
- [ ] PRE Details report has BISU header
- [ ] Category report has BISU header
- [ ] Quarterly report has BISU header
- [ ] Transaction report has BISU header
- [ ] All logos display correctly
- [ ] Text is readable and centered
- [ ] Row height looks good
- [ ] Column widths appropriate
- [ ] Data starts after header
- [ ] No overlap between header and data
- [ ] Border appears correctly

### Preview Testing
- [ ] Preview page loads
- [ ] BISU header displays correctly
- [ ] Logos load from static files
- [ ] Data tables render properly
- [ ] Print button works
- [ ] Print preview shows header
- [ ] Download buttons work
- [ ] Excel download has header
- [ ] PDF download works
- [ ] Back button returns to reports page

### Cross-Browser Testing
- [ ] Chrome - Preview and print
- [ ] Edge - Preview and print
- [ ] Firefox - Preview and print

### Data Accuracy
- [ ] Preview data matches Excel export
- [ ] All filters work correctly
- [ ] Year filter applies properly
- [ ] Report types generate correctly

---

## 📈 Implementation Timeline

| Phase | Task | Time | Total |
|-------|------|------|-------|
| **Phase 1** | Setup logos | 15 min | 15 min |
| | Create BISU header module | 1 hr | 1h 15m |
| **Phase 2** | Modify export_budget_excel | 1 hr | 2h 15m |
| | Test all report types | 30 min | 2h 45m |
| **Phase 3** | Create preview view | 2 hrs | 4h 45m |
| | Create preview template | 2 hrs | 6h 45m |
| | Add preview route | 5 min | 6h 50m |
| **Phase 4** | Update budget reports UI | 30 min | 7h 20m |
| | Test preview functionality | 1 hr | 8h 20m |
| **Phase 5** | Final testing & refinement | 1h 40m | **10 hrs** |

**Total Time: ~10 hours (1.5 days)**

**Target Completion: Before defense next week** ✅

---

## 🎯 Success Criteria

### Must Have:
✅ All Excel exports include BISU header
✅ Header has 3 logos positioned correctly
✅ Text is centered and readable
✅ Preview page shows report before download
✅ Preview can be printed to PDF

### Nice to Have:
⭐ Rich text formatting in header (different font sizes)
⭐ PDF exports also have BISU header
⭐ Preview shows real-time filter changes

---

## 🔄 Rollback Plan

If issues occur during implementation:

1. **BISU header module isolated** - Can disable by not importing
2. **Preview is separate feature** - Can remove route if needed
3. **Excel export has fallback** - Can revert to old version
4. **No database changes** - Safe to rollback anytime

---

## 📝 Post-Implementation

After successful integration:

1. **Update documentation**
2. **Train users on preview feature**
3. **Collect client feedback**
4. **Plan enhancements** (if needed)

---

## 🚀 Next Steps

**Once you approve this revised plan:**

1. I'll copy the logo files to the proper location
2. Create the `bisu_header.py` module
3. Modify the Excel export function
4. Create preview functionality
5. Test everything thoroughly

**Ready to proceed with implementation?**

---

**Created:** November 23, 2025
**Based on:** PERFECT_Budget_Report_BISU_Header.xlsx approach
**Status:** Awaiting approval to begin implementation
**Timeline:** 10 hours (~1.5 days)
