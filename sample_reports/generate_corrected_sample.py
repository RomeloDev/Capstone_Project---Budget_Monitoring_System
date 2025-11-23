"""
Generate sample budget report with EXACT BISU Header from Departmental-PRE.xlsx

This creates a report with the header format copied exactly from Row 1 of Departmental-PRE.xlsx
"""

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime
import os


def copy_bisu_header_from_template(ws, start_row=1):
    """
    Copy the exact BISU header from Departmental-PRE.xlsx Row 1

    Returns: Next available row after header
    """
    # The header text exactly as it appears in Departmental-PRE.xlsx cell A1
    # All 5 lines in a single cell with line breaks
    header_text = """Republic of the Philippines
BOHOL ISLAND STATE UNIVERSITY
Magsija, Balilihan, 6342, Bohol, Philippines
Office of the Administration and Finance
Balance I Integrity I Stewardship I Uprightness"""

    # Merge cells A1:I1 (same as template)
    ws.merge_cells(f'A{start_row}:I{start_row}')

    # Get cell A1
    cell = ws[f'A{start_row}']

    # Set the value
    cell.value = header_text

    # Apply exact formatting from Departmental-PRE.xlsx
    cell.font = Font(
        name='Arial',
        size=11,
        bold=False
    )

    # Center vertical alignment, wrap text for multiline
    cell.alignment = Alignment(
        horizontal='center',
        vertical='center',
        wrap_text=True
    )

    # Set row height to match template (84.75)
    ws.row_dimensions[start_row].height = 84.75

    # Add medium bottom border (as in template)
    cell.border = Border(
        bottom=Side(style='medium', color='FF000000')
    )

    return start_row + 1


def generate_corrected_excel_report():
    """Generate Excel budget report with EXACT BISU header from template"""

    wb = Workbook()
    ws = wb.active
    ws.title = "Budget Summary Report"

    # Add EXACT BISU header from template
    current_row = copy_bisu_header_from_template(ws, start_row=1)

    # Blank row after header
    current_row += 1

    # Report Title
    ws.merge_cells(f'A{current_row}:I{current_row}')
    cell = ws[f'A{current_row}']
    cell.value = "BUDGET SUMMARY REPORT - FISCAL YEAR 2025"
    cell.font = Font(name='Arial', size=16, bold=True, color='1F4E78')
    cell.alignment = Alignment(horizontal='center', vertical='center')
    cell.fill = PatternFill(start_color='E7E6E6', end_color='E7E6E6', fill_type='solid')
    ws.row_dimensions[current_row].height = 25
    current_row += 1

    # Report metadata
    ws.merge_cells(f'A{current_row}:I{current_row}')
    cell = ws[f'A{current_row}']
    cell.value = f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
    cell.font = Font(name='Arial', size=10, bold=False, italic=True)
    cell.alignment = Alignment(horizontal='center', vertical='center')
    current_row += 1

    # Blank row
    current_row += 1

    # Section: Budget Allocation Summary
    ws.merge_cells(f'A{current_row}:I{current_row}')
    cell = ws[f'A{current_row}']
    cell.value = "BUDGET ALLOCATION SUMMARY"
    cell.font = Font(name='Arial', size=12, bold=True, color='FFFFFF')
    cell.alignment = Alignment(horizontal='center', vertical='center')
    cell.fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    current_row += 1

    # Headers for summary
    headers = ['Description', 'Amount (₱)']
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=current_row, column=col_num)
        cell.value = header
        cell.font = Font(name='Arial', size=11, bold=True, color='FFFFFF')
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.fill = PatternFill(start_color='5B9BD5', end_color='5B9BD5', fill_type='solid')
    current_row += 1

    # Sample summary data
    summary_data = [
        ['Total Allocated Budget', 500000.00],
        ['Total Budget Used', 287500.00],
        ['Remaining Balance', 212500.00],
        ['Budget Utilization', '57.50%'],
    ]

    for row_data in summary_data:
        ws.cell(row=current_row, column=1).value = row_data[0]
        ws.cell(row=current_row, column=1).font = Font(name='Arial', size=10)

        cell = ws.cell(row=current_row, column=2)
        if isinstance(row_data[1], str):
            cell.value = row_data[1]
            cell.font = Font(name='Arial', size=10, bold=True, color='1F4E78')
            cell.alignment = Alignment(horizontal='right')
        else:
            cell.value = row_data[1]
            cell.number_format = '₱#,##0.00'
            cell.font = Font(name='Arial', size=10, bold=True if row_data[0] == 'Remaining Balance' else False)
            cell.alignment = Alignment(horizontal='right')

        current_row += 1

    current_row += 2  # Blank rows

    # Section: Detailed Transactions
    ws.merge_cells(f'A{current_row}:I{current_row}')
    cell = ws[f'A{current_row}']
    cell.value = "TRANSACTION DETAILS"
    cell.font = Font(name='Arial', size=12, bold=True, color='FFFFFF')
    cell.alignment = Alignment(horizontal='center', vertical='center')
    cell.fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    current_row += 1

    # Transaction headers
    transaction_headers = ['Date', 'Type', 'Document #', 'Description', 'Quarter', 'Amount (₱)', 'Status']
    for col_num, header in enumerate(transaction_headers, 1):
        cell = ws.cell(row=current_row, column=col_num)
        cell.value = header
        cell.font = Font(name='Arial', size=11, bold=True, color='FFFFFF')
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.fill = PatternFill(start_color='5B9BD5', end_color='5B9BD5', fill_type='solid')

        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        cell.border = thin_border
    current_row += 1

    # Sample transaction data
    transactions = [
        ['2025-01-15', 'PRE', 'PRE-2025-001', 'Office Supplies Budget Allocation', 'Q1', 50000.00, 'Approved'],
        ['2025-02-10', 'PR', 'PR-2025-045', 'Purchase of Printer and Toner', 'Q1', 25000.00, 'Approved'],
        ['2025-02-20', 'AD', 'AD-2025-012', 'Faculty Development Workshop', 'Q1', 75000.00, 'Approved'],
        ['2025-03-05', 'PR', 'PR-2025-078', 'Laboratory Equipment', 'Q1', 125000.00, 'Approved'],
        ['2025-03-15', 'AD', 'AD-2025-023', 'Student Leadership Training', 'Q2', 12500.00, 'Pending'],
    ]

    for row_data in transactions:
        for col_num, value in enumerate(row_data, 1):
            cell = ws.cell(row=current_row, column=col_num)

            if col_num == 6:  # Amount column
                cell.value = value
                cell.number_format = '₱#,##0.00'
                cell.alignment = Alignment(horizontal='right')
            else:
                cell.value = value
                cell.alignment = Alignment(horizontal='center' if col_num in [1, 2, 5, 7] else 'left')

            cell.font = Font(name='Arial', size=10)

            # Status color coding
            if col_num == 7:
                if value == 'Approved':
                    cell.font = Font(name='Arial', size=10, bold=True, color='008000')
                elif value == 'Pending':
                    cell.font = Font(name='Arial', size=10, bold=True, color='FF8C00')
                elif value == 'Rejected':
                    cell.font = Font(name='Arial', size=10, bold=True, color='FF0000')

            thin_border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            cell.border = thin_border

        current_row += 1

    # Column widths
    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 8
    ws.column_dimensions['C'].width = 15
    ws.column_dimensions['D'].width = 35
    ws.column_dimensions['E'].width = 10
    ws.column_dimensions['F'].width = 15
    ws.column_dimensions['G'].width = 12

    # Save the workbook
    file_path = os.path.join(os.path.dirname(__file__), 'CORRECTED_Budget_Report_BISU_Header.xlsx')
    wb.save(file_path)

    return file_path


if __name__ == '__main__':
    print("="*70)
    print("CORRECTED - BISU Budget Report with Exact Template Header")
    print("="*70)
    print("\nThis version copies Row 1 EXACTLY from Departmental-PRE.xlsx:")
    print("  - All 5 lines in single merged cell (A1:I1)")
    print("  - Exact row height (84.75)")
    print("  - Center-aligned with text wrapping")
    print("  - Medium bottom border")
    print("  - Arial 11pt font")
    print("-"*70)

    print("\nGenerating corrected Excel report...")
    try:
        excel_path = generate_corrected_excel_report()
        print(f"[OK] Corrected Excel report created: {excel_path}")
        print("\nThe BISU header now matches Departmental-PRE.xlsx Row 1 exactly!")
    except Exception as e:
        print(f"[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*70)
