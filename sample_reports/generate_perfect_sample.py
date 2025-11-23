"""
Generate sample budget report with PERFECT Row 1 from Departmental-PRE.xlsx
With exact logo positions and centered text
"""

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.drawing.image import Image
from openpyxl.utils import get_column_letter
from datetime import datetime
import os


def copy_perfect_row1_from_template(dest_ws, template_path):
    """
    Copy PERFECT Row 1 from Departmental-PRE.xlsx with:
    - Left logo (BISU seal)
    - Centered text (5 lines)
    - Right logos (2 logos - Bagong Pilipinas and ISO cert)

    Returns: Next available row after header
    """
    # Load the template
    template_wb = load_workbook(template_path)
    template_ws = template_wb.active

    # 1. Copy merged cells A1:I1
    dest_ws.merge_cells('A1:I1')

    # 2. Copy cell A1 content and formatting
    template_cell = template_ws['A1']
    dest_cell = dest_ws['A1']

    # Copy value
    dest_cell.value = template_cell.value

    # Copy font
    dest_cell.font = Font(
        name=template_cell.font.name,
        size=template_cell.font.size,
        bold=template_cell.font.bold,
        italic=template_cell.font.italic
    )

    # IMPORTANT: Text should be CENTER aligned (not left!)
    dest_cell.alignment = Alignment(
        horizontal='center',  # Center the text
        vertical='center',
        wrap_text=True
    )

    # Copy border (medium bottom border)
    border = Border(bottom=Side(style='medium', color='FF000000'))
    # Apply border to all cells in the merged range
    for col in range(1, 10):  # A to I
        dest_ws.cell(1, col).border = border

    # 3. Copy row height
    dest_ws.row_dimensions[1].height = template_ws.row_dimensions[1].height

    # 4. Copy column widths (A to I)
    for col in range(1, 10):
        col_letter = get_column_letter(col)
        dest_ws.column_dimensions[col_letter].width = template_ws.column_dimensions[col_letter].width

    # 5. Add logos with EXACT positions from template
    logo_dir = os.path.dirname(__file__)

    # LEFT LOGO: BISU Seal (logo_1.png)
    # Position: Column A, left side
    logo1_path = os.path.join(logo_dir, 'logo_1.png')
    if os.path.exists(logo1_path):
        img1 = Image(logo1_path)
        img1.width = 100   # Adjust size to fit nicely
        img1.height = 100
        # Anchor to cell A1 (left side)
        dest_ws.add_image(img1, 'A1')

    # RIGHT LOGO 1: Bagong Pilipinas (logo_2.png - the colorful one)
    # Position: Column I, right side
    logo2_path = os.path.join(logo_dir, 'logo_2.png')
    if os.path.exists(logo2_path):
        img2 = Image(logo2_path)
        img2.width = 100
        img2.height = 100
        # Anchor to cell I1 (right side)
        dest_ws.add_image(img2, 'I1')

    # RIGHT LOGO 2: ISO/Management cert (logo_3.png)
    # Position: Column H, right side (next to logo 2)
    logo3_path = os.path.join(logo_dir, 'logo_3.png')
    if os.path.exists(logo3_path):
        img3 = Image(logo3_path)
        img3.width = 85
        img3.height = 85
        # Anchor to cell H1 (right side, before I1)
        dest_ws.add_image(img3, 'H1')

    return 2  # Row 2 is next available


def generate_perfect_sample_report():
    """Generate Excel budget report with PERFECT Row 1 from template"""

    template_path = os.path.join(os.path.dirname(__file__), '../excel_templates/Departmental-PRE.xlsx')

    wb = Workbook()
    ws = wb.active
    ws.title = "Budget Summary Report"

    # Copy PERFECT Row 1 from template (with logos in correct positions)
    current_row = copy_perfect_row1_from_template(ws, template_path)

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

    # Save the workbook
    file_path = os.path.join(os.path.dirname(__file__), 'PERFECT_Budget_Report_BISU_Header.xlsx')
    wb.save(file_path)

    return file_path


if __name__ == '__main__':
    print("="*70)
    print("PERFECT VERSION - Budget Report with Correct Layout")
    print("="*70)
    print("\nRow 1 Layout:")
    print("  [LEFT]   BISU Seal Logo")
    print("  [CENTER] 5-line BISU Header Text (centered)")
    print("  [RIGHT]  ISO Cert Logo + Bagong Pilipinas Logo")
    print("-"*70)

    print("\nGenerating PERFECT sample report...")
    try:
        excel_path = generate_perfect_sample_report()
        print(f"\n[SUCCESS] Report created: {excel_path}")
        print("\nLayout now matches Departmental-PRE.xlsx:")
        print("  - Logo on LEFT (BISU seal)")
        print("  - Text CENTERED (5 lines)")
        print("  - Logos on RIGHT (2 logos)")
    except Exception as e:
        print(f"\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*70)
