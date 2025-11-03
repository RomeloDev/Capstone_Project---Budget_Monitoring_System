# BISU Balilihan - Budget Monitoring System

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.12.3-blue.svg)
![Django Version](https://img.shields.io/badge/django-5.1.6-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

A comprehensive web-based budget monitoring and management system designed for Bohol Island State University (BISU) - Balilihan Campus.

[Features](#features) • [Installation](#installation) • [Usage](#usage) • [Documentation](#documentation)

</div>

---

## Table of Contents

- [About the Project](#about-the-project)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [User Roles](#user-roles)
- [Core Modules](#core-modules)
- [Database Schema](#database-schema)
- [API Endpoints](#api-endpoints)
- [Screenshots](#screenshots)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)
- [Acknowledgments](#acknowledgments)

---

## About the Project

The **BISU Balilihan Budget Monitoring System** is a capstone project developed to streamline and modernize the budget management processes at Bohol Island State University - Balilihan Campus. The system provides real-time monitoring, tracking, and reporting of budget allocations, expenditures, and financial requests across different departments.

### Problem Statement

Traditional budget management at BISU Balilihan involved:
- Manual tracking of budget allocations and expenditures
- Paper-based document processing
- Difficulty in real-time budget monitoring
- Lack of centralized data management
- Time-consuming approval workflows

### Solution

This system provides:
- ✅ Centralized budget tracking and monitoring
- ✅ Digital document management
- ✅ Automated workflow approvals
- ✅ Real-time budget utilization reports
- ✅ Multi-level user access control
- ✅ Comprehensive audit trails
- ✅ Excel/PDF report generation

---

## Features

### 🎯 Core Features

#### For Administrators
- **Dashboard Analytics**: Real-time overview of system-wide budget status
- **Budget Allocation Management**: Create and distribute approved budgets to departments
- **Document Review**: Review and approve/reject PRE, PR, and AD submissions
- **User Management**: Manage end users and approving officers
- **Audit Trail**: Complete history of all system actions
- **Report Generation**: Export comprehensive budget reports

#### For End Users (Department Heads)
- **Budget Overview**: View allocated budget and current utilization
- **PRE Submission**: Submit Program of Receipts and Expenditures via Excel upload
- **Purchase Requests**: Create and submit procurement requests
- **Activity Designs**: Submit activity/event budget proposals
- **Real-time Tracking**: Monitor approval status and budget consumption
- **Quarterly Analysis**: View budget breakdown by quarter
- **Document History**: Access all submitted documents

#### For Approving Officers
- **Approval Dashboard**: Centralized view of pending requests
- **Document Review**: Review PRE, PR, and AD documents with details
- **Partial Approval**: Approve specific line items while rejecting others
- **Scanned Document Upload**: Upload signed/approved documents
- **Notification System**: Alerts for new submissions

### 📊 Document Types

1. **PRE (Program of Receipts and Expenditures)**
   - Excel-based budget planning documents
   - Quarterly budget breakdown
   - Line item categorization
   - Automatic validation against allocated budget

2. **PR (Purchase Request)**
   - Procurement item requests
   - Linked to approved PRE line items
   - Supporting document attachments
   - Multi-stage approval workflow

3. **AD (Activity Design)**
   - Event/activity budget proposals
   - Detailed activity descriptions
   - Budget justifications
   - Document upload support

### 🔐 Security Features

- Role-based access control (RBAC)
- Password encryption
- Session management
- Audit logging
- CSRF protection
- File upload validation

---

## Technology Stack

### Backend
- **Framework**: Django 5.1.6
- **Language**: Python 3.12.3
- **Database**: PostgreSQL / MySQL (configurable)
- **ORM**: Django ORM

### Frontend
- **CSS Framework**: Tailwind CSS 3.8.0
- **Template Engine**: Django Templates
- **JavaScript**: Vanilla JS + Chart.js
- **Icons**: Heroicons

### Libraries & Tools
- **Excel Processing**: openpyxl, pandas, xlwings
- **PDF Generation**: ReportLab
- **Document Processing**: python-docx, docxcompose
- **Admin Interface**: Django Jazzmin
- **Development**: django-browser-reload

### Third-party Services
- **Charts**: Chart.js 4.4.0
- **Date Formatting**: Humanize filters

---

## System Architecture

```
bb_budget_monitoring_system/
├── apps/
│   ├── admin_panel/          # Admin dashboard and management
│   │   ├── templates/
│   │   ├── models.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   ├── budgets/              # Core budget management (NEW models)
│   │   ├── models.py         # ApprovedBudget, BudgetAllocation, DepartmentPRE
│   │   ├── views.py          # PurchaseRequest, ActivityDesign
│   │   └── ...
│   │
│   ├── end_user_app/         # End user interface
│   │   ├── templates/
│   │   │   └── end_user_app/
│   │   │       ├── dashboard.html
│   │   │       ├── budget_overview.html
│   │   │       ├── quarterly_analysis.html
│   │   │       └── ...
│   │   ├── models.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   └── users/                # User authentication & management
│       ├── models.py         # Custom User model
│       ├── views.py
│       └── utils.py          # Role decorators
│
├── theme/                    # Tailwind CSS configuration
│   └── static/
│       └── css/
│
├── bb_budget_monitoring_system/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── manage.py
├── requirements.txt
└── README.md
```

---

## Installation

### Prerequisites

- Python 3.12.3 or higher
- PostgreSQL 13+ or MySQL 8+
- pip (Python package manager)
- Git
- Virtual environment (recommended)

### Step-by-Step Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/bisu-balilihan-budget-monitoring.git
cd bisu-balilihan-budget-monitoring/bb_budget_monitoring_system
```

#### 2. Create Virtual Environment

**Windows:**
```bash
python -m venv env
env\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv env
source env/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Database Setup

**Option A: PostgreSQL (Recommended)**
```bash
# Create database
psql -U postgres
CREATE DATABASE bisu_budget_db;
CREATE USER bisu_admin WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE bisu_budget_db TO bisu_admin;
\q
```

**Option B: MySQL**
```bash
mysql -u root -p
CREATE DATABASE bisu_budget_db;
CREATE USER 'bisu_admin'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON bisu_budget_db.* TO 'bisu_admin'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 5. Configure Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_ENGINE=django.db.backends.postgresql  # or mysql
DATABASE_NAME=bisu_budget_db
DATABASE_USER=bisu_admin
DATABASE_PASSWORD=your_password
DATABASE_HOST=localhost
DATABASE_PORT=5432  # 3306 for MySQL
ALLOWED_HOSTS=localhost,127.0.0.1
```

#### 6. Update Settings

Edit `bb_budget_monitoring_system/settings.py`:

```python
# Database configuration
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DATABASE_ENGINE'),
        'NAME': os.getenv('DATABASE_NAME'),
        'USER': os.getenv('DATABASE_USER'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
        'HOST': os.getenv('DATABASE_HOST'),
        'PORT': os.getenv('DATABASE_PORT'),
    }
}
```

#### 7. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

#### 8. Create Superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

#### 9. Compile Tailwind CSS

```bash
python manage.py tailwind install
python manage.py tailwind build
```

#### 10. Collect Static Files

```bash
python manage.py collectstatic
```

#### 11. Run Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser.

---

## Configuration

### Initial Setup Tasks

After installation, perform these setup tasks:

#### 1. Create Approved Budget

1. Login as admin at `/admin/`
2. Navigate to **Budgets > Approved Budgets**
3. Click **Add Approved Budget**
4. Fill in:
   - Title: e.g., "FY 2025 General Fund"
   - Fiscal Year: "2025"
   - Amount: Total budget amount
   - Upload supporting documents

#### 2. Create Budget Allocations

1. Navigate to **Budgets > Budget Allocations**
2. Click **Add Budget Allocation**
3. Select:
   - Approved Budget
   - End User (department head)
   - Department name
   - Allocated amount

#### 3. Create Users

1. Navigate to **Users > Users**
2. Create end users with:
   - Username, email, password
   - **Role**: End User
   - Assign to department

3. Create approving officers with:
   - Username, email, password
   - **Role**: Approving Officer

---

## Usage

### For End Users

#### Accessing the Dashboard
1. Login at `/login/`
2. View your dashboard with:
   - Total allocated budget
   - Budget utilization
   - Recent activities
   - Pending approvals

#### Submitting a PRE
1. Navigate to **Submit PRE**
2. Upload Excel file following the template
3. Select budget allocation
4. Submit for review
5. Track status in dashboard

#### Creating a Purchase Request
1. Navigate to **Create PR**
2. Select source PRE and line item
3. Fill in item details and quantities
4. Upload supporting documents
5. Submit for approval

#### Creating an Activity Design
1. Navigate to **Create AD**
2. Fill in activity details
3. Upload activity design document
4. Submit for approval

### For Approving Officers

#### Reviewing Documents
1. Login and view **Pending Approvals**
2. Click on document to review
3. View details and uploaded files
4. Options:
   - **Approve**: Approve entire document
   - **Partial Approve**: Select specific line items
   - **Reject**: Reject with remarks
5. Upload scanned signed document

### For Administrators

#### Managing Budgets
1. Access admin panel at `/admin/`
2. Create approved budgets
3. Allocate to departments
4. Monitor utilization

#### Viewing Analytics
1. Access **Admin Dashboard**
2. View:
   - Total budget and utilization
   - Pending/approved requests
   - Department-wise breakdown
   - Recent activities

#### Generating Reports
1. Navigate to **Reports**
2. Select report type:
   - Budget Overview
   - PRE Details
   - Quarterly Analysis
3. Export to Excel/PDF

---

## User Roles

### 1. Administrator (Super Admin)
- **Access Level**: Full system access
- **Permissions**:
  - Create/edit approved budgets
  - Manage budget allocations
  - Manage users
  - View all documents
  - Generate system-wide reports
  - Access audit trails

### 2. End User (Department Head)
- **Access Level**: Department-specific
- **Permissions**:
  - View assigned budget allocation
  - Submit PRE, PR, AD documents
  - Track submission status
  - View budget utilization
  - Generate department reports

### 3. Approving Officer
- **Access Level**: Document review
- **Permissions**:
  - Review submitted documents
  - Approve/reject/partially approve
  - Upload signed documents
  - View approval history
  - Receive notifications

---

## Core Modules

### 1. Budget Management (`apps/budgets/`)

**Models:**
- `ApprovedBudget`: System-wide approved budgets
- `BudgetAllocation`: Department budget allocations
- `DepartmentPRE`: PRE documents with line items
- `PurchaseRequest`: Procurement requests
- `ActivityDesign`: Activity/event proposals
- `RequestApproval`: Approval workflow tracking

**Key Features:**
- Automatic budget validation
- Quarterly breakdown tracking
- Multi-stage approval workflow
- Budget consumption tracking

### 2. User Management (`apps/users/`)

**Custom User Model:**
```python
class User(AbstractUser):
    is_approving_officer = BooleanField()
    department = CharField()
    position = CharField()
    # ... other fields
```

**Authentication:**
- Custom login/logout views
- Role-based decorators: `@role_required('admin')`
- Session management

### 3. Admin Panel (`apps/admin_panel/`)

**Features:**
- Dashboard with analytics
- Budget allocation management
- Document approval interface
- Audit trail viewer
- Report generation

### 4. End User App (`apps/end_user_app/`)

**Features:**
- User dashboard
- PRE/PR/AD submission forms
- Budget overview and analytics
- Quarterly analysis
- Transaction history

---

## Database Schema

### Key Models

#### ApprovedBudget
```python
- title: CharField
- fiscal_year: CharField (unique)
- amount: DecimalField
- remaining_budget: DecimalField
- created_at: DateTimeField
- is_active: BooleanField
```

#### BudgetAllocation
```python
- approved_budget: ForeignKey(ApprovedBudget)
- end_user: ForeignKey(User)
- department: CharField
- allocated_amount: DecimalField
- remaining_balance: DecimalField
- pre_amount_used: DecimalField
- pr_amount_used: DecimalField
- ad_amount_used: DecimalField
- is_active: BooleanField
```

#### DepartmentPRE
```python
- id: UUIDField
- budget_allocation: ForeignKey(BudgetAllocation)
- submitted_by: ForeignKey(User)
- department: CharField
- fiscal_year: CharField
- status: CharField (Draft/Pending/Approved/Rejected)
- total_amount: DecimalField
- uploaded_excel_file: FileField
- line_items: ManyToMany(PRELineItem)
```

#### PurchaseRequest
```python
- id: UUIDField
- budget_allocation: ForeignKey(BudgetAllocation)
- submitted_by: ForeignKey(User)
- pr_number: CharField (unique)
- source_pre: ForeignKey(DepartmentPRE)
- source_line_item: ForeignKey(PRELineItem)
- total_amount: DecimalField
- status: CharField
```

#### ActivityDesign
```python
- id: UUIDField
- budget_allocation: ForeignKey(BudgetAllocation)
- submitted_by: ForeignKey(User)
- ad_number: CharField (unique)
- activity_title: CharField
- total_amount: DecimalField
- status: CharField
- uploaded_document: FileField
```

---

## API Endpoints

### Authentication
- `POST /login/` - User login
- `GET /logout/` - User logout

### End User Routes
- `GET /dashboard/` - User dashboard
- `GET /budget/overview/` - Budget overview
- `GET /budget/quarterly/` - Quarterly analysis
- `POST /pre/submit/` - Submit PRE
- `POST /pr/create/` - Create purchase request
- `POST /ad/create/` - Create activity design

### Admin Routes
- `GET /admin/dashboard/` - Admin dashboard
- `GET /admin/budget-allocation/` - Manage allocations
- `GET /admin/pre/pending/` - Pending PRE approvals
- `POST /admin/pre/approve/<id>/` - Approve PRE
- `GET /admin/audit-trail/` - View audit logs

### Reports
- `GET /reports/budget-overview/` - Budget overview report
- `GET /reports/pre-details/` - PRE details report
- `GET /reports/export/excel/` - Export to Excel
- `GET /reports/export/pdf/` - Export to PDF

---

## Screenshots

> **Note**: Add screenshots of your application here

### Admin Dashboard
![Admin Dashboard](docs/screenshots/admin-dashboard.png)

### End User Dashboard
![End User Dashboard](docs/screenshots/user-dashboard.png)

### PRE Submission
![PRE Submission](docs/screenshots/pre-submission.png)

### Budget Overview
![Budget Overview](docs/screenshots/budget-overview.png)

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Coding Standards

- Follow PEP 8 style guide
- Use meaningful variable names
- Add docstrings to functions and classes
- Write unit tests for new features
- Update documentation as needed

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Contact

**Project Team**
- Developer: John Romel Lucot
- Institution: Bohol Island State University - Balilihan Campus
- Project Type: Capstone Project

**Support**
- Email: support@bisubalilihan.edu.ph
- GitHub Issues: [Create an issue](https://github.com/yourusername/repo/issues)

---

## Acknowledgments

- **Bohol Island State University - Balilihan Campus** for the opportunity and support
- **Project Advisers** for guidance and mentorship
- **Django Community** for excellent documentation
- **Tailwind CSS** for the beautiful UI framework
- **Chart.js** for interactive data visualization
- All contributors and testers

---

## Project Status

**Current Version**: 1.0.0
**Status**: Active Development
**Last Updated**: November 2025

### Roadmap

- [x] Core budget management system
- [x] PRE submission and approval
- [x] Purchase request module
- [x] Activity design module
- [x] Admin dashboard analytics
- [x] Report generation (Excel/PDF)
- [ ] Email notifications
- [ ] Mobile responsive optimization
- [ ] API for external integrations
- [ ] Advanced analytics and forecasting
- [ ] Bulk upload features
- [ ] Multi-year budget comparison

---

## Troubleshooting

### Common Issues

**Issue: Database connection error**
```
Solution: Check your database credentials in settings.py and ensure the database server is running.
```

**Issue: Static files not loading**
```bash
Solution: Run:
python manage.py collectstatic
python manage.py tailwind build
```

**Issue: Permission denied errors**
```
Solution: Ensure the user has the correct role assigned in the admin panel.
```

**Issue: Excel upload fails**
```
Solution: Verify the Excel file follows the PRE template format. Check file permissions.
```

---

<div align="center">

**Built with ❤️ at BISU Balilihan**

[Back to Top](#bisu-balilihan---budget-monitoring-system)

</div>
