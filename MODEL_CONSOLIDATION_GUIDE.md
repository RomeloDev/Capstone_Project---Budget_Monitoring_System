# Model Consolidation Guide

## Critical Issue: Duplicate Models Detected

### Overview
Multiple Django models are duplicated across different apps, which can cause:
- Database migration conflicts
- Data inconsistencies
- Maintenance nightmares
- Import confusion
- Potential bugs

### Duplicate Models Identified

| Model Name | Primary Location | Duplicate Locations |
|-----------|-----------------|-------------------|
| ApprovedBudget | apps/budgets/models.py:58 | apps/admin_panel/models.py:39 |
| BudgetAllocation | apps/budgets/models.py:184 | apps/admin_panel/models.py:63 |
| PurchaseRequest | apps/budgets/models.py:478 | apps/end_user_app/models.py:9 |
| DepartmentPRE | apps/budgets/models.py:241 | apps/end_user_app/models.py:170 |
| ActivityDesign | apps/budgets/models.py:724 | apps/end_user_app/models.py:257 |
| PurchaseRequestAllocation | apps/budgets/models.py:1096 | apps/end_user_app/models.py:87 |

### Consolidation Strategy

**Decision:** Keep `apps/budgets/models.py` as the single source of truth because:
1. Most comprehensive implementation
2. Includes archive functionality
3. Has better documentation
4. More complete field definitions

### Step-by-Step Consolidation Process

#### Phase 1: Preparation (DO THIS FIRST)

1. **Create a Full Backup**
   ```bash
   # Backup database
   python manage.py dumpdata > backup_$(date +%Y%m%d_%H%M%S).json

   # Commit current state to git
   git add .
   git commit -m "Backup before model consolidation"
   git branch model-consolidation-backup
   ```

2. **Document Current Imports**
   ```bash
   # Find all imports of duplicate models
   grep -r "from apps.admin_panel.models import" apps/
   grep -r "from apps.end_user_app.models import" apps/
   grep -r "from admin_panel.models import" apps/
   grep -r "from end_user_app.models import" apps/
   ```

3. **Test Current System**
   ```bash
   python manage.py check
   python manage.py makemigrations --dry-run
   ```

#### Phase 2: Update Imports (Critical)

**Files to Update:**

1. **apps/admin_panel/views.py** (5,236 lines)
   - Find: `from .models import ApprovedBudget, BudgetAllocation`
   - Replace: `from apps.budgets.models import ApprovedBudget, BudgetAllocation`

2. **apps/admin_panel/forms.py**
   - Update all model imports

3. **apps/admin_panel/admin.py**
   - Update all model imports

4. **apps/end_user_app/views.py** (6,024 lines)
   - Find: `from .models import PurchaseRequest, DepartmentPRE, ActivityDesign`
   - Replace: `from apps.budgets.models import PurchaseRequest, DepartmentPRE, ActivityDesign`

5. **apps/end_user_app/forms.py**
   - Update all model imports

6. **apps/end_user_app/admin.py**
   - Update all model imports

7. **apps/approving_officer_app/views.py**
   - Verify imports are already using apps.budgets.models

8. **All template files**
   - Check for any model references
   - Update if necessary

#### Phase 3: Remove Duplicate Models

**IMPORTANT: Only do this after ALL imports are updated!**

1. **Edit apps/admin_panel/models.py**
   - Remove: `ApprovedBudget` class (lines 39-61)
   - Remove: `BudgetAllocation` class (lines 63-77)
   - Keep: `Budget` class (legacy, check if used)
   - Keep: `AuditTrail` class (unique to admin_panel)

2. **Edit apps/end_user_app/models.py**
   - Remove: `PurchaseRequest` class (lines 9-65)
   - Remove: `DepartmentPRE` class (lines 170-256)
   - Remove: `ActivityDesign` class (lines 257-301)
   - Remove: `PurchaseRequestAllocation` class (lines 87-107)
   - Keep unique models: `Budget_Realignment`, `Session`, `FundsAvailable`, etc.

#### Phase 4: Database Migrations

```bash
# After removing duplicate models, create migrations
python manage.py makemigrations

# Review the migration files carefully!
# Django should detect that models were moved, not deleted

# If Django thinks models are being deleted, you may need to:
# 1. Create a custom migration
# 2. Use db_table in Meta to preserve existing tables
# 3. Or manually edit migration files

# Apply migrations
python manage.py migrate --fake-initial  # If tables already exist
```

#### Phase 5: Testing

1. **Run Django checks**
   ```bash
   python manage.py check
   python manage.py check --deploy
   ```

2. **Test each feature**
   - Budget creation
   - PRE submission
   - PR creation
   - AD creation
   - Approval workflows
   - Archive functionality

3. **Check admin interface**
   - Verify all models appear correctly
   - Test CRUD operations

4. **Run server and test manually**
   ```bash
   python manage.py runserver
   ```

#### Phase 6: Verification

```bash
# Check for any remaining old imports
grep -r "from apps.admin_panel.models import ApprovedBudget" .
grep -r "from apps.end_user_app.models import PurchaseRequest" .
grep -r "from apps.end_user_app.models import DepartmentPRE" .

# Should return no results if successful
```

### Alternative: Use db_table to Maintain Compatibility

If migration is too risky, you can keep duplicate model definitions but ensure they point to the same database table:

```python
# In apps/admin_panel/models.py
from apps.budgets.models import ApprovedBudget as BudgetsApprovedBudget
from apps.budgets.models import BudgetAllocation as BudgetsBudgetAllocation

# Create proxy models or aliases
ApprovedBudget = BudgetsApprovedBudget
BudgetAllocation = BudgetsBudgetAllocation
```

This is a **temporary solution** and should eventually be refactored to use direct imports.

### Recommended Approach

Given the complexity and risk:

1. **Short-term (Immediate):**
   - Create this documentation
   - Add TODO comments in code
   - Use import aliases to reduce duplication

2. **Medium-term (Next Sprint):**
   - Create a separate git branch
   - Follow phases 1-6 above
   - Test thoroughly in development
   - Get team review before merging

3. **Long-term:**
   - Implement comprehensive test suite first
   - Then consolidate models
   - Consider microservices if complexity grows

### Risk Assessment

**High Risk:**
- Breaking existing functionality
- Data loss if migrations go wrong
- Import errors across the codebase

**Mitigation:**
- Always backup database first
- Work on a separate git branch
- Test thoroughly before deployment
- Consider rolling out in stages

### Checklist Before Starting

- [ ] Full database backup created
- [ ] Git branch created
- [ ] All team members notified
- [ ] Development environment ready
- [ ] Testing plan prepared
- [ ] Rollback plan documented
- [ ] At least 4 hours allocated for the work

### Emergency Rollback

If something goes wrong:

```bash
# Restore from backup
git checkout main
git branch -D model-consolidation

# Restore database
python manage.py flush
python manage.py loaddata backup_YYYYMMDD_HHMMSS.json

# Restart server
python manage.py runserver
```

### Support

If you encounter issues:
1. Check Django documentation on migrations
2. Review git diff to see what changed
3. Test in small increments
4. Don't skip the backup step!

---

**Status:** PENDING - Requires careful execution
**Priority:** HIGH - But needs proper planning
**Estimated Time:** 4-8 hours
**Risk Level:** HIGH
