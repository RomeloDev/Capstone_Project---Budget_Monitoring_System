# Simple Budget Savings Feature - MVP for Capstone Defense

## CONTEXT
I'm a capstone student at BISU Balilihan working on a Django Budget Monitoring System. My defense is on the **2nd week of December 2025** (3 weeks away). I need a **simple, functional MVP** - not an enterprise-grade solution.

## GOAL
Add a basic **Savings Tracking Feature** that shows:
1. Where unused budget comes from (which departments/quarters)
2. How much budget wasn't spent
3. A simple report showing savings

**IMPORTANT**: Keep it simple! I need something that works for my defense, not a production-ready enterprise system.

---

## WHAT I NEED FROM YOU

### Step 1: Quick Analysis (30 minutes max)
Scan my codebase and tell me:

1. **Current Budget Models** - What models handle budget data?
2. **How budget is tracked now** - Where are amounts stored?
3. **Where expenditures are recorded** - What models track spending?
4. **Current calculations** - Is there already any "remaining budget" calculation?

### Step 2: Simple MVP Plan (Keep it minimal!)

Suggest the **SIMPLEST possible way** to add savings tracking:

#### Option A: Use Existing Models
Can I just add a few fields to existing models? Something like:
- Add `unused_amount` field?
- Add `is_saved` boolean flag?
- Add a simple calculation method?

#### Option B: One New Simple Model
If I need a new model, keep it minimal:
```python
class BudgetSavings(models.Model):
    department = ...
    quarter = ...
    original_budget = ...
    spent_amount = ...
    savings_amount = ...  # just original - spent
    date_identified = ...
```

### Step 3: Minimal Implementation (What can I build in 2 weeks?)

Give me a **realistic 2-week plan**:

**Week 1: Core Functionality**
- Day 1-2: Database changes (1 model or a few fields)
- Day 3-4: Basic calculation logic
- Day 5: Simple admin view to see savings

**Week 2: UI & Reports**
- Day 1-3: Simple dashboard showing savings by department
- Day 4-5: Basic Excel/PDF report
- Day 6-7: Testing and bug fixes

---

## WHAT I DON'T NEED

❌ State management systems
❌ Workflow automation
❌ Complex approval chains
❌ Celery/Redis/background jobs
❌ Advanced analytics
❌ Multi-level reconciliation
❌ 250+ unit tests
❌ Enterprise deployment plans

## WHAT I DO NEED

✅ Simple database model(s)
✅ Basic calculation (allocated - spent = savings)
✅ One admin page to view savings
✅ One simple report (Excel or PDF)
✅ Something I can demo in 15 minutes

---

## DELIVERABLES I NEED

1. **Quick Summary** (1 paragraph)
   - Current state of budget tracking
   - Simplest way to add savings

2. **Minimal Code Suggestions**
   - 1 model (or fields to add to existing models)
   - 1-2 simple view functions
   - 1 template for displaying savings

3. **2-Week Implementation Checklist**
   - Day-by-day tasks
   - Keep each task under 4 hours
   - No task should require learning new tech

---

## CONSTRAINTS

- **Time**: 2 weeks (not 10 weeks!)
- **Complexity**: Junior developer level (I'm a student)
- **Tech**: Just Django basics (no Celery, Redis, advanced stuff)
- **Goal**: Working demo for capstone defense
- **Scope**: Track savings, show report - that's it!

---

## OUTPUT FORMAT

Please give me:

```
CURRENT STATE:
- [Brief description of how budget works now]

SIMPLEST SOLUTION:
- [Option A or B - which is easier?]
- [Exact model/fields needed]

2-WEEK PLAN:
Week 1:
- Day 1: [Specific task, <4 hours]
- Day 2: [Specific task, <4 hours]
...

Week 2:
- Day 1: [Specific task, <4 hours]
...

CODE TO START WITH:
[Just the essential model code]

DEMO SCRIPT:
[What to show in defense - 15 minute demo]
```

---

**Remember**: I'm a student with a deadline, not building a production system. Simple and functional beats perfect and incomplete!
