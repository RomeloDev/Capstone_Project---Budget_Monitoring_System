# Contributing to BISU Balilihan Budget Monitoring System

First off, thank you for considering contributing to the BISU Balilihan Budget Monitoring System! It's people like you that make this project better for everyone.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing Guidelines](#testing-guidelines)

---

## Code of Conduct

This project and everyone participating in it is governed by our commitment to creating a welcoming and respectful environment. By participating, you are expected to uphold this standard.

### Our Standards

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

---

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the behavior
- **Expected vs actual behavior**
- **Screenshots** if applicable
- **Environment details** (OS, Python version, Django version)
- **Error messages** or stack traces

**Example:**

```markdown
**Bug**: Admin dashboard shows zero values

**Environment**:
- OS: Windows 11
- Python: 3.12.3
- Django: 5.1.6

**Steps to Reproduce**:
1. Login as admin
2. Navigate to dashboard
3. Observe metrics showing 0

**Expected**: Should show actual budget data
**Actual**: All metrics show 0

**Error**: None visible, but query returns None
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear and descriptive title**
- **Provide step-by-step description** of the enhancement
- **Explain why this would be useful**
- **List similar features** in other systems if applicable

### Your First Code Contribution

Unsure where to begin? Look for issues labeled:
- `good first issue` - Simple issues for beginners
- `help wanted` - Issues that need attention
- `bug` - Bug fixes needed
- `enhancement` - New features to implement

---

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/bisu-budget-monitoring.git
cd bisu-budget-monitoring/bb_budget_monitoring_system
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv env
env\Scripts\activate

# Linux/Mac
python3 -m venv env
source env/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Database

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

---

## Coding Standards

### Python Code Style

Follow **PEP 8** guidelines:

```python
# Good
def calculate_total_budget(allocations):
    """
    Calculate total budget from allocations.

    Args:
        allocations (QuerySet): Budget allocation objects

    Returns:
        Decimal: Total allocated amount
    """
    return sum(a.allocated_amount for a in allocations)


# Bad
def calc(a):
    return sum(x.allocated_amount for x in a)
```

### Django Best Practices

1. **Models**
   ```python
   class BudgetAllocation(models.Model):
       """Budget allocations distributed to departments"""

       # Fields with help_text
       allocated_amount = models.DecimalField(
           max_digits=15,
           decimal_places=2,
           help_text="Amount allocated to this department"
       )

       class Meta:
           ordering = ['-created_at']
           verbose_name = "Budget Allocation"
           verbose_name_plural = "Budget Allocations"

       def __str__(self):
           return f"{self.department} - ₱{self.allocated_amount:,.2f}"
   ```

2. **Views**
   ```python
   @role_required('admin', login_url='/admin/')
   def admin_dashboard(request):
       """Admin dashboard with budget analytics"""
       try:
           # Your logic here
           context = {...}
           return render(request, 'template.html', context)
       except Exception as e:
           messages.error(request, f"Error: {e}")
           return redirect('fallback_view')
   ```

3. **Templates**
   - Use semantic HTML
   - Follow Tailwind CSS conventions
   - Add ARIA labels for accessibility
   - Use Django template filters

### File Organization

```
apps/your_app/
├── __init__.py
├── models.py          # Database models
├── views.py           # View functions
├── urls.py            # URL patterns
├── forms.py           # Django forms
├── utils.py           # Utility functions
├── tests.py           # Unit tests
└── templates/
    └── your_app/
        └── template.html
```

### Naming Conventions

- **Variables/Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_CASE`
- **Template files**: `lowercase_with_underscores.html`
- **URLs**: `kebab-case`

---

## Commit Message Guidelines

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

### Examples

```bash
feat(dashboard): add quarterly budget chart

- Added Chart.js integration
- Created quarterly spending visualization
- Updated dashboard template

Closes #123
```

```bash
fix(admin): correct budget total calculation

The admin dashboard was showing incorrect totals due to
field name mismatch. Changed 'total_amount' to 'amount'
to match the ApprovedBudget model.

Fixes #456
```

---

## Pull Request Process

### Before Submitting

1. **Test your changes**
   ```bash
   python manage.py test
   python manage.py check
   ```

2. **Update documentation**
   - Update README.md if needed
   - Add docstrings to new functions
   - Update CHANGELOG.md

3. **Check code style**
   ```bash
   # Optional: Use flake8 or black
   flake8 apps/
   black apps/
   ```

### Submitting

1. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request**
   - Go to the original repository
   - Click "New Pull Request"
   - Select your branch
   - Fill in the PR template

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] All tests pass
- [ ] Added new tests
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] CHANGELOG.md updated

## Screenshots (if applicable)
```

### Review Process

- At least one approval required
- All CI checks must pass
- No merge conflicts
- Documentation updated

---

## Testing Guidelines

### Writing Tests

```python
# apps/budgets/tests.py
from django.test import TestCase
from apps.budgets.models import BudgetAllocation

class BudgetAllocationTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.allocation = BudgetAllocation.objects.create(
            department="IT Department",
            allocated_amount=100000
        )

    def test_get_total_used(self):
        """Test total used calculation"""
        self.allocation.pre_amount_used = 10000
        self.allocation.pr_amount_used = 5000
        self.assertEqual(
            self.allocation.get_total_used(),
            15000
        )
```

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.budgets

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

---

## Questions?

If you have questions, you can:
- Open an issue with the `question` label
- Email: support@bisubalilihan.edu.ph
- Contact the maintainers

---

## Recognition

Contributors will be added to:
- README.md acknowledgments
- CONTRIBUTORS.md file
- Project documentation

Thank you for contributing! 🎉
