"""
Dynamic PRE Excel Parser
Extracts ALL line items including custom ones added by users

This parser uses dynamic row scanning instead of fixed cell mappings,
allowing it to detect and extract custom line items that users insert
into the Excel template.

Key Features:
- Scans all rows within section boundaries
- Automatically detects custom line items
- Multi-level validation (cell, row, section, grand total)
- Subcategory detection for MOOE and Capital sections
- Comprehensive error reporting

Author: BISU Budget Monitoring System
Date: 2025
"""

from openpyxl import load_workbook
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Tuple, Optional
import logging

# Configure logging
logger = logging.getLogger(__name__)


class DynamicPREParser:
    """
    Dynamic parser that extracts all line items from PRE Excel file
    including custom items added by end users
    """

    # Section boundaries in the PRE template
    SECTION_BOUNDARIES = {
        'receipts': {
            'start_row': 9,
            'end_row': 11,
            'category': 'RECEIPTS',
            'subcategory': 'Budget Receipts',
            'has_subcategories': False,
        },
        'personnel': {
            'start_row': 13,
            'end_row': 19,
            'category': 'PERSONNEL',
            'subcategory': 'Personnel Services',
            'has_subcategories': False,
        },
        'mooe': {
            'start_row': 20,
            'end_row': 132,
            'category': 'MOOE',
            'subcategory': None,  # Will be detected dynamically
            'has_subcategories': True,
        },
        'capital': {
            'start_row': 133,
            'end_row': 176,
            'category': 'CAPITAL',
            'subcategory': None,  # Will be detected dynamically
            'has_subcategories': True,
        },
    }

    # Grand total row
    GRAND_TOTAL_ROW = 177

    # Row patterns to skip (section headers, totals, etc.)
    SKIP_PATTERNS = [
        'TOTAL',
        'Total',
        'Sub-total',
        'RECEIPTS / BUDGET',
        'BUDGET BY OBJECT',
        'Personnel Services',
        'Maintenance and Other Operating',
        'MAINTENANCE AND OTHER',
        'CAPITAL OUTLAYS',
        'Current Operating',
    ]

    # Standard template items (for custom item detection)
    STANDARD_ITEMS = {
        'GASS - TUITION FEE',
        'Basic Salary',
        'Honoraria',
        'Overtime Pay',
        'Travelling expenses-local',
        'Travelling Expenses-foreign',
        'Training Expenses',
        'Office Supplies Expenses',
        'Accountable Form Expenses',
        'Agricultural and Marine Supplies expenses',
        'Drugs and Medicines',
        # ... (add more as needed, or load from config)
    }

    def __init__(self, file_path: str):
        """
        Initialize parser with Excel file path

        Args:
            file_path: Path to PRE Excel file
        """
        self.file_path = file_path
        self.workbook = None
        self.worksheet = None
        self.errors = []
        self.warnings = []
        self.validation_summary = {
            'cell_errors': [],
            'row_total_mismatches': [],
            'grand_total_error': None,
        }

    def validate_template(self) -> bool:
        """
        Validate that the uploaded file is a valid PRE template

        Returns:
            bool: True if valid, False otherwise
        """
        try:
            self.workbook = load_workbook(self.file_path, data_only=True)
            self.worksheet = self.workbook.active

            # Basic validation - check if sheet has expected structure
            if not self.worksheet:
                self.errors.append("Could not read Excel worksheet")
                return False

            # Check if grand total row exists
            grand_total_cell = self.worksheet[f'A{self.GRAND_TOTAL_ROW}'].value
            if not grand_total_cell or 'TOTAL' not in str(grand_total_cell).upper():
                self.warnings.append(
                    f"Warning: Grand total row expected at row {self.GRAND_TOTAL_ROW} "
                    f"but found: '{grand_total_cell}'"
                )

            logger.info(f"Template validation successful: {self.file_path}")
            return True

        except Exception as e:
            self.errors.append(f"Error reading Excel file: {str(e)}")
            logger.error(f"Template validation failed: {str(e)}")
            return False

    def _parse_cell_value(self, cell_value) -> Decimal:
        """
        Parse cell value and convert to Decimal

        Handles:
        - None/empty values → 0
        - 'XXX', 'xxx', 'X' placeholders → 0
        - Numeric values → Decimal
        - Invalid values → 0 (with warning)

        Args:
            cell_value: Raw cell value from Excel

        Returns:
            Decimal: Parsed value
        """
        try:
            # Handle None or empty
            if cell_value is None or cell_value == '':
                return Decimal('0')

            # Convert to string and clean
            value_str = str(cell_value).strip().upper()

            # Handle 'XXX' or 'xxx' as 0 (template placeholders)
            if value_str in ['XXX', 'X', 'XX', 'XXXX', '-', '']:
                return Decimal('0')

            # Try to convert to Decimal
            return Decimal(str(cell_value))

        except (InvalidOperation, ValueError, TypeError):
            # If conversion fails, return 0 and log warning
            self.warnings.append(f"Invalid cell value: '{cell_value}' - treated as 0")
            return Decimal('0')

    def _is_skip_row(self, item_name: str) -> bool:
        """
        Check if row should be skipped (headers, totals, etc.)

        Args:
            item_name: Value from column A

        Returns:
            bool: True if should skip
        """
        if not item_name:
            return True

        item_name_upper = str(item_name).strip().upper()

        # Check against skip patterns
        for pattern in self.SKIP_PATTERNS:
            if pattern.upper() in item_name_upper:
                return True

        return False

    def _detect_subcategory(self, row_num: int, section_key: str) -> Optional[str]:
        """
        Detect subcategory for a line item by looking backward for group headers

        Group headers have item names but no quarterly values.

        Args:
            row_num: Current row number
            section_key: Section key (mooe or capital)

        Returns:
            str or None: Subcategory name
        """
        section = self.SECTION_BOUNDARIES[section_key]

        # Only MOOE and Capital have subcategories
        if not section['has_subcategories']:
            return section['subcategory']

        # Look backward from current row to find group header
        for check_row in range(row_num - 1, section['start_row'] - 1, -1):
            check_name = self.worksheet[f'A{check_row}'].value

            if not check_name:
                continue

            # Check if this row has quarterly values
            check_q1 = self.worksheet[f'E{check_row}'].value

            # Group header: has name but no quarterly values
            if check_name and not check_q1:
                # Make sure it's not a section header
                if not self._is_skip_row(check_name):
                    return str(check_name).strip()

        return 'Uncategorized'

    def _is_custom_item(self, item_name: str) -> bool:
        """
        Check if item is a custom item (not in standard template)

        Args:
            item_name: Item name from column A

        Returns:
            bool: True if custom item
        """
        # Simple check - compare against standard items
        # In production, you might load this from a config file
        return item_name.strip() not in self.STANDARD_ITEMS

    def _validate_row_total(
        self,
        row_num: int,
        item_name: str,
        q1: Decimal,
        q2: Decimal,
        q3: Decimal,
        q4: Decimal
    ) -> Optional[Dict]:
        """
        Validate that Q1+Q2+Q3+Q4 matches Excel total

        Args:
            row_num: Row number
            item_name: Item name
            q1, q2, q3, q4: Quarterly values

        Returns:
            dict or None: Mismatch info if validation fails
        """
        calculated_total = q1 + q2 + q3 + q4
        excel_total = self._parse_cell_value(self.worksheet[f'I{row_num}'].value)

        # Allow 1 cent rounding difference
        difference = abs(calculated_total - excel_total)
        if difference > Decimal('0.01'):
            return {
                'row': row_num,
                'item': item_name,
                'calculated': float(calculated_total),
                'excel_total': float(excel_total),
                'difference': float(difference)
            }

        return None

    def extract_line_items_dynamic(self) -> Dict:
        """
        Main extraction logic - dynamically scans all rows to extract line items

        Returns:
            dict: Extracted data organized by section
        """
        if not self.worksheet:
            self.errors.append("Worksheet not loaded")
            return None

        extracted_data = {
            'receipts': [],
            'personnel': [],
            'mooe': [],
            'capital': [],
        }

        total_items = 0
        custom_items_count = 0

        logger.info("Starting dynamic extraction...")

        # Scan each section
        for section_key, section_info in self.SECTION_BOUNDARIES.items():
            start_row = section_info['start_row']
            end_row = section_info['end_row']

            logger.info(f"Scanning section '{section_key}' (rows {start_row}-{end_row})")

            for row_num in range(start_row, end_row + 1):
                # Get item name from columns A, B, or C (check all for multi-level items)
                item_name = (
                    self.worksheet[f'A{row_num}'].value or
                    self.worksheet[f'B{row_num}'].value or
                    self.worksheet[f'C{row_num}'].value
                )

                # Skip if no item name or is a skip row
                if not item_name or self._is_skip_row(item_name):
                    continue

                item_name = str(item_name).strip()

                # Extract quarterly values
                q1 = self._parse_cell_value(self.worksheet[f'E{row_num}'].value)
                q2 = self._parse_cell_value(self.worksheet[f'F{row_num}'].value)
                q3 = self._parse_cell_value(self.worksheet[f'G{row_num}'].value)
                q4 = self._parse_cell_value(self.worksheet[f'H{row_num}'].value)

                # Only include if has any non-zero value
                if q1 == 0 and q2 == 0 and q3 == 0 and q4 == 0:
                    continue

                # Validate row total
                mismatch = self._validate_row_total(row_num, item_name, q1, q2, q3, q4)
                if mismatch:
                    self.validation_summary['row_total_mismatches'].append(mismatch)
                    self.warnings.append(
                        f"Row {row_num} ({item_name}): Quarterly sum doesn't match Excel total "
                        f"(Calculated: {mismatch['calculated']}, Excel: {mismatch['excel_total']})"
                    )

                # Detect subcategory
                subcategory = self._detect_subcategory(row_num, section_key)

                # Check if custom item
                is_custom = self._is_custom_item(item_name)
                if is_custom:
                    custom_items_count += 1

                # Calculate total (use calculated value, not Excel formula)
                total = q1 + q2 + q3 + q4

                # Add to extracted data
                item_data = {
                    'row_number': row_num,
                    'item_name': item_name,
                    'q1': q1,
                    'q2': q2,
                    'q3': q3,
                    'q4': q4,
                    'total': total,
                    'category': section_info['category'],
                    'subcategory': subcategory,
                    'source_type': 'excel',
                    'is_custom_item': is_custom,
                }

                extracted_data[section_key].append(item_data)
                total_items += 1

                logger.debug(
                    f"Row {row_num}: {item_name} | "
                    f"Q1={q1} Q2={q2} Q3={q3} Q4={q4} Total={total} | "
                    f"Custom={is_custom}"
                )

        logger.info(
            f"Extraction complete: {total_items} total items, "
            f"{custom_items_count} custom items"
        )

        # Store metadata
        extracted_data['_metadata'] = {
            'total_items': total_items,
            'custom_items_count': custom_items_count,
            'items_by_section': {
                'receipts': len(extracted_data['receipts']),
                'personnel': len(extracted_data['personnel']),
                'mooe': len(extracted_data['mooe']),
                'capital': len(extracted_data['capital']),
            }
        }

        return extracted_data

    def calculate_grand_total(self, extracted_data: Dict) -> Decimal:
        """
        Calculate grand total from all extracted line items

        Args:
            extracted_data: Extracted data dict

        Returns:
            Decimal: Grand total
        """
        grand_total = Decimal('0')

        for section_key in ['receipts', 'personnel', 'mooe', 'capital']:
            for item in extracted_data.get(section_key, []):
                grand_total += item['total']

        return grand_total

    def validate_grand_total(self, calculated_total: Decimal) -> Dict:
        """
        Validate calculated grand total against Excel grand total

        Args:
            calculated_total: Calculated grand total from line items

        Returns:
            dict: Validation result
        """
        # Get raw cell value first to check for placeholders
        raw_cell_value = self.worksheet[f'I{self.GRAND_TOTAL_ROW}'].value
        excel_grand_total = self._parse_cell_value(raw_cell_value)

        # Check if cell contains placeholder text
        if isinstance(raw_cell_value, str):
            placeholder_values = ['xxx', 'x', '-']
            if raw_cell_value.strip().lower() in placeholder_values:
                # Use calculated total as source of truth when placeholder is found
                warning_msg = (
                    f"Grand total cell contains placeholder '{raw_cell_value}'. "
                    f"Using calculated total: ₱{calculated_total:,.2f}"
                )
                logger.warning(warning_msg)

                return {
                    'valid': True,
                    'message': warning_msg,
                    'calculated_total': float(calculated_total),
                    'excel_total': float(calculated_total),  # Use calculated as excel value
                    'difference': 0.0,
                    'is_placeholder': True,
                }

        difference = abs(calculated_total - excel_grand_total)

        if difference > Decimal('0.01'):
            error_msg = (
                f"Grand total mismatch: "
                f"Calculated=₱{calculated_total:,.2f}, "
                f"Excel=₱{excel_grand_total:,.2f}, "
                f"Difference=₱{difference:,.2f}"
            )
            logger.error(error_msg)

            return {
                'valid': False,
                'error': error_msg,
                'calculated_total': float(calculated_total),
                'excel_total': float(excel_grand_total),
                'difference': float(difference),
            }

        logger.info(f"Grand total validation passed: ₱{calculated_total:,.2f}")

        return {
            'valid': True,
            'message': 'Grand total validated successfully',
            'calculated_total': float(calculated_total),
            'excel_total': float(excel_grand_total),
            'difference': float(difference),
        }

    def get_fiscal_year(self) -> Optional[str]:
        """
        Extract fiscal year from PRE document (Row 3, Column A)

        Returns:
            str or None: Fiscal year
        """
        try:
            fy_cell = self.worksheet['A3'].value
            if fy_cell:
                # Extract year from "FY 2026" format
                fy_str = str(fy_cell).strip()
                if fy_str.startswith('FY'):
                    return fy_str.split()[1] if len(fy_str.split()) > 1 else fy_str
                return fy_str
            return None
        except Exception as e:
            logger.warning(f"Could not extract fiscal year: {str(e)}")
            return None

    def parse(self) -> Dict:
        """
        Main parse function - orchestrates the entire parsing process

        Returns:
            dict: Parse result with success status, data, errors, warnings
        """
        logger.info(f"Starting PRE Excel parsing: {self.file_path}")

        # Step 1: Validate template
        if not self.validate_template():
            return {
                'success': False,
                'errors': self.errors,
                'warnings': self.warnings,
            }

        # Step 2: Extract line items dynamically
        extracted_data = self.extract_line_items_dynamic()

        if extracted_data is None:
            return {
                'success': False,
                'errors': self.errors,
                'warnings': self.warnings,
            }

        # Step 3: Calculate grand total
        calculated_grand_total = self.calculate_grand_total(extracted_data)

        # Step 4: Validate grand total
        grand_total_validation = self.validate_grand_total(calculated_grand_total)
        self.validation_summary['grand_total_error'] = grand_total_validation

        if not grand_total_validation['valid']:
            self.errors.append(grand_total_validation['error'])

        # Step 5: Get fiscal year
        fiscal_year = self.get_fiscal_year()

        # Step 6: Compile results
        metadata = extracted_data.pop('_metadata', {})

        result = {
            'success': len(self.errors) == 0,
            'data': extracted_data,
            'grand_total': calculated_grand_total,
            'fiscal_year': fiscal_year,
            'total_items': metadata.get('total_items', 0),
            'custom_items_count': metadata.get('custom_items_count', 0),
            'items_by_section': metadata.get('items_by_section', {}),
            'errors': self.errors,
            'warnings': self.warnings,
            'validation_summary': self.validation_summary,
        }

        logger.info(
            f"Parsing complete: Success={result['success']}, "
            f"Items={result['total_items']}, "
            f"Custom={result['custom_items_count']}, "
            f"Errors={len(self.errors)}, "
            f"Warnings={len(self.warnings)}"
        )

        return result


# Convenience function for backward compatibility
def parse_pre_excel_dynamic(file_path: str) -> Dict:
    """
    Parse PRE Excel file using dynamic parser

    Args:
        file_path: Path to Excel file

    Returns:
        dict: Parse result
    """
    parser = DynamicPREParser(file_path)
    return parser.parse()


# For testing
if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        print(f"Testing parser with: {test_file}")
        result = parse_pre_excel_dynamic(test_file)

        print("\n=== PARSE RESULT ===")
        print(f"Success: {result['success']}")
        print(f"Total Items: {result.get('total_items', 0)}")
        print(f"Custom Items: {result.get('custom_items_count', 0)}")
        print(f"Grand Total: PHP {result.get('grand_total', 0):,.2f}")
        print(f"Fiscal Year: {result.get('fiscal_year', 'N/A')}")
        print(f"\nItems by section:")
        for section, count in result.get('items_by_section', {}).items():
            print(f"  {section}: {count}")
        print(f"\nErrors: {len(result['errors'])}")
        for err in result['errors']:
            print(f"  - {err}")
        print(f"\nWarnings: {len(result['warnings'])}")
        for warn in result['warnings'][:10]:  # Show first 10
            print(f"  - {warn}")
    else:
        print("Usage: python pre_parser_dynamic.py <excel_file_path>")
