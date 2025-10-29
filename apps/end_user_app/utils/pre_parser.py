"""
PRE Excel Parser Utility
Extracts data from PRE template with fixed cell positions
"""

from openpyxl import load_workbook
from decimal import Decimal, InvalidOperation


class PREParser:
    """Parse PRE Excel file based on fixed cell positions"""
    
    # Define cell mappings based on your PRE template structure
    # Format: 'category': [(item_name, q1_cell, q2_cell, q3_cell, q4_cell, total_cell)]
    
    CELL_MAPPINGS = {
        # RECEIPTS / BUDGET
        'receipts': [
            ('GASS - TUITION FEE', 'E10', 'F10', 'G10', 'H10', 'I10'),
        ],
        
        # PERSONNEL SERVICES
        'personnel': [
            ('Basic Salary', 'E15', 'F15', 'G15', 'H15', 'I15'),
            ('Honoraria', 'E16', 'F16', 'G16', 'H16', 'I16'),
            ('Overtime Pay', 'E17', 'F17', 'G17', 'H17', 'I17'),
        ],
        
        # MAINTENANCE AND OTHER OPERATING EXPENSES
        'mooe': {
            'travelling_expenses': [
                ('Travelling expenses-local', 'E23', 'F23', 'G23', 'H23', 'I23'),
                ('Travelling Expenses-foreign', 'E24', 'F24', 'G24', 'H24', 'I24'),
            ],
            'training': [
                ('Training Expenses', 'E26', 'F26', 'G26', 'H26', 'I26'),
            ],
            'supplies': [
                ('Office Supplies Expenses', 'E28', 'F28', 'G28', 'H28', 'I28'),
                ('Accountable Form Expenses', 'E29', 'F29', 'G29', 'H29', 'I29'),
                ('Agricultural and Marine Supplies expenses', 'E30', 'F30', 'G30', 'H30', 'I30'),
                ('Drugs and Medicines', 'E31', 'F31', 'G31', 'H31', 'I31'),
                ('Medical, Dental & Laboratory Supplies Expenses', 'E32', 'F32', 'G32', 'H32', 'I32'),
                ('Food Supplies Expenses', 'E33', 'F33', 'G33', 'H33', 'I33'),
            ],
            'fuel': [
                ('Fuel, Oil and Lubricants Expenses', 'E39', 'F39', 'G39', 'H39', 'I39'),
            ],
            'textbooks': [
                ('Textbooks and instructional materials expenses', 'E40', 'F40', 'G40', 'H40', 'I40'),
            ],
            'construction_materials': [
                ('Construction Materials Expense', 'E41', 'F41', 'G41', 'H41', 'I41'),
            ],
            'other_supplies': [
                ('Other Supplies & Materials Expenses', 'E42', 'F42', 'G42', 'H42', 'I42'),
            ],
            'machinery': [
                ('Machinery', 'E44', 'F44', 'G44', 'H44', 'I44'),
                ('Office Equipment', 'E45', 'F45', 'G45', 'H45', 'I45'),
                ('Information and Communications Technology Equipment', 'E46', 'F46', 'G46', 'H46', 'I46'),
                ('Communications Equipment', 'E47', 'F47', 'G47', 'H47', 'I47'),
                ('Disaster Response and Rescue Equipment', 'E48', 'F48', 'G48', 'H48', 'I48'),
                ('Medical Equipment', 'E49', 'F49', 'G49', 'H49', 'I49'),
                ('Printing Equipment', 'E50', 'F50', 'G50', 'H50', 'I50'),
                ('Sports Equipment', 'E51', 'F51', 'G51', 'H51', 'I51'),
                ('Technical and Scientific Equipment', 'E52', 'F52', 'G52', 'H52', 'I52'),
                ('ICT Equipment', 'E53', 'F53', 'G53', 'H53', 'I53'),
                ('Other Machinery and Equipment', 'E54', 'F54', 'G54', 'H54', 'I54'),
            ],
            'furniture': [
                ('Furniture and Fixtures', 'E56', 'F56', 'G56', 'H56', 'I56'),
                ('Books', 'E57', 'F57', 'G57', 'H57', 'I57'),
            ],
            'utility': [
                ('Water Expenses', 'E59', 'F59', 'G59', 'H59', 'I59'),
                ('Electricity Expenses', 'E60', 'F60', 'G60', 'H60', 'I60'),
            ],
            'communication': [
                ('Postage and Courier Services', 'E62', 'F62', 'G62', 'H62', 'I62'),
                ('Telephone Expenses', 'E63', 'F63', 'G63', 'H63', 'I63'),
                ('Telephone Expenses (Landline)', 'E64', 'F64', 'G64', 'H64', 'I64'),
                ('Internet Subscription Expenses', 'E65', 'F65', 'G65', 'H65', 'I65'),
                ('Cable, Satellite, Telegraph & Radio Expenses', 'E66', 'F66', 'G66', 'H66', 'I66'),
            ],
            'awards': [
                ('Awards/Rewards expenses', 'E72', 'F72', 'G72', 'H72', 'I72'),
                ('Prizes', 'E73', 'F73', 'G73', 'H73', 'I73'),
            ],
            'research': [
                ('Survey, Research, Exploration and Development', 'E74', 'F74', 'G74', 'H74', 'I74'),
                ('Survey expenses', 'E75', 'F75', 'G75', 'H75', 'I75'),
                ('Survey, Research, Exploration and Development expenses', 'E76', 'F76', 'G76', 'H76', 'I76'),
            ],
            'professional': [
                ('Legal Services', 'E78', 'F78', 'G78', 'H78', 'I78'),
                ('Auditing services', 'E79', 'F79', 'G79', 'H79', 'I79'),
                ('Consultancy services', 'E80', 'F80', 'G80', 'H80', 'I80'),
                ('Other Professional Services', 'E81', 'F81', 'G81', 'H81', 'I81'),
            ],
            'general_services': [
                ('Security services', 'E83', 'F83', 'G83', 'H83', 'I83'),
                ('Janitorial Services', 'E84', 'F84', 'G84', 'H84', 'I84'),
            ],
        },
        
        # CAPITAL OUTLAYS
        'capital': {
            'land': [
                ('Land', 'E135', 'F135', 'G135', 'H135', 'I135'),
                ('Land', 'E136', 'F136', 'G136', 'H136', 'I136'),
            ],
            'land_improvements': [
                ('Land Improvements, Aquaculture Structure', 'E138', 'F138', 'G138', 'H138', 'I138'),
            ],
            'infrastructure': [
                ('Water Supply Systems', 'E140', 'F140', 'G140', 'H140', 'I140'),
                ('Power Supply System', 'E141', 'F141', 'G141', 'H141', 'I141'),
                ('Other Infrastructure Assets', 'E142', 'F142', 'G142', 'H142', 'I142'),
            ],
            'buildings': [
                ('Building', 'E144', 'F144', 'G144', 'H144', 'I144'),
                ('School Buildings', 'E145', 'F145', 'G145', 'H145', 'I145'),
                ('Hostels and Dormitories', 'E146', 'F146', 'G146', 'H146', 'I146'),
                ('Other Structures', 'E147', 'F147', 'G147', 'H147', 'I147'),
            ],
        }
    }
    
    def __init__(self, file_path):
        """Initialize parser with Excel file"""
        self.file_path = file_path
        self.workbook = None
        self.worksheet = None
        self.errors = []
        
    def validate_template(self):
        """Validate that the uploaded file matches expected template structure"""
        try:
            self.workbook = load_workbook(self.file_path, data_only=True)
            self.worksheet = self.workbook.active
            
            # Check header cells
            # if self.worksheet['A1'].value != "Republic of the Philippines":
            #     self.errors.append("Invalid template: Header mismatch")
            #     return False
            
            # if "BOHOL ISLAND STATE UNIVERSITY" not in str(self.worksheet['B2'].value or ''):
            #     self.errors.append("Invalid template: Institution name mismatch")
            #     return False
            
            return True
            
        except Exception as e:
            self.errors.append(f"Error reading file: {str(e)}")
            return False
    
    def _parse_cell_value(self, cell_ref):
        """Parse cell value and convert to Decimal, handling 'xxx' or 'XXX' as 0"""
        try:
            cell_value = self.worksheet[cell_ref].value
            
            # Handle None or empty
            if cell_value is None or cell_value == '':
                return Decimal('0')
            
            # Convert to string and clean
            value_str = str(cell_value).strip().upper()
            
            # Handle 'XXX' or 'xxx' as 0
            if value_str in ['XXX', 'X', 'XX', 'XXXX']:
                return Decimal('0')
            
            # Try to convert to Decimal
            return Decimal(str(cell_value))
            
        except (InvalidOperation, ValueError, TypeError):
            # If conversion fails, return 0
            return Decimal('0')
    
    def extract_line_items(self):
        """Extract all line items from the PRE"""
        if not self.worksheet:
            self.errors.append("Worksheet not loaded")
            return None
        
        extracted_data = {
            'receipts': [],
            'personnel': [],
            'mooe': [],
            'capital': [],
        }
        
        # ✅ Track validation warnings
        validation_warnings = []
        
        # Extract Receipts
        for item_name, q1, q2, q3, q4, total in self.CELL_MAPPINGS['receipts']:
            q1_val = self._parse_cell_value(q1)
            q2_val = self._parse_cell_value(q2)
            q3_val = self._parse_cell_value(q3)
            q4_val = self._parse_cell_value(q4)
            total_val = self._parse_cell_value(total)
            
            # ✅ Calculate correct total from quarters
            calculated_total = q1_val + q2_val + q3_val + q4_val
            
            # ✅ Validate: Check if Excel total matches calculated total
            if calculated_total > 0 and abs(total_val - calculated_total) > Decimal('0.01'):
                validation_warnings.append({
                    'item': item_name,
                    'excel_total': float(total_val),
                    'calculated_total': float(calculated_total),
                    'difference': float(calculated_total - total_val)
                })
            
            # Only add if there's any value
            if q1_val > 0 or q2_val > 0 or q3_val > 0 or q4_val > 0:
                extracted_data['receipts'].append({
                    'item_name': item_name,
                    'q1': q1_val,
                    'q2': q2_val,
                    'q3': q3_val,
                    'q4': q4_val,
                    'total': calculated_total
                })
        
        # Extract Personnel Services
        for item_name, q1, q2, q3, q4, total in self.CELL_MAPPINGS['personnel']:
            q1_val = self._parse_cell_value(q1)
            q2_val = self._parse_cell_value(q2)
            q3_val = self._parse_cell_value(q3)
            q4_val = self._parse_cell_value(q4)
            total_val = self._parse_cell_value(total)
            
            calculated_total = q1_val + q2_val + q3_val + q4_val
            
            if calculated_total > 0 and abs(total_val - calculated_total) > Decimal('0.01'):
                validation_warnings.append({
                    'item': item_name,
                    'excel_total': float(total_val),
                    'calculated_total': float(calculated_total),
                    'difference': float(calculated_total - total_val)
                })
            
            if q1_val > 0 or q2_val > 0 or q3_val > 0 or q4_val > 0:
                extracted_data['personnel'].append({
                    'item_name': item_name,
                    'q1': q1_val,
                    'q2': q2_val,
                    'q3': q3_val,
                    'q4': q4_val,
                    'total': calculated_total
                })
        
        # Extract MOOE (nested structure)
        for category, items in self.CELL_MAPPINGS['mooe'].items():
            for item_name, q1, q2, q3, q4, total in items:
                q1_val = self._parse_cell_value(q1)
                q2_val = self._parse_cell_value(q2)
                q3_val = self._parse_cell_value(q3)
                q4_val = self._parse_cell_value(q4)
                total_val = self._parse_cell_value(total)
                
                calculated_total = q1_val + q2_val + q3_val + q4_val
            
                if calculated_total > 0 and abs(total_val - calculated_total) > Decimal('0.01'):
                    validation_warnings.append({
                        'item': item_name,
                        'excel_total': float(total_val),
                        'calculated_total': float(calculated_total),
                        'difference': float(calculated_total - total_val)
                    })
                
                if q1_val > 0 or q2_val > 0 or q3_val > 0 or q4_val > 0:
                    extracted_data['mooe'].append({
                        'category': category,
                        'item_name': item_name,
                        'q1': q1_val,
                        'q2': q2_val,
                        'q3': q3_val,
                        'q4': q4_val,
                        'total': calculated_total
                    })
        
        # Extract Capital Outlays (nested structure)
        for category, items in self.CELL_MAPPINGS['capital'].items():
            for item_name, q1, q2, q3, q4, total in items:
                q1_val = self._parse_cell_value(q1)
                q2_val = self._parse_cell_value(q2)
                q3_val = self._parse_cell_value(q3)
                q4_val = self._parse_cell_value(q4)
                total_val = self._parse_cell_value(total)
                
                calculated_total = q1_val + q2_val + q3_val + q4_val
            
                if calculated_total > 0 and abs(total_val - calculated_total) > Decimal('0.01'):
                    validation_warnings.append({
                        'item': item_name,
                        'excel_total': float(total_val),
                        'calculated_total': float(calculated_total),
                        'difference': float(calculated_total - total_val)
                    })
                
                if q1_val > 0 or q2_val > 0 or q3_val > 0 or q4_val > 0:
                    extracted_data['capital'].append({
                        'category': category,
                        'item_name': item_name,
                        'q1': q1_val,
                        'q2': q2_val,
                        'q3': q3_val,
                        'q4': q4_val,
                        'total': calculated_total
                    })
                    
        # ✅ Store validation warnings
        extracted_data['validation_warnings'] = validation_warnings
        
        return extracted_data
    
    def calculate_grand_total(self, extracted_data):
        """Calculate the grand total from all categories"""
        grand_total = Decimal('0')
        
        for category in ['receipts', 'personnel', 'mooe', 'capital']:
            for item in extracted_data.get(category, []):
                grand_total += item['total']
        
        return grand_total
    
    def get_fiscal_year(self):
        """Extract fiscal year from PRE document"""
        try:
            # Assuming fiscal year is in a specific cell (adjust as needed)
            fy_cell = self.worksheet['D3'].value  # Adjust cell reference
            if fy_cell:
                return str(fy_cell).strip()
            return None
        except:
            return None


def parse_pre_excel(file_path):
    """Main function to parse PRE Excel file"""
    parser = PREParser(file_path)
    
    # Validate template
    if not parser.validate_template():
        return {
            'success': False,
            'errors': parser.errors
        }
    
    # Extract data
    extracted_data = parser.extract_line_items()
    
    if extracted_data is None:
        return {
            'success': False,
            'errors': parser.errors
        }
    
    # ✅ Get validation warnings
    validation_warnings = extracted_data.pop('validation_warnings', [])
    
    # Calculate grand total
    grand_total = parser.calculate_grand_total(extracted_data)
    
    # Get fiscal year
    fiscal_year = parser.get_fiscal_year()
    
    return {
        'success': True,
        'data': extracted_data,
        'grand_total': grand_total,
        'fiscal_year': fiscal_year,
        'validation_warnings': validation_warnings,
        'errors': []
    }