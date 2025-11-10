# Archive Feature Documentation

## Overview

The Archive Feature provides a comprehensive soft-delete system for the Budget Monitoring System. Instead of permanently deleting data, records are archived and can be restored later. This ensures data integrity, maintains audit trails, and allows historical data preservation.

---

## Features

### 1. **Fiscal Year Archive**
- Archive entire fiscal years with one action
- Cascading archive to all related records (allocations, PREs, PRs, ADs)
- Automatic archiving on January 1st
- Manual archive/unarchive via Archive Center

### 2. **Selective Archive (Soft-Delete)**
- User account archiving (instead of deletion)
- Individual record archiving
- Easy restoration from Archive Center

### 3. **View-Only Access for End Users**
- End users can view archived records (read-only)
- Archived records clearly marked with badges
- Forms disabled for archived records
- Archive banners with detailed information

### 4. **Admin Management**
- Archive Center dashboard
- Statistics and reports
- Archive/Unarchive with required reasons
- Full audit trail logging

---

## Architecture

### Database Schema

#### Archive Fields (Added to 6 Models)

**Models with Archive Support:**
1. `ApprovedBudget`
2. `BudgetAllocation`
3. `DepartmentPRE`
4. `PurchaseRequest`
5. `ActivityDesign`
6. `User`

**Archive Fields:**
```python
is_archived = BooleanField(default=False, db_index=True)
archived_at = DateTimeField(null=True, blank=True)
archived_by = ForeignKey(User, ...)
archive_reason = TextField(blank=True)
archive_type = CharField(choices=[('FISCAL_YEAR', 'MANUAL')])
```

### Custom Managers

```python
# Default: Excludes archived records
Model.objects.all()  # Returns only active records

# Get only archived
Model.objects.archived()

# Get all (including archived)
Model.all_objects.all()
```

---

## Usage Guide

### For Administrators

#### Accessing Archive Center
1. Navigate to Admin Panel
2. Click "Archive Center" in the sidebar
3. View fiscal years and their archive status

#### Archiving a Fiscal Year
1. In Archive Center, find the fiscal year
2. Click "Archive" button
3. Enter reason for archiving (required)
4. Click "Confirm Archive"
5. All related records are archived automatically

#### Unarchiving a Fiscal Year
1. In Archive Center, find the archived fiscal year
2. Click "Restore" button
3. Enter reason for unarchiving (required)
4. Click "Confirm Restore"
5. All related records are restored

#### Archiving a User Account
1. Navigate to User Management
2. Click "Delete" on a user
3. User is archived (not deleted)
4. Can be restored from Archive Center

### For End Users

#### Viewing Archived Records
- Archived records show with purple "ARCHIVED" badge
- Archive banner displayed at top of page
- All form fields disabled
- Cannot submit new documents for archived records

#### Requesting Unarchive
- Contact your administrator
- Provide reason for restore request
- Admin can restore from Archive Center

---

## Automatic Archiving

### Setup

#### Windows (Task Scheduler)
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily, January 1st, 2:00 AM
4. Action: Start a program
   - Program: `python`
   - Arguments: `manage.py auto_archive_fiscal_year`
   - Start in: `C:\path\to\project`

#### Linux (Cron)
```bash
# Edit crontab
crontab -e

# Add this line (runs Jan 1st at 2 AM)
0 2 1 1 * cd /path/to/project && python manage.py auto_archive_fiscal_year
```

### Manual Execution
```bash
# Dry run (no actual archiving)
python manage.py auto_archive_fiscal_year --year 2023 --dry-run

# Archive specific year
python manage.py auto_archive_fiscal_year --year 2023 --force

# Skip email notifications
python manage.py auto_archive_fiscal_year --year 2023 --no-email
```

---

## Management Commands

### 1. Auto Archive Fiscal Year
```bash
python manage.py auto_archive_fiscal_year [options]

Options:
  --dry-run          Run without making changes
  --force            Run regardless of date
  --year YEAR        Archive specific year
  --no-email         Skip email notifications
```

### 2. Create Test Data
```bash
python manage.py create_archive_test_data [options]

Options:
  --years YEARS      Comma-separated years (default: 2021,2022,2023,2024,2025)
  --clear            Clear existing test data first
```

---

## API Reference

### Archive Service Functions

#### `archive_fiscal_year(fiscal_year, archived_by, reason, archive_type='FISCAL_YEAR')`
Archive an entire fiscal year with cascading.

**Parameters:**
- `fiscal_year` (str): Fiscal year to archive (e.g., "2023")
- `archived_by` (User|None): User performing action (None for system)
- `reason` (str): Reason for archiving
- `archive_type` (str): 'FISCAL_YEAR' or 'MANUAL'

**Returns:** Dictionary with counts of archived records

**Raises:** ValueError, Exception

**Example:**
```python
from apps.budgets.services import archive_fiscal_year

counts = archive_fiscal_year(
    fiscal_year='2023',
    archived_by=request.user,
    reason='End of fiscal year',
    archive_type='FISCAL_YEAR'
)
# Returns: {'approved_budgets': 1, 'budget_allocations': 5, ...}
```

#### `unarchive_fiscal_year(fiscal_year, unarchived_by, reason)`
Restore an archived fiscal year.

**Parameters:**
- `fiscal_year` (str): Fiscal year to restore
- `unarchived_by` (User): User performing action (required)
- `reason` (str): Reason for unarchiving (required)

**Returns:** Dictionary with counts of restored records

**Example:**
```python
from apps.budgets.services import unarchive_fiscal_year

counts = unarchive_fiscal_year(
    fiscal_year='2023',
    unarchived_by=request.user,
    reason='Need to make corrections'
)
```

#### `archive_record(model_class, record_id, archived_by, reason, archive_type='MANUAL')`
Archive a single record.

**Example:**
```python
from apps.budgets.services import archive_record
from apps.users.models import User

archive_record(
    model_class=User,
    record_id=123,
    archived_by=request.user,
    reason='User account inactive',
    archive_type='MANUAL'
)
```

#### `get_archive_statistics()`
Get archive statistics for all models.

**Returns:** Dictionary with active/archived/total counts

**Example:**
```python
from apps.budgets.services import get_archive_statistics

stats = get_archive_statistics()
# Returns: {
#     'ApprovedBudget': {'active': 2, 'archived': 3, 'total': 5},
#     ...
# }
```

---

## Template Tags

### Load Archive Tags
```django
{% load archive_tags %}
```

### Available Tags

#### `{% archive_badge record %}`
Display archive badge if record is archived.

```django
{% load archive_tags %}
{% archive_badge pre_record %}
```

#### `{% archive_status_badge record %}`
Display status badge (Active or Archived).

```django
{% archive_status_badge budget_allocation %}
```

#### `{% archive_banner record user %}`
Display prominent archive warning banner.

```django
{% archive_banner pre_record request.user %}
```

#### `{% disable_if_archived record "class-name" %}`
Add disabled attribute and classes if archived.

```django
<button {% disable_if_archived pre_record %}>Submit</button>
<input {% disable_if_archived record "opacity-50" %} />
```

#### `{{ record|is_archived }}`
Check if record is archived (filter).

```django
{% if record|is_archived %}
    <p>This record is archived</p>
{% endif %}
```

---

## Template Includes

### Archive Banner Include
```django
{% include 'budgets/includes/archive_banner.html' with record=pre_record %}
```

This displays a complete archive warning banner with:
- Archive status icon
- Read-only message
- Archived date and user
- Archive reason
- Link to Archive Center (for admins)

---

## URL Routes

### Archive Management URLs
```python
# Archive Center
/admin/archive/

# Archive fiscal year (POST only)
/admin/archive/fiscal-year/<fiscal_year>/archive/

# Unarchive fiscal year (POST only)
/admin/archive/fiscal-year/<fiscal_year>/unarchive/

# Archive statistics (AJAX)
/admin/archive/statistics/
```

---

## Database Migrations

### Migration Files Created
```
apps/budgets/migrations/
└── 0015_activitydesign_archive_reason_and_more.py

apps/users/migrations/
└── 0011_user_archive_reason_user_archive_type_and_more.py
```

### Rollback
If you need to rollback the migrations:

```bash
# Find previous migration number
python manage.py showmigrations budgets

# Rollback budgets app
python manage.py migrate budgets 0014

# Rollback users app
python manage.py migrate users 0010
```

---

## Security & Permissions

### Access Control
- **Admins Only:** Archive/Unarchive actions
- **End Users:** View-only access to archived records
- **Middleware:** Prevents editing archived records

### Audit Trail
All archive actions are logged to `AuditTrail`:
- User who archived
- Timestamp
- Model and record ID
- Action (ARCHIVE/UNARCHIVE)
- Reason

---

## Troubleshooting

### Issue: Records not appearing after unarchive
**Solution:** Clear browser cache or hard refresh (Ctrl+F5)

### Issue: Cannot archive fiscal year
**Possible Causes:**
1. Fiscal year doesn't exist
2. Already archived
3. Permission denied

**Solution:** Check Archive Center for current status

### Issue: Automatic archive not running
**Solution:**
1. Check cron job / task scheduler is active
2. Verify command path is correct
3. Check system logs for errors
4. Test manually with `--force` flag

### Issue: Email notifications not sending
**Solution:**
1. Check `settings.py` email configuration
2. Verify `DEFAULT_FROM_EMAIL` is set
3. Test with `--no-email` flag first
4. Check SMTP settings

---

## File Structure

```
apps/budgets/
├── managers.py                    # Custom archive managers
├── models.py                      # Updated with archive fields
├── services/
│   ├── __init__.py
│   └── archive_service.py         # Archive business logic
├── middleware.py                  # Archived record protection
├── context_processors.py          # Archive context variables
├── templatetags/
│   ├── __init__.py
│   └── archive_tags.py            # Template tags/filters
├── templates/budgets/includes/
│   └── archive_banner.html        # Reusable banner template
└── management/commands/
    ├── __init__.py
    ├── auto_archive_fiscal_year.py
    └── create_archive_test_data.py

apps/admin_panel/
├── views.py                       # Updated with archive views
├── urls.py                        # Archive routes
└── templates/admin_panel/
    └── archive_center.html        # Archive Center UI

apps/users/
└── models.py                      # Updated with archive fields
```

---

## Testing

### Manual Testing Checklist

- [ ] Archive fiscal year 2023
- [ ] Verify dashboard excludes archived records
- [ ] Check PRE/PR/AD from 2023 are hidden
- [ ] Unarchive fiscal year 2023
- [ ] Verify data reappears
- [ ] Test year filter with archived toggle
- [ ] Archive user account
- [ ] Verify user appears in Archive Center
- [ ] Restore archived user
- [ ] Test end user view-only access
- [ ] Verify forms disabled on archived records
- [ ] Check audit trail logs
- [ ] Test automatic archive (dry-run)
- [ ] Verify email notifications

### Unit Tests
```python
# Run all tests
python manage.py test apps.budgets.tests

# Run specific test
python manage.py test apps.budgets.tests.TestArchiveFeature
```

---

## Performance Considerations

### Indexes
Archive fields are indexed for fast queries:
```python
is_archived = BooleanField(default=False, db_index=True)
```

### Query Optimization
- Use `select_related()` and `prefetch_related()`
- Archive operations wrapped in transactions
- Bulk updates where possible

### Expected Performance
- Archive operation: < 5 seconds for 1 fiscal year
- Dashboard load: No degradation (with index)
- Queryset filtering: < 100ms overhead

---

## Future Enhancements

### Potential Additions
1. **Archive Analytics Dashboard**
   - Storage metrics
   - Archive trends
   - Usage reports

2. **Selective Department Archive**
   - Archive by department
   - Archive by date range

3. **Archive Export**
   - Export to CSV/Excel
   - Backup to external storage

4. **Data Retention Policies**
   - Automatic deletion after X years
   - Compliance features

5. **Advanced Notifications**
   - SMS notifications
   - In-app notifications
   - Archive reminders

---

## Support & Maintenance

### Regular Maintenance
1. Monitor archive growth
2. Review audit trails monthly
3. Test automatic archive annually
4. Backup database before bulk operations

### Getting Help
- Check this documentation first
- Review audit trail for action history
- Contact system administrator
- Submit bug reports to development team

---

## Changelog

### Version 1.0.0 (2025-11-10)
- Initial release
- Fiscal year archive
- Selective archive
- Archive Center UI
- Automatic archiving
- Template tags
- Documentation

---

**Documentation Last Updated:** 2025-11-10
**Feature Version:** 1.0.0
**Author:** Budget Monitoring System Development Team
