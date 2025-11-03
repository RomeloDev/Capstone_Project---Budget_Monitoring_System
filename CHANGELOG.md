# Changelog

All notable changes to the BISU Balilihan Budget Monitoring System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-03

### Added

#### Core Features
- **User Management System**
  - Custom user model with role-based access control
  - Three user roles: Administrator, End User, Approving Officer
  - User authentication and session management
  - Role-based decorators for view protection

- **Budget Management Module**
  - Approved budget creation and management
  - Department budget allocation system
  - Real-time budget tracking and monitoring
  - Quarterly budget breakdown
  - Budget utilization percentage calculations

- **PRE (Program of Receipts and Expenditures)**
  - Excel file upload and parsing
  - Automatic validation against allocated budget
  - Line item categorization
  - Quarterly budget distribution
  - Multi-stage approval workflow
  - PDF generation for partially approved PREs

- **Purchase Request (PR) Module**
  - Link to approved PRE line items
  - Item-based procurement requests
  - Supporting document uploads
  - Approval workflow with partial approval support
  - PR number auto-generation

- **Activity Design (AD) Module**
  - Activity/event budget proposals
  - Document upload (DOCX format)
  - Budget allocation tracking
  - Approval workflow
  - AD number auto-generation

- **Dashboard & Analytics**
  - **Admin Dashboard**
    - System-wide budget overview
    - Total users, budget, pending/approved requests metrics
    - Department budget allocation chart
    - Department budget overview table
    - Recent activity feed
    - Active departments count
    - Average utilization percentage
    - Low budget alerts

  - **End User Dashboard**
    - Personal budget allocation overview
    - Budget utilization progress bar
    - Quarterly spending breakdown
    - Recent activity timeline
    - Pending approvals summary
    - Quick action buttons
    - Active documents count

- **Reporting System**
  - Budget overview reports
  - PRE budget details with quarterly breakdown
  - Quarterly analysis reports
  - Transaction history
  - Excel export functionality
  - PDF export functionality
  - Department-wise budget reports

- **Approval Workflow**
  - Multi-level approval system
  - Partial approval capability
  - Rejection with remarks
  - Scanned document upload
  - Email notifications (planned)
  - Approval history tracking

- **Audit Trail**
  - Complete action logging
  - User activity tracking
  - Timestamp recording
  - Model change tracking
  - Searchable audit logs

#### Frontend Features
- **Modern UI Design**
  - Tailwind CSS integration
  - Responsive design
  - Card-based layouts
  - Interactive charts (Chart.js)
  - Animated counters
  - Gradient backgrounds
  - Hover effects and transitions

- **Data Visualization**
  - Bar charts for department budgets
  - Pie charts for category distribution
  - Progress bars for budget utilization
  - Quarterly spending trends
  - Real-time metric updates

- **User Experience**
  - Clean navigation
  - Breadcrumb trails
  - Loading states
  - Success/error messages
  - Form validation
  - File upload previews
  - Natural time formatting

#### Backend Features
- **Database Architecture**
  - PostgreSQL/MySQL support
  - Optimized queries with select_related
  - Proper indexing
  - Foreign key constraints
  - UUID primary keys for security
  - JSON field support

- **File Management**
  - Secure file upload
  - File validation (format, size)
  - Organized file storage by year/month
  - Support for Excel, PDF, DOCX formats
  - File size display

- **Security**
  - CSRF protection
  - Password hashing
  - Role-based access control
  - Session security
  - File upload validation
  - SQL injection prevention

### Changed
- Migrated from deprecated models to new architecture
- Updated admin dashboard to use new BudgetAllocation model
- Improved query performance with proper annotations
- Enhanced error handling with try-catch blocks

### Fixed
- Admin dashboard showing zero values (field name mismatch: `total_amount` → `amount`)
- Budget allocation spent calculation (now uses `get_total_used()` method)
- Remaining percentage calculation in end user dashboard
- Department aggregation for charts
- Low budget department calculation

### Technical Improvements
- Code organization into separate apps
- Proper separation of concerns
- Reusable utility functions
- Comprehensive docstrings
- PEP 8 compliance
- Git version control

### Dependencies
- Django 5.1.6
- Python 3.12.3
- Tailwind CSS 3.8.0
- Chart.js 4.4.0
- openpyxl 3.1.5
- pandas 2.2.3
- reportlab 4.4.4
- python-docx 1.2.0
- And 40+ other packages (see requirements.txt)

---

## [Unreleased]

### Planned Features
- Email notification system
- SMS notifications
- Advanced analytics and forecasting
- Multi-year budget comparison
- Bulk upload functionality
- RESTful API for external integrations
- Mobile app
- Budget realignment module
- Advanced search and filtering
- Export to multiple formats (CSV, JSON)
- Automated backup system
- Performance optimization
- Caching implementation

### Known Issues
- None reported

---

## Version History

- **1.0.0** - Initial release with core features (2025-11-03)

---

## Upgrade Notes

### From 0.x to 1.0.0
This is the initial release. No upgrade path needed.

---

## Contributors
- John Romel Lucot - Lead Developer
- BISU Balilihan Team - Testing and Feedback

---

*For detailed commit history, see the [Git log](https://github.com/yourusername/repo/commits/main)*
