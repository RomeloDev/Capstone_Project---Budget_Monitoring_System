# BISU Header Template Guide

## Overview

This system uses a **template-based approach** for adding BISU headers to all Excel reports. Instead of creating headers programmatically, we use a reusable template file (`BISU_Report_Template.xlsx`) that contains the exact BISU header format from the official Departmental-PRE.xlsx file.

## Benefits of Template-Based Approach

✅ **Perfect Consistency** - Headers are exact replicas of the official format
✅ **Easier Maintenance** - Update one template file instead of modifying code
✅ **Faster Performance** - Load template instead of creating headers from scratch
✅ **Reusability** - Same template used across end_user_app and admin_panel
✅ **No Logo Issues** - Logos are embedded in the template with correct positioning

## File Structure

```
bb_budget_monitoring_system/
├── excel_templates/
│   └── Departmental-PRE.xlsx          # Original official template
│
├── apps/
│   └── end_user_app/
│       ├── templates/
│       │   └── excel_templates/
│       │       └── BISU_Report_Template.xlsx  # Reusable BISU header template
│       │
│       ├── static/
│       │   └── logos/                 # Logos for HTML preview
│       │       ├── bisu_seal.png
│       │       ├── bagong_pilipinas.png
│       │       └── iso_cert.png
│       │
│       └── utils/
│           └── bisu_header.py         # Template-based header utility
│
└── create_bisu_template_from_existing.py  # Script to regenerate template
```

## How It Works

### 1. Template Creation

The `BISU_Report_Template.xlsx` contains:
- **Row 1**: Complete BISU header with all logos and text
- **Merged cells**: A1:I1 (spanning 9 columns)
- **3 Logos**:
  - Left (Column A): BISU Seal (90x90 px)
  - Right (Column I): Bagong Pilipinas logo (90x90 px)
  - Right (Column H): ISO Certification logo (80x80 px)
- **Official Text** (5 lines, centered):
  ```
  Republic of the Philippines
  BOHOL ISLAND STATE UNIVERSITY
  Magsija, Balilihan, 6342, Bohol, Philippines
  Office of the Administration and Finance
  Balance I Integrity I Stewardship I Uprightness
  ```
- **Formatting**: Arial 11pt, centered, wrapped text, medium bottom border
- **Row Height**: 84.75
- **Column Widths**: A=13.14, B=8.43, C=10.57, D-G=10.71, H=13.71, I=10.71

### 2. Template Usage in Code

The `add_bisu_header_to_excel()` function in `apps/end_user_app/utils/bisu_header.py`:

```python
from apps.end_user_app.utils.bisu_header import add_bisu_header_to_excel

# In your export function
wb = Workbook()
ws = wb.active

# Add BISU header from template
current_row = add_bisu_header_to_excel(ws, start_row=1)
current_row += 1  # Blank row after header

# Continue with your report data starting at current_row
ws[f'A{current_row}'] = 'REPORT TITLE'
# ... rest of your report
```

### 3. Where Template is Used

The template is currently used in **5 report types** in `end_user_app`:

1. **PRE Details Report** (`export_budget_excel` with `type=pre`)
2. **Summary Report** (`export_budget_excel` with `type=summary`)
3. **Category Report** (`export_budget_excel` with `type=category`)
4. **Quarterly Report** (`export_budget_excel` with `type=quarterly`)
5. **Transaction Report** (`export_budget_excel` with `type=transaction`)

## Regenerating the Template

If you need to update the template (e.g., new logo, text changes):

### Option 1: From Departmental-PRE.xlsx

1. Update `excel_templates/Departmental-PRE.xlsx` with new header
2. Run the regeneration script:

```bash
python create_bisu_template_from_existing.py
```

This will:
- Load the Departmental-PRE.xlsx file
- Extract Row 1 (header with logos)
- Create clean `BISU_Report_Template.xlsx`
- Save to `apps/end_user_app/templates/excel_templates/`

### Option 2: Manual Update

1. Open `apps/end_user_app/templates/excel_templates/BISU_Report_Template.xlsx`
2. Modify Row 1 (text, logos, formatting)
3. Save the file
4. All future reports will use the updated header

## Using Template in Admin Panel

To use this template in `admin_panel` reports:

```python
# In admin_panel/views.py (or wherever you generate Excel reports)

from apps.end_user_app.utils.bisu_header import add_bisu_header_to_excel

def some_admin_export_view(request):
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active

    # Add BISU header
    current_row = add_bisu_header_to_excel(ws, start_row=1)
    current_row += 1  # Add blank row

    # Your admin report data
    ws[f'A{current_row}'] = 'Admin Report Title'
    # ... continue building report

    # Return response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=admin_report.xlsx'
    wb.save(response)
    return response
```

## Preview Functionality

For HTML preview (before downloading Excel):

```python
from apps.end_user_app.utils.bisu_header import get_bisu_header_context

def preview_report(request):
    context = {
        'report_title': 'My Report',
        **get_bisu_header_context(),  # Adds BISU header data
    }
    return render(request, 'preview_report.html', context)
```

In template (`preview_report.html`):

```html
<!-- BISU Header -->
<div class="bisu-header">
    <img src="{% static bisu_header.logo_bisu_seal %}" alt="BISU Seal">
    <div class="header-text">
        <p>{{ bisu_header.line1 }}</p>
        <p><strong>{{ bisu_header.line2 }}</strong></p>
        <p>{{ bisu_header.line3 }}</p>
        <p>{{ bisu_header.line4 }}</p>
        <p><em>{{ bisu_header.line5 }}</em></p>
    </div>
    <img src="{% static bisu_header.logo_bagong_pilipinas %}" alt="Bagong Pilipinas">
    <img src="{% static bisu_header.logo_iso_cert %}" alt="ISO">
</div>
```

## Troubleshooting

### Template Not Found Error

```
FileNotFoundError: BISU Report Template not found at ...
```

**Solution**: Run `python create_bisu_template_from_existing.py` to create the template.

### Logos Not Showing

**Check**:
1. Template exists at `apps/end_user_app/templates/excel_templates/BISU_Report_Template.xlsx`
2. Template has 3 images embedded
3. Open template in Excel to verify logos are visible

**Fix**: Regenerate template from Departmental-PRE.xlsx

### Wrong Header Format

**Solution**:
1. Check source file: `excel_templates/Departmental-PRE.xlsx`
2. Ensure Row 1 has correct format
3. Regenerate template: `python create_bisu_template_from_existing.py`

## Best Practices

1. **Never modify the template manually** unless you're intentionally updating the official header
2. **Always use the utility function** `add_bisu_header_to_excel()` instead of copying code
3. **Keep Departmental-PRE.xlsx** as the source of truth
4. **Test after regenerating** the template to ensure logos and formatting are correct
5. **Use same template** for both end_user_app and admin_panel reports

## Summary

This template-based system ensures that **all budget reports across the entire application** have a consistent, professional BISU header that exactly matches the official Departmental-PRE.xlsx format. This approach is maintainable, reusable, and guarantees consistency across the system.

---

**Created**: November 23, 2025
**Last Updated**: November 23, 2025
**Maintained By**: Development Team
