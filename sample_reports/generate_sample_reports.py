"""
Generate sample budget reports with BISU Header Format

This script creates example reports (Excel and PDF) with the BISU header
matching the format from Departmental-PRE.xlsx

Run this script to generate sample reports in the sample_reports directory.
"""

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime
from decimal import Decimal

# For PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
import os


def create_bisu_header_excel(ws, report_title, start_row=1):
    """
    Add BISU header to Excel worksheet matching Departmental-PRE.xlsx format

    Returns: Next available row after header
    """
    current_row = start_row

    # Row 1: Republic of the Philippines
    ws.merge_cells(f'A{current_row}:I{current_row}')
    cell = ws[f'A{current_row}']
    cell.value = "Republic of the Philippines"
    cell.font = Font(name='Arial', size=11, bold=False)
    cell.alignment = Alignment(horizontal='center', vertical='center')
    current_row += 1

    # Row 2: BOHOL ISLAND STATE UNIVERSITY
    ws.merge_cells(f'A{current_row}:I{current_row}')
    cell = ws[f'A{current_row}']
    cell.value = "BOHOL ISLAND STATE UNIVERSITY"
    cell.font = Font(name='Arial', size=14, bold=True)
    cell.alignment = Alignment(horizontal='center', vertical='center')
    current_row += 1

    # Row 3: Address
    ws.merge_cells(f'A{current_row}:I{current_row}')
    cell = ws[f'A{current_row}']
    cell.value = "Magsija, Balilihan, 6342, Bohol, Philippines"
    cell.font = Font(name='Arial', size=10, bold=False)
    cell.alignment = Alignment(horizontal='center', vertical='center')
    current_row += 1

    # Row 4: Office
    ws.merge_cells(f'A{current_row}:I{current_row}')
    cell = ws[f'A{current_row}']
    cell.value = "Office of the Administration and Finance"
    cell.font = Font(name='Arial', size=11, bold=True)
    cell.alignment = Alignment(horizontal='center', vertical='center')
    current_row += 1

    # Row 5: BISU Values
    ws.merge_cells(f'A{current_row}:I{current_row}')
    cell = ws[f'A{current_row}']
    cell.value = "Balance I Integrity I Stewardship I Uprightness"
    cell.font = Font(name='Arial', size=9, bold=False, italic=True)
    cell.alignment = Alignment(horizontal='center', vertical='center')
    current_row += 1

    # Blank row
    current_row += 1

    # Report Title
    ws.merge_cells(f'A{current_row}:I{current_row}')
    cell = ws[f'A{current_row}']
    cell.value = report_title
    cell.font = Font(name='Arial', size=16, bold=True, color='1F4E78')
    cell.alignment = Alignment(horizontal='center', vertical='center')
    cell.fill = PatternFill(start_color='E7E6E6', end_color='E7E6E6', fill_type='solid')
    current_row += 1

    # Report metadata
    ws.merge_cells(f'A{current_row}:I{current_row}')
    cell = ws[f'A{current_row}']
    cell.value = f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
    cell.font = Font(name='Arial', size=10, bold=False, italic=True)
    cell.alignment = Alignment(horizontal='center', vertical='center')
    current_row += 1

    # Blank row before data
    current_row += 1

    # Set row heights for header
    for i in range(start_row, current_row):
        ws.row_dimensions[i].height = 18

    return current_row


def generate_sample_excel_report():
    """Generate sample Excel budget report with BISU header"""

    wb = Workbook()
    ws = wb.active
    ws.title = "Budget Summary Report"

    # Add BISU header
    data_start_row = create_bisu_header_excel(ws, "BUDGET SUMMARY REPORT - FISCAL YEAR 2025")

    # Sample data - Budget Overview
    current_row = data_start_row

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

        # Add borders
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

            # Add borders
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
    file_path = os.path.join(os.path.dirname(__file__), 'SAMPLE_Budget_Report_with_BISU_Header.xlsx')
    wb.save(file_path)

    return file_path


def create_bisu_header_pdf():
    """Create BISU header elements for PDF using ReportLab"""

    elements = []

    # Define styles
    title_style = ParagraphStyle(
        'BISUTitle',
        fontName='Helvetica',
        fontSize=11,
        textColor=colors.HexColor('#1f2937'),
        alignment=TA_CENTER,
        spaceAfter=2
    )

    main_title_style = ParagraphStyle(
        'BISUMainTitle',
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor('#1f2937'),
        alignment=TA_CENTER,
        spaceAfter=2
    )

    address_style = ParagraphStyle(
        'BISUAddress',
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#1f2937'),
        alignment=TA_CENTER,
        spaceAfter=2
    )

    office_style = ParagraphStyle(
        'BISUOffice',
        fontName='Helvetica-Bold',
        fontSize=11,
        textColor=colors.HexColor('#1f2937'),
        alignment=TA_CENTER,
        spaceAfter=2
    )

    values_style = ParagraphStyle(
        'BISUValues',
        fontName='Helvetica-Oblique',
        fontSize=9,
        textColor=colors.HexColor('#374151'),
        alignment=TA_CENTER,
        spaceAfter=6
    )

    # Add header elements
    elements.append(Paragraph("Republic of the Philippines", title_style))
    elements.append(Paragraph("<b>BOHOL ISLAND STATE UNIVERSITY</b>", main_title_style))
    elements.append(Paragraph("Magsija, Balilihan, 6342, Bohol, Philippines", address_style))
    elements.append(Paragraph("<b>Office of the Administration and Finance</b>", office_style))
    elements.append(Paragraph("<i>Balance I Integrity I Stewardship I Uprightness</i>", values_style))

    return elements


def generate_sample_pdf_report():
    """Generate sample PDF budget report with BISU header"""

    file_path = os.path.join(os.path.dirname(__file__), 'SAMPLE_Budget_Report_with_BISU_Header.pdf')

    # Create PDF document
    doc = SimpleDocTemplate(
        file_path,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    # Container for PDF elements
    story = []

    # Add BISU header
    story.extend(create_bisu_header_pdf())
    story.append(Spacer(1, 0.3*inch))

    # Report title
    report_title_style = ParagraphStyle(
        'ReportTitle',
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=colors.HexColor('#1F4E78'),
        alignment=TA_CENTER,
        spaceAfter=10
    )

    story.append(Paragraph("BUDGET SUMMARY REPORT - FISCAL YEAR 2025", report_title_style))

    # Report metadata
    metadata_style = ParagraphStyle(
        'Metadata',
        fontName='Helvetica-Oblique',
        fontSize=10,
        textColor=colors.HexColor('#6b7280'),
        alignment=TA_CENTER,
        spaceAfter=20
    )

    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", metadata_style))
    story.append(Spacer(1, 0.2*inch))

    # Section header style
    section_header_style = ParagraphStyle(
        'SectionHeader',
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.white,
        alignment=TA_CENTER,
        spaceAfter=10
    )

    # Budget Allocation Summary Section
    story.append(Paragraph("BUDGET ALLOCATION SUMMARY", section_header_style))

    summary_data = [
        ['Description', 'Amount (₱)'],
        ['Total Allocated Budget', '₱500,000.00'],
        ['Total Budget Used', '₱287,500.00'],
        ['Remaining Balance', '₱212,500.00'],
        ['Budget Utilization', '57.50%'],
    ]

    summary_table = Table(summary_data, colWidths=[4*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

        # Data rows
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#1f2937')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),

        # Borders
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#4472C4')),

        # Emphasize remaining balance
        ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1, 3), (1, 3), colors.HexColor('#1F4E78')),
    ]))

    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))

    # Transaction Details Section
    story.append(Paragraph("TRANSACTION DETAILS", section_header_style))

    transaction_data = [
        ['Date', 'Type', 'Document #', 'Description', 'Amount (₱)', 'Status'],
        ['2025-01-15', 'PRE', 'PRE-2025-001', 'Office Supplies Budget', '₱50,000.00', 'Approved'],
        ['2025-02-10', 'PR', 'PR-2025-045', 'Printer and Toner', '₱25,000.00', 'Approved'],
        ['2025-02-20', 'AD', 'AD-2025-012', 'Faculty Workshop', '₱75,000.00', 'Approved'],
        ['2025-03-05', 'PR', 'PR-2025-078', 'Laboratory Equipment', '₱125,000.00', 'Approved'],
        ['2025-03-15', 'AD', 'AD-2025-023', 'Leadership Training', '₱12,500.00', 'Pending'],
    ]

    transaction_table = Table(transaction_data, colWidths=[0.9*inch, 0.5*inch, 1.1*inch, 2*inch, 1*inch, 0.8*inch])
    transaction_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5B9BD5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

        # Data rows
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#1f2937')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # Date
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Type
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Document #
        ('ALIGN', (3, 1), (3, -1), 'LEFT'),    # Description
        ('ALIGN', (4, 1), (4, -1), 'RIGHT'),   # Amount
        ('ALIGN', (5, 1), (5, -1), 'CENTER'),  # Status

        # Borders
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#5B9BD5')),

        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
    ]))

    story.append(transaction_table)
    story.append(Spacer(1, 0.3*inch))

    # Footer note
    footer_style = ParagraphStyle(
        'Footer',
        fontName='Helvetica-Oblique',
        fontSize=8,
        textColor=colors.HexColor('#6b7280'),
        alignment=TA_CENTER,
    )

    story.append(Paragraph(
        "This is a computer-generated report from the Budget Monitoring System.",
        footer_style
    ))

    # Build PDF
    doc.build(story)

    return file_path


if __name__ == '__main__':
    print("="*70)
    print("BISU Budget Report Generator - Sample Reports")
    print("="*70)
    print("\nGenerating sample reports with BISU header format...")
    print("\nNote: This demonstrates the proposed header format for client review.")
    print("-"*70)

    # Generate Excel report
    print("\n[1/2] Generating Excel report...")
    try:
        excel_path = generate_sample_excel_report()
        print(f"[OK] Excel report created: {excel_path}")
    except Exception as e:
        print(f"[ERROR] Excel report failed: {e}")

    # Generate PDF report
    print("\n[2/2] Generating PDF report...")
    try:
        pdf_path = generate_sample_pdf_report()
        print(f"[OK] PDF report created: {pdf_path}")
    except Exception as e:
        print(f"[ERROR] PDF report failed: {e}")

    print("\n" + "="*70)
    print("Sample reports generated successfully!")
    print("="*70)
    print("\nPlease review the sample reports to verify they meet client requirements.")
    print("Both reports include:")
    print("  • Official BISU header (matching Departmental-PRE.xlsx)")
    print("  • Professional formatting and styling")
    print("  • Sample budget data and transactions")
    print("  • Print-ready layout")
    print("\nIf approved, these formats will be integrated into the system.")
    print("="*70)
