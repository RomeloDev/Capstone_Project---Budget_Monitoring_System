# Line Item Savings Feature - Complete Documentation

**Project**: BISU Balilihan Budget Monitoring System
**Feature**: PRE Line Item Savings & Surplus Tracking
**Implementation Date**: November 17, 2025
**Version**: 1.0
**Status**: Production Ready ✅

---

## Table of Contents
1. [Overview](#overview)
2. [Feature Purpose](#feature-purpose)
3. [Key Concepts](#key-concepts)
4. [Technical Architecture](#technical-architecture)
5. [User Guide](#user-guide)
6. [Administrator Guide](#administrator-guide)
7. [Database Schema](#database-schema)
8. [API Reference](#api-reference)
9. [Configuration](#configuration)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The **Line Item Savings Feature** extends the existing Budget Savings system by providing **granular tracking** of unused/surplus budget at the **PRE (Program of Receipts and Expenditures) line item level**.

### What It Does
- Tracks surplus budget for individual line items (not just department totals)
- Provides quarterly breakdown (Q1, Q2, Q3, Q4) of unused funds
- Flags "significant" surplus items (>₱5,000) requiring attention
- Groups savings by budget category (Personnel, MOOE, Capital Outlays)
- Enables data-driven budget reallocation decisions

### Key Benefits
1. **Granular Visibility** - See exactly which line items have surplus
2. **Quarterly Insights** - Identify which quarters have most unused budget
3. **Category Analysis** - Understand spending patterns by category
4. **Prioritization** - Focus on significant surplus items first
5. **Compliance** - Detailed audit trail for government requirements

---

## Feature Purpose

### Business Problem Solved
**Before**: Admins only knew total department surplus (e.g., "College of Engineering has ₱50,000 surplus")

**After**: Admins know exact breakdown:
- Office Supplies: ₱800 surplus (Q1: ₱200, Q2: ₱300, Q3: ₱200, Q4: ₱100)
- ICT Equipment: ₱18,000 surplus ⚠️ **SIGNIFICANT** (Q3: ₱18,000)
- Training: ₱15,000 surplus ⚠️ **SIGNIFICANT** (Q2: ₱15,000)

This enables **informed decisions** about:
- Which budgets to reallocate
- Which departments consistently over-budget
- Which quarters have procurement delays

---

## Key Concepts

### 1. Surplus
**Definition**: Any unused/unspent budget amount.

**Formula**:
```
Surplus = Allocated Amount - Used Amount
```

**Example**:
```
Allocated: ₱50,000
PR Used:   ₱20,000
AD Used:   ₱15,000
Total Used: ₱35,000
─────────────────────
SURPLUS:   ₱15,000
```

### 2. Significant Surplus
**Definition**: Surplus exceeding ₱5,000 threshold.

**Why It Matters**:
- Small surplus (₱500) = Normal operational variance ✅
- Large surplus (₱15,000) = Requires investigation ⚠️
  - Over-allocated budget?
  - Cancelled projects?
  - Procurement delays?
  - Opportunity for reallocation?

**Visual Indicators**:
- Regular Surplus: Green text
- Significant Surplus: Yellow text + "Significant" badge

### 3. Quarterly Breakdown
Each line item tracks surplus per quarter:
- **Q1 Surplus**: Unused budget in Quarter 1 (Jan-Mar)
- **Q2 Surplus**: Unused budget in Quarter 2 (Apr-Jun)
- **Q3 Surplus**: Unused budget in Quarter 3 (Jul-Sep)
- **Q4 Surplus**: Unused budget in Quarter 4 (Oct-Dec)
- **Total Surplus**: Sum of all quarters

### 4. Budget Categories
Line items are grouped by category:
- **Personnel Services** - Salaries, honoraria, overtime
- **MOOE** - Maintenance and Other Operating Expenses
- **Capital Outlays** - Equipment, infrastructure, buildings

---

## Technical Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│              Budget Savings Workflow                     │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  1. Admin Creates Snapshot (Fiscal Year + Quarter)      │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  2. System Creates BudgetSavings Record                 │
│     (Department-level totals - EXISTING)                │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  3. System Creates PRELineItemSavings Records           │
│     (Line item details - NEW FEATURE)                   │
│     - Loop through all approved PREs                    │
│     - Calculate quarterly breakdown for each line item  │
│     - Save only items with surplus > 0                  │
│     - Flag significant items (>₱5,000)                  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  4. Admin Views Line Item Details                       │
│     - Filter by category                                │
│     - Show significant items only                       │
│     - View quarterly breakdown                          │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

```
ApprovedBudget (Fiscal Year)
    ↓
BudgetAllocation (Distributed to Departments)
    ↓
DepartmentPRE (Approved PRE Documents)
    ↓
PRELineItem (Individual Budget Items)
    ├─ Q1, Q2, Q3, Q4 Amounts
    ├─ PR/AD Consumption Tracking
    └─ Remaining Balance per Quarter
        ↓
BudgetSavings (Snapshot - Department Level)
    └─ PRELineItemSavings (NEW - Line Item Level)
        ├─ Quarterly Breakdown
        ├─ Category Grouping
        └─ Significance Flag
```

---

## User Guide

### Accessing the Feature

1. **Login** as Admin
2. **Navigate** to Budget Savings:
   - Sidebar → Budget Management → Savings Overview
   - URL: `/admin/savings/`

### Creating a Snapshot with Line Items

**Step 1**: Click "Create Snapshot" button

**Step 2**: Fill in the form
- **Fiscal Year**: Select (e.g., "2025-2026")
- **Quarter**: Select Q1, Q2, Q3, Q4, or Full Year
- **Notes**: Optional description

**Step 3**: Submit

**Result**:
```
✅ Successfully created 5 savings snapshot(s) for fiscal year 2025-2026.
   Captured 127 line items with surplus.
```

### Viewing Line Item Details

**Step 1**: On Savings Overview page, find a recent snapshot

**Step 2**: Click "View Line Items" button
- Only appears if snapshot has line item data

**Step 3**: Explore the breakdown
- See quarterly surplus per line item
- Filter by category (Personnel, MOOE, Capital)
- Show only significant items (>₱5,000)

### Understanding the Display

#### Summary Cards
```
┌──────────────────────┐  ┌──────────────────────┐
│ Total Allocated      │  │ Total Used           │
│ ₱500,000            │  │ ₱350,000            │
└──────────────────────┘  └──────────────────────┘

┌──────────────────────┐  ┌──────────────────────┐
│ Total Surplus        │  │ Significant Surplus  │
│ ₱150,000            │  │ 8 items              │
│                      │  │ Items >₱5,000        │
└──────────────────────┘  └──────────────────────┘
```

#### Category Breakdown
Shows surplus grouped by budget category:
```
┌──────────────────────────────────────┐
│ Personnel Services                    │
│ ₱25,000                              │
│ 3 items                              │
│                          [View →]    │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ MOOE                                  │
│ ₱98,000                              │
│ 45 items                             │
│                          [View →]    │
└──────────────────────────────────────┘
```

#### Line Items Table
Displays detailed quarterly breakdown:

| Line Item | Category | Q1 | Q2 | Q3 | Q4 | Total | Procurable |
|-----------|----------|----|----|----|----|-------|------------|
| Office Supplies | MOOE | ₱200 | ₱300 | ₱200 | ₱100 | ₱800 | Yes |
| **ICT Equipment** | **MOOE** | ₱0 | ₱0 | **₱18,000** | ₱0 | **₱18,000** 🟡 | Yes |

🟡 = Significant surplus badge

### Filtering Options

**By Category**:
- All Categories
- Personnel Services
- MOOE
- Capital Outlays

**By Significance**:
- ☑ Significant only (>₱5,000)

---

## Administrator Guide

### Configuration

#### Adjusting the Significance Threshold

**File**: `apps/admin_panel/views.py` (line 5350)

**Current Setting**:
```python
SURPLUS_THRESHOLD = Decimal('5000.00')  # ₱5,000
```

**To Change**:
```python
# For ₱10,000 threshold
SURPLUS_THRESHOLD = Decimal('10000.00')

# For ₱3,000 threshold
SURPLUS_THRESHOLD = Decimal('3000.00')
```

**Restart required**: Yes (restart Django server after changing)

#### Disabling Line Item Tracking

If you need to disable the feature:

**File**: `apps/admin_panel/views.py` (line 5349)

```python
# Disable
ENABLE_LINE_ITEM_SAVINGS = False

# Enable (default)
ENABLE_LINE_ITEM_SAVINGS = True
```

**Effect**:
- Snapshots will still be created
- Line items won't be tracked
- Existing line item data remains intact

### Django Admin Access

**URL**: `/admin/budgets/prelineitemsavings/`

**Features**:
- View all line item savings records
- Filter by category, significance, procurable
- Search by item name
- Export to CSV

**List Columns**:
- Item Name
- Category
- Subcategory
- Total Surplus
- Is Significant
- Is Procurable
- Budget Snapshot
- Created At

### Monitoring & Maintenance

#### Check Snapshot Success
```python
from apps.budgets.models import BudgetSavings

# Get latest snapshot
latest = BudgetSavings.objects.latest('snapshot_date')

# Check line items created
line_item_count = latest.line_item_breakdowns.count()
print(f"Line items captured: {line_item_count}")

# Check significant items
significant = latest.line_item_breakdowns.filter(is_significant=True).count()
print(f"Significant items: {significant}")
```

#### View Error Logs
If line item creation fails, check logs:
```bash
# In Django logs
WARNING: Line item savings creation failed for allocation 123: <error>
```

**Note**: Main snapshot still succeeds even if line items fail (by design).

---

## Database Schema

### Table: `budgets_prelineitemsavings`

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | BigAutoField | Primary key |
| `budget_savings_id` | ForeignKey | Link to parent snapshot |
| `pre_line_item_id` | ForeignKey | Link to original PRE line item (nullable) |
| `category` | CharField(255) | Budget category name |
| `subcategory` | CharField(255) | Subcategory (optional) |
| `item_name` | CharField(255) | Line item name |
| `q1_allocated` | Decimal(15,2) | Q1 allocated amount |
| `q1_consumed` | Decimal(15,2) | Q1 consumed (PR+AD) |
| `q1_surplus` | Decimal(15,2) | Q1 unused amount |
| `q2_allocated` | Decimal(15,2) | Q2 allocated amount |
| `q2_consumed` | Decimal(15,2) | Q2 consumed (PR+AD) |
| `q2_surplus` | Decimal(15,2) | Q2 unused amount |
| `q3_allocated` | Decimal(15,2) | Q3 allocated amount |
| `q3_consumed` | Decimal(15,2) | Q3 consumed (PR+AD) |
| `q3_surplus` | Decimal(15,2) | Q3 unused amount |
| `q4_allocated` | Decimal(15,2) | Q4 allocated amount |
| `q4_consumed` | Decimal(15,2) | Q4 consumed (PR+AD) |
| `q4_surplus` | Decimal(15,2) | Q4 unused amount |
| `total_allocated` | Decimal(15,2) | Total allocated |
| `total_consumed` | Decimal(15,2) | Total consumed |
| `total_surplus` | Decimal(15,2) | Total surplus |
| `is_procurable` | Boolean | Requires procurement? |
| `is_significant` | Boolean | Surplus >₱5,000? |
| `created_at` | DateTime | Record creation timestamp |

#### Indexes

1. `idx_budget_savings_category` - For filtering by snapshot and category
2. `idx_total_surplus` - For ordering by surplus amount
3. `idx_is_significant` - For filtering significant items

#### Relationships

```sql
-- Parent snapshot
FOREIGN KEY (budget_savings_id)
  REFERENCES budgets_budgetsavings(id)
  ON DELETE CASCADE

-- Original line item (optional)
FOREIGN KEY (pre_line_item_id)
  REFERENCES budgets_prelineitem(id)
  ON DELETE SET NULL
```

### Sample Query

```python
from apps.budgets.models import PRELineItemSavings

# Get all significant surplus items for a snapshot
significant_items = PRELineItemSavings.objects.filter(
    budget_savings_id=123,
    is_significant=True
).order_by('-total_surplus')

# Get MOOE category surplus
mooe_surplus = PRELineItemSavings.objects.filter(
    budget_savings_id=123,
    category='Maintenance and Other Operating Expenses'
).aggregate(total=Sum('total_surplus'))
```

---

## API Reference

### Views

#### 1. `line_item_savings_detail`

**File**: `apps/admin_panel/views.py:5607`

**URL**: `/admin/savings/<snapshot_id>/line-items/`

**Method**: GET

**Parameters**:
- `snapshot_id` (path) - BudgetSavings ID
- `category` (query) - Filter by category (optional)
- `significant` (query) - Show significant only (true/false)

**Returns**: Rendered template with line item data

**Example**:
```
GET /admin/savings/45/line-items/
GET /admin/savings/45/line-items/?category=MOOE
GET /admin/savings/45/line-items/?significant=true
GET /admin/savings/45/line-items/?category=MOOE&significant=true
```

**Context Variables**:
```python
{
    'snapshot': BudgetSavings object,
    'line_items': QuerySet of PRELineItemSavings,
    'category_summary': Category aggregation,
    'all_categories': List of categories,
    'category_filter': Current filter,
    'show_significant_only': Boolean,
    'total_line_items': Count,
    'total_surplus_all': Decimal,
    'significant_count': Count,
}
```

### Models

#### PRELineItemSavings

**File**: `apps/budgets/models.py:1729`

**Properties**:
```python
@property
def utilization_rate(self):
    """Calculate utilization percentage"""
    return (total_consumed / total_allocated) * 100

@property
def surplus_rate(self):
    """Calculate surplus percentage"""
    return (total_surplus / total_allocated) * 100
```

**Methods**:
```python
def get_quarter_data(self, quarter):
    """
    Get data for specific quarter.

    Args:
        quarter (str): 'Q1', 'Q2', 'Q3', or 'Q4'

    Returns:
        dict: {
            'allocated': Decimal,
            'consumed': Decimal,
            'surplus': Decimal,
            'utilization': float
        }
    """
```

---

## Configuration

### Environment Variables

None required - feature uses Django settings.

### Feature Flags

#### ENABLE_LINE_ITEM_SAVINGS
- **Location**: `apps/admin_panel/views.py:5349`
- **Type**: Boolean
- **Default**: `True`
- **Purpose**: Enable/disable line item tracking

#### SURPLUS_THRESHOLD
- **Location**: `apps/admin_panel/views.py:5350`
- **Type**: Decimal
- **Default**: `Decimal('5000.00')`
- **Purpose**: Threshold for "significant" surplus

### Performance Settings

**Database Indexes**: Automatically created by migration

**Query Optimization**:
- Uses `select_related()` for foreign keys
- Uses `aggregate()` for totals
- Filters applied before loading data

**Recommended for Large Datasets** (>10,000 line items):
```python
# Add to settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}

# Cache category summary for 5 minutes
from django.core.cache import cache
cache.set(f'category_summary_{snapshot_id}', category_summary, 300)
```

---

## Troubleshooting

### Issue: Line items not created

**Symptoms**:
- Snapshot created successfully
- "View Line Items" button not showing
- Message says "0 line items captured"

**Possible Causes**:
1. **No approved PREs**: System only tracks approved PREs
2. **No surplus**: All budget fully consumed
3. **Feature disabled**: `ENABLE_LINE_ITEM_SAVINGS = False`
4. **Error in line item creation**: Check logs

**Solutions**:
```python
# Check if PREs exist
from apps.budgets.models import DepartmentPRE
pres = DepartmentPRE.objects.filter(
    budget_allocation__approved_budget__fiscal_year='2025-2026',
    status='Approved'
)
print(f"Approved PREs: {pres.count()}")

# Check for surplus
for pre in pres:
    for item in pre.line_items.all():
        surplus = item.get_quarter_available('Q1')
        if surplus > 0:
            print(f"{item.item_name}: Q1 surplus = {surplus}")

# Check feature flag
from apps.admin_panel import views
print(f"Feature enabled: {views.ENABLE_LINE_ITEM_SAVINGS}")
```

### Issue: Incorrect surplus amounts

**Symptoms**: Surplus doesn't match expected values

**Check**:
1. **PR/AD status**: Only non-rejected requests count as "consumed"
2. **Quarter allocation**: Verify Q1-Q4 amounts in PRE line items
3. **Calculation method**: Uses `get_quarter_breakdown()` from PRELineItem

**Debug**:
```python
from apps.budgets.models import PRELineItem

item = PRELineItem.objects.get(id=123)

# Check quarterly breakdown
for quarter in ['Q1', 'Q2', 'Q3', 'Q4']:
    data = item.get_quarter_breakdown(quarter)
    print(f"{quarter}:")
    print(f"  Allocated: {data['original']}")
    print(f"  PR Used: {data['pr_consumed']}")
    print(f"  AD Used: {data['ad_consumed']}")
    print(f"  Total Used: {data['total_consumed']}")
    print(f"  Available: {data['available']}")
```

### Issue: Performance slow with many line items

**Symptoms**: Page takes >5 seconds to load

**Solutions**:

1. **Add pagination** to line items table:
```python
from django.core.paginator import Paginator

paginator = Paginator(line_items, 50)  # 50 items per page
page_number = request.GET.get('page')
page_obj = paginator.get_page(page_number)
```

2. **Use database aggregation**:
```python
# Instead of looping in Python
total = sum(item.total_surplus for item in line_items)  # Slow

# Use database aggregation
total = line_items.aggregate(Sum('total_surplus'))['total_surplus__sum']  # Fast
```

3. **Add database indexes** (already done):
```python
class Meta:
    indexes = [
        models.Index(fields=['budget_savings', 'category']),
        models.Index(fields=['-total_surplus']),
    ]
```

---

## Testing Guide

### Manual Testing Checklist

#### Snapshot Creation
- [ ] Create snapshot for fiscal year with data
- [ ] Verify success message shows line item count
- [ ] Check "View Line Items" button appears
- [ ] Create snapshot for fiscal year without data
- [ ] Verify graceful handling (no line items message)

#### Line Item Detail View
- [ ] Access detail page from snapshot
- [ ] Verify summary cards display correctly
- [ ] Check category breakdown cards
- [ ] Test category filter
- [ ] Test "Significant only" filter
- [ ] Verify quarterly columns display
- [ ] Check color coding (green/yellow)
- [ ] Test "Significant" badge display

#### Data Accuracy
- [ ] Compare line item surplus with PRE line item
- [ ] Verify quarterly amounts match
- [ ] Check total surplus calculation
- [ ] Verify significant flag (>₱5,000)
- [ ] Confirm category grouping correct

#### Error Handling
- [ ] Access non-existent snapshot ID → 404
- [ ] Filter by non-existent category → empty result
- [ ] Snapshot without line items → friendly message

### Automated Testing

```python
# test_line_item_savings.py
from django.test import TestCase
from apps.budgets.models import BudgetSavings, PRELineItemSavings
from decimal import Decimal

class LineItemSavingsTestCase(TestCase):

    def test_significant_flag(self):
        """Test that significant flag is set correctly"""
        # Create item with ₱3,000 surplus
        item1 = PRELineItemSavings.objects.create(
            total_surplus=Decimal('3000.00'),
            # ... other fields
        )
        self.assertFalse(item1.is_significant)

        # Create item with ₱6,000 surplus
        item2 = PRELineItemSavings.objects.create(
            total_surplus=Decimal('6000.00'),
            # ... other fields
        )
        self.assertTrue(item2.is_significant)

    def test_utilization_rate(self):
        """Test utilization rate calculation"""
        item = PRELineItemSavings.objects.create(
            total_allocated=Decimal('100000.00'),
            total_consumed=Decimal('75000.00'),
            total_surplus=Decimal('25000.00'),
        )
        self.assertEqual(item.utilization_rate, Decimal('75.0'))
```

---

## FAQ

### Q: Can I change the ₱5,000 threshold?
**A**: Yes! Edit `SURPLUS_THRESHOLD` in `apps/admin_panel/views.py:5350`

### Q: Why are some snapshots missing line items?
**A**: Line items are only created if:
1. PRE is approved
2. Line item has surplus >₱0
3. Feature is enabled

### Q: Can I delete line item data?
**A**: Yes, via Django Admin. Line items are linked to snapshots, so deleting a snapshot deletes its line items (CASCADE).

### Q: Does this affect existing snapshots?
**A**: No! Existing snapshots created before this feature was added won't have line items. Only new snapshots will.

### Q: How do I export line item data?
**A**: Currently via Django Admin (`/admin/budgets/prelineitemsavings/` → Actions → Export as CSV). Custom Excel export can be added.

### Q: Can I view line items for old snapshots?
**A**: Only if they were created after this feature was implemented. Old snapshots won't have line item data.

---

## Version History

### Version 1.0 (November 17, 2025)
- ✅ Initial release
- ✅ PRELineItemSavings model
- ✅ Quarterly breakdown tracking
- ✅ Significant surplus flagging (₱5,000 threshold)
- ✅ Category grouping
- ✅ Line item detail view
- ✅ Filtering by category and significance
- ✅ Django Admin integration

### Planned Enhancements
- [ ] Excel export for line items
- [ ] Configurable threshold via UI
- [ ] Trend analysis (compare snapshots)
- [ ] Automated alerts for significant surplus
- [ ] Reallocation workflow integration

---

## Support & Contact

**For Technical Issues**:
- Check Django logs: `logs/django.log`
- Check error messages in UI
- Review this documentation

**For Feature Requests**:
- Document use case
- Describe expected behavior
- Provide examples

**For Questions**:
- Refer to [Key Concepts](#key-concepts) section
- Check [Troubleshooting](#troubleshooting) guide
- Review [FAQ](#faq)

---

## Appendix

### Complete File List

**Modified Files** (5):
1. `apps/budgets/models.py` - Added PRELineItemSavings model
2. `apps/budgets/admin.py` - Registered model in admin
3. `apps/admin_panel/views.py` - Added/updated views
4. `apps/admin_panel/urls.py` - Added URL route
5. `apps/admin_panel/templates/admin_panel/savings_overview.html` - Added button

**Created Files** (2):
1. `apps/budgets/migrations/0018_prelineitemsavings.py` - Database migration
2. `apps/admin_panel/templates/admin_panel/line_item_savings_detail.html` - Detail template

### Code Statistics
- **Total Lines Added**: ~600
- **Models Created**: 1
- **Views Created**: 1
- **Templates Created**: 1
- **URL Patterns Added**: 1
- **Database Tables**: 1
- **Database Indexes**: 3

---

**Document End**

*Last Updated: November 17, 2025*
*Documentation Version: 1.0*
