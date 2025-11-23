# Sample Reports with BISU Header Format

This directory contains **sample budget reports** demonstrating the proposed BISU header format for client review.

## Generated Files

### 📊 Excel Report
**File:** `SAMPLE_Budget_Report_with_BISU_Header.xlsx`

**Features:**
- ✅ Official BISU header matching Departmental-PRE.xlsx format
- ✅ Professional formatting with proper fonts and colors
- ✅ Budget allocation summary section
- ✅ Transaction details with color-coded status
- ✅ Currency formatting (₱#,##0.00)
- ✅ Print-ready layout

**Header Format:**
```
Republic of the Philippines
BOHOL ISLAND STATE UNIVERSITY
Magsija, Balilihan, 6342, Bohol, Philippines
Office of the Administration and Finance
Balance I Integrity I Stewardship I Uprightness
```

---

### 📄 PDF Report
**File:** `SAMPLE_Budget_Report_with_BISU_Header.pdf`

**Features:**
- ✅ Official BISU letterhead
- ✅ Professional table formatting
- ✅ Budget summary with styled tables
- ✅ Transaction listing with color-coded rows
- ✅ Proper spacing and margins
- ✅ Print-ready for official documents

**Styling:**
- Blue headers (#4472C4, #5B9BD5)
- Professional fonts (Helvetica)
- Proper alignment and borders
- Footer with system attribution

---

## BISU Header Components

Both reports include the complete BISU header with:

1. **Line 1:** "Republic of the Philippines" (centered, regular)
2. **Line 2:** "BOHOL ISLAND STATE UNIVERSITY" (centered, bold, large)
3. **Line 3:** "Magsija, Balilihan, 6342, Bohol, Philippines" (centered, regular)
4. **Line 4:** "Office of the Administration and Finance" (centered, bold)
5. **Line 5:** "Balance I Integrity I Stewardship I Uprightness" (centered, italic)

---

## Sample Data Included

### Budget Summary
- Total Allocated: ₱500,000.00
- Total Used: ₱287,500.00
- Remaining: ₱212,500.00
- Utilization: 57.50%

### Sample Transactions
- PRE approval (₱50,000)
- Purchase requests (₱25,000 - ₱125,000)
- Activity designs (₱12,500 - ₱75,000)
- Various quarters (Q1, Q2)
- Different statuses (Approved, Pending)

---

## How to Regenerate

If you need to regenerate the sample reports:

```bash
cd sample_reports
python generate_sample_reports.py
```

The script will create both Excel and PDF versions with the BISU header.

---

## Next Steps

### ✅ For Client Review
1. Open both files to verify formatting
2. Check that BISU header matches Departmental-PRE.xlsx
3. Verify professional appearance meets requirements
4. Confirm print quality (try printing or save as PDF from browser)

### 📋 If Approved
Once the client approves these sample formats, we will:

1. **Integrate into System**
   - Add BISU header to all budget report exports (Excel, PDF)
   - Create report preview functionality
   - Update report generation views

2. **Add Preview Feature**
   - HTML preview page with print-to-PDF capability
   - Similar to the Activity Design document preview
   - Browser-based PDF generation

3. **Testing**
   - Test all report types with BISU header
   - Verify on different devices/browsers
   - Validate print output quality

---

## Technical Details

### Excel Generation
- Uses `openpyxl` library
- Merged cells for header (A1:I1, etc.)
- Custom fonts and colors
- Auto-column sizing

### PDF Generation
- Uses `reportlab` library
- ReportLab Paragraphs for header
- Professional table styling
- Proper margins and spacing

### Styling Consistency
Both formats use:
- Same BISU header text and layout
- Similar color schemes
- Professional fonts
- Print-optimized formatting

---

## Files in This Directory

```
sample_reports/
├── README.md (this file)
├── generate_sample_reports.py (generator script)
├── SAMPLE_Budget_Report_with_BISU_Header.xlsx (Excel output)
└── SAMPLE_Budget_Report_with_BISU_Header.pdf (PDF output)
```

---

## Questions or Modifications?

If the client requests changes to:
- Header formatting
- Colors or fonts
- Layout or spacing
- Additional sections

Simply modify `generate_sample_reports.py` and regenerate the samples.

---

**Generated:** November 23, 2025
**Purpose:** Client review and approval of BISU header format
**Status:** Ready for presentation
