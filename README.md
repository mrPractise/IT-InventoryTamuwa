# ICTcore — IT Inventory Management System

ICTcore is a Django-based inventory management system for tracking IT assets, maintenance, requisitions, issues, and projects. It provides role-based access control, real-time notifications, and automated workflows.

## Overview

The system manages the complete lifecycle of IT assets from procurement to retirement, with integrated maintenance tracking, requisition workflows, issue reporting, and project management.

## Core Applications

### assets
Manages IT assets including computers, peripherals, and equipment.
- **Models**: Asset, Category, Department, Person, StatusOption, ActivityLog
- **Features**: QR code generation, soft delete, assignment history, status lifecycle (In Use, Available, Under Maintenance, Missing, Retired)
- **Signals**: Auto-creates maintenance logs when asset status changes to "Under Maintenance"

### maintenance
Tracks maintenance activities and repair history.
- **Models**: MaintenanceLog, ActionTakenOption
- **Features**: Configurable action types, cost tracking, technician assignment
- **Signals**: Auto-updates asset status when maintenance is completed

### requisition
Manages procurement requests and approval workflows.
- **Models**: Requisition, RequisitionItem
- **Features**: Multi-company support (Tera, Flux, Tamuwa), item approval/rejection, bought items queue
- **Links**: One-way FK to Issue and Project (requisition tags issue/project, not vice versa)

### issues
Issue tracking and project management.
- **Models**: Issue, IssueComment, Project, ProjectComment, ProjectItem
- **Features**: Priority levels, status tracking, cost breakdown with line items, category-linked asset previews

### technicians
External technician management and service recommendations.
- **Models**: Technician, TechnicianService, TechnicianRecommendation
- **Features**: Service catalog, recommendations linked to technicians

### users
User management with role-based access.
- **Models**: User (extended via Profile), Department, Person
- **Roles**: Super Admin, Admin, Technician, Viewer
- **Features**: Password change with toggle visibility, people & departments directory

### dashboard
Analytics and notifications hub.
- **Views**: Dashboard home with charts, notifications aggregation
- **Context Processor**: Injects unread notification count on all pages
- **Notifications**: Aggregates critical issues, stale requisitions, missing assets, long-running maintenance, pending projects

### api
Centralized REST API endpoints.
- **Features**: Category assets API, asset search, requisition items

## Key Interconnections

```
Asset <--FK--> Category
Asset <--FK--> StatusOption
Asset <--M2M--> Person (assignment history)

MaintenanceLog <--FK--> Asset
MaintenanceLog <--FK--> Technician (performed_by)
MaintenanceLog <--FK--> Requisition (optional)

Requisition <--FK--> Issue (linked_issue, optional)
Requisition <--FK--> Project (linked_project, optional)
RequisitionItem <--FK--> Requisition

Issue <--FK--> Asset (optional)
Issue <--FK--> Department (optional)
Issue <--FK--> User (reported_by)

Project <--M2M--> Category
Project <--FK--> User (reported_by)
ProjectItem <--FK--> Project

TechnicianService <--FK--> Technician
TechnicianRecommendation <--FK--> Technician
```

## Automated Workflows (Signals)

1. **Asset → Maintenance**: When asset status changes to "Under Maintenance", auto-creates a MaintenanceLog
2. **Maintenance → Asset**: When maintenance log closes, asset status auto-updates to "Available"
3. **Bidirectional sync protected**: Loop guard prevents signal recursion

## Notifications System

The notifications tab aggregates real-time alerts:
- Critical/High priority open issues
- Requisitions pending > 7 days
- Bought requisitions with unprocessed items
- Assets under maintenance > 14 days
- Missing assets
- Projects pending > 30 days

## Technology Stack

### Backend
- **Django 6.0+** — Web framework
- **Django REST Framework** — API endpoints
- **Django Crispy Forms** — Form rendering with Bootstrap 5
- **Django Extensions** — Development utilities

### Database
- **SQLite** — Development (default)
- **PostgreSQL** — Production (via psycopg2-binary)

### Frontend
- **Bootstrap 5** — UI framework
- **Bootstrap Icons** — Icon library
- **Chart.js** — Dashboard analytics charts

### Utilities
- **Pillow** — Image processing (asset photos)
- **qrcode** — QR code generation for assets
- **openpyxl** — Excel export for reports
- **reportlab** — PDF generation
- **python-decouple** — Environment configuration
- **gunicorn** — WSGI HTTP server
- **whitenoise** — Static file serving

## Environment Configuration

Create a `.env` file:

```
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Optional: PostgreSQL
DB_HOST=
DB_NAME=inventory_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_PORT=5432
```

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Initialize default data (status options, maintenance actions)
python manage.py init_defaults

# Run development server
python manage.py runserver
```

## Default Data Commands

```bash
python manage.py init_defaults          # Initialize status options and maintenance actions
python manage.py init_maintenance_actions  # Reset maintenance action options
python manage.py seed_data              # Load sample data (optional)
```

## URL Structure

| Path | Description |
|------|-------------|
| `/` | Dashboard home |
| `/assets/` | Asset management |
| `/maintenance/` | Maintenance logs |
| `/requisition/` | Requisitions |
| `/issues/` | Issues list |
| `/issues/projects/` | Projects list |
| `/technicians/` | Technicians |
| `/users/directory/` | People & Departments |
| `/notifications/` | System notifications |
| `/admin/` | Django admin |
| `/api/` | REST API endpoints |

## Error Pages

Standalone HTML error pages for Nginx (no Django dependency):
- `templates/errors/404.html` — Page Not Found
- `templates/errors/403.html` — Access Denied
- `templates/errors/500.html` — Server Error
- `templates/errors/502.html` — Bad Gateway
- `templates/errors/503.html` — Service Unavailable

## Role-Based Access

| Role | Permissions |
|------|-------------|
| Super Admin | Full access including user management |
| Admin | Create/edit assets, maintenance, requisitions, issues, projects |
| Technician | View assets, update maintenance logs |
| Viewer | Read-only access to dashboard and lists |

## License

Internal use — Tamuwa ICT Department
