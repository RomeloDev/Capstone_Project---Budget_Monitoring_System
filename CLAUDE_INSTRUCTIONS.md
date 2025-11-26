# Archive Feature Improvement Plan

## Context
We are refining the Archive Feature to fix a "Nested State" bug where manually archived items are incorrectly restored when unarchiving a fiscal year. We are also improving the UI/UX to provide better feedback and adding a **new Archive Details Page** to view historical data.

## Architectural Decisions
1.  **Nested State Fix:** We will use the existing `archive_type` field (`FISCAL_YEAR` vs `MANUAL`).
    *   **Archiving:** When archiving a fiscal year, we will ONLY update records that are currently `is_archived=False`. This preserves the state of manually archived records.
    *   **Unarchiving:** When restoring a fiscal year, we will ONLY restore records where `archive_type='FISCAL_YEAR'`. Manually archived records will remain archived.
2.  **Archive Details View:** We will implement a dedicated view `archive_fiscal_year_details` that leverages the `ArchiveManager.fiscal_year_archived` method to fetch and aggregate data for a specific archived year. This ensures we can see a snapshot of the budget state at the time of archiving.
3.  **Performance:** We will continue to use `queryset.update()` for bulk operations as `signals.py` does not contain any search indexing or critical side-effects that require individual `save()` calls for archiving.
4.  **UI Feedback:** We will implement a "Fetch & Show" pattern for the archive modal. Before confirming, we will fetch exact counts of affected items to warn the user.

---

## Phase 1: Service Layer Logic Updates
**File:** `apps/budgets/services/archive_service.py`

### Step 1.1: Update `archive_fiscal_year`
Modify the bulk update queries to **exclude** already archived items.
*   **Current:** `allocations_queryset.update(...)`
*   **New:** `allocations_queryset.filter(is_archived=False).update(...)`
*   **Apply to:** `BudgetAllocation`, `DepartmentPRE`, `PurchaseRequest`, `ActivityDesign`.

### Step 1.2: Update `unarchive_fiscal_year`
Modify the bulk update queries to **only** restore items archived by the fiscal year cascade.
*   **Current:** `allocations.update(is_archived=False, ...)`
*   **New:** `allocations.filter(archive_type='FISCAL_YEAR').update(is_archived=False, ...)`
*   **Apply to:** `BudgetAllocation`, `DepartmentPRE`, `PurchaseRequest`, `ActivityDesign`.

## Phase 2: Archive Details Page (NEW)
**Files:** `apps/admin_panel/views.py`, `apps/admin_panel/urls.py`, `apps/admin_panel/templates/admin_panel/archive_details.html`

### Step 2.1: Create View Logic
Create `archive_fiscal_year_details(request, fiscal_year)` in `views.py`.
*   **Access Control:** `@role_required('admin')`
*   **Data Fetching:**
    *   Get `ApprovedBudget` using `ApprovedBudget.objects.archived().get(fiscal_year=fiscal_year)`.
    *   Get Allocations using `BudgetAllocation.objects.fiscal_year_archived(fiscal_year)`.
    *   Get PREs using `DepartmentPRE.objects.fiscal_year_archived(fiscal_year)`.
    *   Get PRs/ADs similarly.
*   **Aggregation:** Calculate total allocated, total spent (PR+AD), and remaining balance for the archived year.
*   **Context:** Pass `budget`, `allocations`, `pres`, `prs`, `ads`, and `summary_stats` to the template.

### Step 2.2: Create Template
Create `apps/admin_panel/templates/admin_panel/archive_details.html`.
*   **Header:** Show Fiscal Year, Total Budget, and Archive Date/Reason.
*   **Summary Cards:** Total Allocated vs Total Spent.
*   **Tabs/Sections:**
    *   **Allocations:** Table showing department allocations and their final utilization.
    *   **PREs:** List of approved PREs for that year.
    *   **Transactions:** List of PRs and ADs.
*   **Navigation:** "Back to Archive Center" button.

### Step 2.3: Register URL
Add path in `apps/admin_panel/urls.py`:
*   `path('archive/fiscal-year/<str:fiscal_year>/details/', views.archive_fiscal_year_details, name='archive_fiscal_year_details')`

### Step 2.4: Link from Archive Center
Update `archive_center.html` to make the Fiscal Year clickable or add a "View Details" button (e.g., an eye icon) next to the "Restore" button for archived rows.

## Phase 3: Frontend & UX Strategy
**Files:**
*   `apps/admin_panel/templates/admin_panel/archive_center.html`
*   `apps/admin_panel/views.py`

### Step 3.1: Dynamic Modal Statistics
*   **Backend:** Ensure `archive_statistics_ajax` (or a new endpoint) can return stats *for a specific fiscal year* (currently it returns global stats).
    *   *Action:* Modify `archive_statistics_ajax` in `views.py` to accept a `fiscal_year` parameter and return counts for that year (Allocations, PREs, PRs, ADs).
*   **Frontend:** Update `openArchiveModal` in `archive_center.html`:
    1.  Show a "Loading..." state in the modal content.
    2.  Fetch stats from the backend.
    3.  Update the modal text to say: "This will archive **X** Allocations, **Y** PREs, **Z** PRs..."
    4.  Show the "Confirm" button only after data loads.

### Step 3.2: Visual Distinction
*   In the "Archived Records" table (if one exists, or wherever archived items are listed), add a badge:
    *   If `archive_type == 'MANUAL'`: Red Badge "Manually Archived"
    *   If `archive_type == 'FISCAL_YEAR'`: Purple Badge "FY Archived"

## Phase 4: Verification
**Manual Test Script:**
1.  **Nested State:** Archive a PR manually, then archive the FY. Restore the FY. Verify PR remains archived.
2.  **Details Page:** Archive a FY. Click "View Details". Verify all data (allocations, PREs, PRs) is visible and read-only. Check that totals match the state before archiving.
3.  **Modal Stats:** Click "Archive" on a new FY. Verify the modal shows the correct count of items before confirming.
