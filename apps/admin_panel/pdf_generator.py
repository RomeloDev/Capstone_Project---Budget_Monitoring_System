# bb_budget_monitoring_system/apps/admin_panel/pdf_generator.py
"""
PRE PDF Generator using ReportLab
Generates formatted PRE documents for printing and signatures
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfgen import canvas
from django.core.files.base import ContentFile
from django.utils import timezone
from io import BytesIO
from decimal import Decimal


class PREPDFGenerator:
    """Generate formatted PRE PDF documents"""
    
    def __init__(self, pre):
        self.pre = pre
        self.buffer = BytesIO()
        self.width, self.height = letter
        self.styles = getSampleStyleSheet()
        
        # Custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=14,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        self.header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading2'],
            fontSize=11,
            textColor=colors.HexColor('#374151'),
            spaceAfter=6,
            fontName='Helvetica-Bold'
        )
        
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#1f2937'),
        )
    
    def generate(self):
        """Main method to generate PDF"""
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Build document content
        story = []
        
        # Add header
        story.extend(self._create_header())
        story.append(Spacer(1, 0.2*inch))
        
        # Add basic information
        story.extend(self._create_basic_info())
        story.append(Spacer(1, 0.2*inch))
        
        # Add budget allocation info
        story.extend(self._create_budget_info())
        story.append(Spacer(1, 0.2*inch))
        
        # Add receipts section
        story.extend(self._create_receipts_section())
        story.append(Spacer(1, 0.15*inch))
        
        # Add expenditures by category
        story.extend(self._create_expenditures_section())
        story.append(Spacer(1, 0.3*inch))
        
        # Add signature blocks
        story.extend(self._create_signature_blocks())
        
        # Build PDF
        doc.build(story, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)
        
        # Get PDF content
        pdf_content = self.buffer.getvalue()
        self.buffer.close()
        
        return pdf_content
    
    def _create_header(self):
        """Create document header"""
        elements = []
        
        # University/Organization name
        org_name = Paragraph(
            "<b>BATANGAS STATE UNIVERSITY</b><br/>The National Engineering University<br/>Alangilan Campus",
            self.title_style
        )
        elements.append(org_name)
        elements.append(Spacer(1, 0.1*inch))
        
        # Document title
        title = Paragraph(
            "<b>PROGRAM OF RECEIPTS AND EXPENDITURES</b>",
            self.title_style
        )
        elements.append(title)
        
        # PRE Number and Date
        pre_info = Paragraph(
            f"PRE No: <b>PRE-{str(self.pre.id)[:8].upper()}</b> | "
            f"Fiscal Year: <b>{self.pre.fiscal_year}</b> | "
            f"Date Generated: <b>{timezone.now().strftime('%B %d, %Y')}</b>",
            self.normal_style
        )
        elements.append(pre_info)
        
        return elements
    
    def _create_basic_info(self):
        """Create basic information section"""
        elements = []
        
        elements.append(Paragraph("<b>BASIC INFORMATION</b>", self.header_style))
        
        data = [
            ['Department:', self.pre.department, 'Program:', self.pre.program],
            ['Fund Source:', self.pre.fund_source, 'Status:', self.pre.status],
            ['Submitted By:', self.pre.submitted_by.get_full_name() or self.pre.submitted_by.username, 
             'Submitted Date:', self.pre.submitted_at.strftime('%B %d, %Y') if self.pre.submitted_at else 'N/A'],
        ]
        
        table = Table(data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1f2937')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(table)
        return elements
    
    def _create_budget_info(self):
        """Create budget allocation information"""
        elements = []
        
        if not self.pre.budget_allocation:
            return elements
        
        elements.append(Paragraph("<b>BUDGET ALLOCATION</b>", self.header_style))
        
        ba = self.pre.budget_allocation
        
        data = [
            ['Allocated Amount:', f'₱{ba.allocated_amount:,.2f}', 
             'Remaining Balance:', f'₱{ba.remaining_balance:,.2f}'],
            ['Budget Period:', ba.approved_budget.fiscal_year,
             'Total PRE Amount:', f'₱{self.pre.total_amount:,.2f}'],
        ]
        
        table = Table(data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1f2937')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(table)
        return elements
    
    def _create_receipts_section(self):
        """Create receipts section"""
        elements = []
        
        receipts = self.pre.receipts.all()
        
        if not receipts.exists():
            return elements
        
        elements.append(Paragraph("<b>RECEIPTS</b>", self.header_style))
        
        # Table header
        data = [['Receipt Type', 'Q1', 'Q2', 'Q3', 'Q4', 'Total']]
        
        total_q1 = total_q2 = total_q3 = total_q4 = Decimal('0.00')
        
        for receipt in receipts:
            row = [
                receipt.receipt_type,
                f'₱{receipt.q1_amount:,.2f}',
                f'₱{receipt.q2_amount:,.2f}',
                f'₱{receipt.q3_amount:,.2f}',
                f'₱{receipt.q4_amount:,.2f}',
                f'₱{receipt.get_total():,.2f}'
            ]
            data.append(row)
            
            total_q1 += receipt.q1_amount
            total_q2 += receipt.q2_amount
            total_q3 += receipt.q3_amount
            total_q4 += receipt.q4_amount
        
        # Add total row
        data.append([
            'TOTAL RECEIPTS',
            f'₱{total_q1:,.2f}',
            f'₱{total_q2:,.2f}',
            f'₱{total_q3:,.2f}',
            f'₱{total_q4:,.2f}',
            f'₱{(total_q1 + total_q2 + total_q3 + total_q4):,.2f}'
        ])
        
        table = Table(data, colWidths=[2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#dbeafe')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#93c5fd')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(table)
        return elements
    
    def _create_expenditures_section(self):
        """Create expenditures section grouped by category"""
        elements = []
        
        line_items = self.pre.line_items.select_related('category', 'subcategory').order_by(
            'category__sort_order', 'subcategory__sort_order', 'item_name'
        )
        
        if not line_items.exists():
            return elements
        
        elements.append(Paragraph("<b>EXPENDITURES</b>", self.header_style))
        
        # Group by category
        from itertools import groupby
        
        grand_total_q1 = grand_total_q2 = grand_total_q3 = grand_total_q4 = Decimal('0.00')
        
        for category, items in groupby(line_items, key=lambda x: x.category):
            # Category header
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph(f"<b>{category.name} ({category.category_type})</b>", self.normal_style))
            
            # Table header
            data = [['Item', 'Q1', 'Q2', 'Q3', 'Q4', 'Total']]
            
            cat_total_q1 = cat_total_q2 = cat_total_q3 = cat_total_q4 = Decimal('0.00')
            
            for item in items:
                item_name = item.item_name
                if item.subcategory:
                    item_name = f"{item.subcategory.name} - {item.item_name}"
                
                row = [
                    item_name[:50],  # Truncate long names
                    f'₱{item.q1_amount:,.2f}',
                    f'₱{item.q2_amount:,.2f}',
                    f'₱{item.q3_amount:,.2f}',
                    f'₱{item.q4_amount:,.2f}',
                    f'₱{item.get_total():,.2f}'
                ]
                data.append(row)
                
                cat_total_q1 += item.q1_amount
                cat_total_q2 += item.q2_amount
                cat_total_q3 += item.q3_amount
                cat_total_q4 += item.q4_amount
            
            # Category subtotal
            data.append([
                f'Subtotal - {category.category_type}',
                f'₱{cat_total_q1:,.2f}',
                f'₱{cat_total_q2:,.2f}',
                f'₱{cat_total_q3:,.2f}',
                f'₱{cat_total_q4:,.2f}',
                f'₱{(cat_total_q1 + cat_total_q2 + cat_total_q3 + cat_total_q4):,.2f}'
            ])
            
            grand_total_q1 += cat_total_q1
            grand_total_q2 += cat_total_q2
            grand_total_q3 += cat_total_q3
            grand_total_q4 += cat_total_q4
            
            table = Table(data, colWidths=[2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.3*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d1fae5')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#6ee7b7')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            
            elements.append(table)
        
        # Grand total
        elements.append(Spacer(1, 0.1*inch))
        grand_data = [[
            'TOTAL EXPENDITURES',
            f'₱{grand_total_q1:,.2f}',
            f'₱{grand_total_q2:,.2f}',
            f'₱{grand_total_q3:,.2f}',
            f'₱{grand_total_q4:,.2f}',
            f'₱{(grand_total_q1 + grand_total_q2 + grand_total_q3 + grand_total_q4):,.2f}'
        ]]
        
        grand_table = Table(grand_data, colWidths=[2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.3*inch])
        grand_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#1f2937')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(grand_table)
        return elements
    
    def _create_signature_blocks(self):
        """Create signature blocks"""
        elements = []
        
        elements.append(Spacer(1, 0.3*inch))
        
        # Signature data
        sig_data = [
            ['Prepared by:', 'Certified Correct:', 'Approved by:'],
            ['', '', ''],
            ['', '', ''],
            [self.pre.prepared_by_name or '_____________________', 
             self.pre.certified_by_name or '_____________________',
             self.pre.approved_by_name or '_____________________'],
            ['Position/Designation', 'Budget Officer', 'Campus Director'],
            ['Date: _____________', 'Date: _____________', 'Date: _____________']
        ]
        
        sig_table = Table(sig_data, colWidths=[2.5*inch, 2.5*inch, 2.5*inch])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
            ('LINEABOVE', (0, 3), (-1, 3), 1, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(sig_table)
        return elements
    
    def _add_page_number(self, canvas, doc):
        """Add page numbers to each page"""
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.HexColor('#6b7280'))
        canvas.drawRightString(self.width - 0.5*inch, 0.5*inch, text)
        canvas.restoreState()


def generate_pre_pdf(pre):
    """
    Main function to generate PDF for a PRE
    Returns the PDF content as bytes
    """
    generator = PREPDFGenerator(pre)
    pdf_content = generator.generate()
    return pdf_content


def save_pre_pdf(pre):
    """
    Generate and save PDF to the PRE model
    """
    pdf_content = generate_pre_pdf(pre)
    
    # Create filename
    filename = f'PRE_{str(pre.id)[:8].upper()}_{timezone.now().strftime("%Y%m%d")}.pdf'
    
    # Save to model
    pre.partially_approved_pdf.save(filename, ContentFile(pdf_content), save=True)
    
    return pre.partially_approved_pdf.url