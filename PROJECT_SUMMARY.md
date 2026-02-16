# AssetCore - Inventory Management System

## 🎯 Project Overview

A **production-ready, full-featured Inventory & Asset Management System** built with Django, PostgreSQL, and Bootstrap 5. This system transforms Excel-based inventory tracking into a comprehensive, scalable web application.

## ✨ Key Features Implemented

### 1. Core Asset Management
- ✅ Unique Asset ID system
- ✅ Dynamic Category management (admin-configurable)
- ✅ Dynamic Status options (In Use, Available, Under Maintenance, Missing, Retired)
- ✅ Serial number tracking (unique per category)
- ✅ User/Department assignment
- ✅ Purchase date tracking
- ✅ Admin comments field
- ✅ Soft delete functionality

### 2. Automated Business Logic
- ✅ **Auto-status updates**: Status changes to "In Use" when assigned, "Available" when unassigned
- ✅ **Assignment history**: Complete audit trail of all assignments
- ✅ **Maintenance auto-logging**: Creates maintenance log when status changes to "Under Maintenance"
- ✅ **Activity logging**: All critical changes are logged automatically

### 3. Dashboard & Analytics
- ✅ Real-time statistics (Total Assets, In Use, Available, Under Maintenance, etc.)
- ✅ Status distribution pie chart (Chart.js)
- ✅ Category distribution bar chart
- ✅ Recent activity feed
- ✅ Monthly asset additions tracking

### 4. Maintenance Module
- ✅ Automatic maintenance log creation
- ✅ Dynamic "Action Taken" options (admin-configurable)
- ✅ Cost tracking
- ✅ Maintenance status (Open/Closed)
- ✅ Auto-status update when maintenance completes

### 5. User Management & Security
- ✅ Role-based access control (Super Admin, Admin, Technician, Viewer)
- ✅ Django authentication integration
- ✅ User profiles with department assignment
- ✅ Permission decorators for views

### 6. Advanced Features
- ✅ **Search & Filter**: By category, status, user, serial number
- ✅ **Pagination**: 25 items per page
- ✅ **Export to Excel**: Full asset export with formatting
- ✅ **Export to PDF**: Professional PDF reports
- ✅ **QR Code Generation**: Automatic QR code for each asset
- ✅ **Asset Detail Page**: Complete history timeline
- ✅ **Responsive Design**: Mobile-friendly Bootstrap 5 UI

### 7. UI/UX
- ✅ Modern sidebar navigation
- ✅ Clean card-based layout
- ✅ Status color coding
- ✅ Dark sidebar with gradient
- ✅ Professional dashboard design
- ✅ Mobile responsive

## 📁 Project Structure

```
Inventory-Web/
├── assets/                    # Core asset management
│   ├── models.py             # Asset, Category, StatusOption, AssignmentHistory, ActivityLog
│   ├── views.py              # CRUD operations, search, export
│   ├── forms.py              # Asset forms
│   ├── signals.py            # Automated workflows
│   ├── utils.py              # QR codes, Excel/PDF export
│   ├── admin.py              # Admin panel configuration
│   └── management/commands/  # init_defaults command
├── dashboard/                 # Dashboard & analytics
│   └── views.py              # Dashboard with charts
├── maintenance/              # Maintenance module
│   ├── models.py             # MaintenanceLog, ActionTakenOption
│   ├── views.py              # Maintenance list/detail
│   └── management/commands/  # init_maintenance_actions
├── users/                    # User management
│   ├── models.py             # UserProfile with roles
│   ├── decorators.py         # Role-based access decorators
│   └── views.py              # Login, profile views
├── templates/                # HTML templates
│   ├── base.html             # Base template with sidebar
│   ├── dashboard/            # Dashboard templates
│   ├── assets/               # Asset templates
│   ├── maintenance/          # Maintenance templates
│   └── users/                # User templates
├── inventory_system/         # Project settings
│   ├── settings.py           # Django configuration
│   └── urls.py               # URL routing
├── requirements.txt          # Python dependencies
├── README.md                 # Main documentation
├── SETUP.md                  # Quick setup guide
└── DEPLOYMENT.md             # Production deployment guide
```

## 🗄️ Database Models

### Core Models
1. **Asset**: Main asset model with all required fields
2. **Category**: Dynamic categories (admin-manageable)
3. **StatusOption**: Dynamic status options with colors
4. **Department**: Department organization
5. **AssignmentHistory**: Complete assignment audit trail
6. **ActivityLog**: System-wide activity logging
7. **MaintenanceLog**: Maintenance tracking
8. **ActionTakenOption**: Dynamic maintenance actions
9. **UserProfile**: Extended user profiles with roles

## 🔄 Automated Workflows (Signals)

1. **Asset Assignment**: Auto-updates status when assigned/unassigned
2. **Assignment History**: Logs all assignment changes
3. **Maintenance Creation**: Auto-creates maintenance log when status changes to "Under Maintenance"
4. **Activity Logging**: Logs all critical changes
5. **Maintenance Completion**: Auto-updates asset status when maintenance closes

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run migrations
python manage.py migrate

# 3. Create superuser
python manage.py createsuperuser

# 4. Initialize default data
python manage.py init_defaults
python manage.py init_maintenance_actions

# 5. Run server
python manage.py runserver
```

## 📊 Technology Stack

- **Backend**: Django 5.0.2
- **Database**: PostgreSQL (SQLite for development)
- **Frontend**: Bootstrap 5, Chart.js
- **Export**: openpyxl (Excel), reportlab (PDF)
- **QR Codes**: qrcode library
- **Forms**: django-crispy-forms
- **Deployment**: Gunicorn + Nginx

## 🎨 UI Features

- Modern gradient sidebar
- Responsive card layouts
- Color-coded status badges
- Interactive charts (Chart.js)
- Professional color scheme
- Mobile-first design

## 🔐 Security Features

- Role-based access control
- Django authentication
- CSRF protection
- SQL injection protection (Django ORM)
- Soft delete (no permanent deletion)
- Activity audit logging

## 📈 Future Enhancements (Modular Architecture Ready)

The system is designed to easily add:
- Purchase Orders module
- Vendor Management
- IT Support Ticketing
- Incident Reporting
- Field Technician Logs
- Asset Depreciation Tracking
- Warranty Tracking
- Expense Management
- Department Budget Tracking

## 📝 Notes

- All status options and categories are dynamically manageable from admin
- QR codes are automatically generated for each asset
- Export functions respect current filters/search
- Soft delete ensures no data loss
- Complete audit trail for compliance

## 🎯 System Name: AssetCore

The system is branded as **AssetCore** - a professional, enterprise-ready inventory management platform.

---

**Built with ❤️ using Django**
