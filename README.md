# AssetCore - Inventory Management System

A comprehensive, production-ready Inventory & Asset Management System built with Django.

## Features

### Core Functionality
- **Asset Management**: Complete CRUD operations for assets with unique IDs and serial numbers
- **Dynamic Categories**: Admin-manageable categories for organizing assets
- **Status Management**: Dynamic status options (In Use, Available, Under Maintenance, Missing, Retired)
- **User Assignment**: Track asset assignments with automatic status updates
- **Assignment History**: Complete audit trail of all asset assignments
- **Maintenance Module**: Automated maintenance logging when assets go under maintenance
- **QR Code Generation**: Automatic QR code generation for each asset
- **Search & Filter**: Advanced search and filtering capabilities
- **Export**: Export assets to Excel and PDF formats

### Dashboard & Analytics
- Real-time asset statistics
- Status distribution charts (Pie chart)
- Category distribution charts (Bar chart)
- Recent activity feed
- Monthly asset additions tracking

### Security & Access Control
- Role-based access control (Super Admin, Admin, Technician, Viewer)
- Django authentication system
- Soft delete functionality (never permanently delete records)
- Complete activity logging

### Technical Features
- PostgreSQL database support
- Django signals for automated workflows
- Responsive Bootstrap 5 UI
- Mobile-friendly design
- Production-ready deployment configuration

## Installation

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- pip

### Setup Steps

1. **Clone the repository**
```bash
git clone <repository-url>
cd Inventory-Web
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure database**
   - Create a PostgreSQL database
   - Update database settings in `inventory_system/settings.py` or use environment variables:
     ```bash
     DB_NAME=inventory_db
     DB_USER=postgres
     DB_PASSWORD=your_password
     DB_HOST=localhost
     DB_PORT=5432
     ```

5. **Run migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Create superuser**
```bash
python manage.py createsuperuser
```

7. **Create initial data (Status Options and Categories)**
   - Login to admin panel at `/admin/`
   - Create Status Options: In Use, Available, Under Maintenance, Missing, Retired
   - Create Categories as needed

8. **Run development server**
```bash
python manage.py runserver
```

## Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=inventory_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
```

## Project Structure

```
Inventory-Web/
├── assets/              # Asset management app
│   ├── models.py       # Asset, Category, StatusOption models
│   ├── views.py        # Asset CRUD views
│   ├── forms.py        # Asset forms
│   ├── signals.py      # Automated workflows
│   └── utils.py        # QR code, export utilities
├── dashboard/          # Dashboard app
│   └── views.py        # Dashboard analytics
├── maintenance/        # Maintenance module
│   ├── models.py       # MaintenanceLog model
│   └── views.py        # Maintenance views
├── users/              # User management
│   ├── models.py       # UserProfile model
│   └── decorators.py   # Role-based access decorators
├── templates/          # HTML templates
├── static/            # Static files
└── inventory_system/  # Project settings
```

## Usage

### Creating Assets
1. Navigate to Assets → Add Asset
2. Fill in required fields (Asset ID, Category, Serial Number)
3. Assign to user (optional - will auto-set status to "In Use")
4. Save - QR code is automatically generated

### Managing Maintenance
- When asset status changes to "Under Maintenance", a maintenance log is automatically created
- Maintenance logs can be viewed and updated in the Maintenance section

### Exporting Data
- Use Export Excel or Export PDF buttons in the Assets list view
- Exports include all filtered/search results

## Deployment

### Production Settings
- Set `DEBUG=False` in settings.py
- Configure proper `ALLOWED_HOSTS`
- Use environment variables for secrets
- Set up PostgreSQL database
- Configure static files serving (WhiteNoise or Nginx)
- Use Gunicorn as WSGI server
- Set up Nginx as reverse proxy

### Using Gunicorn
```bash
gunicorn inventory_system.wsgi:application --bind 0.0.0.0:8000
```

## Future Enhancements

The system is designed to be modular and extensible. Planned modules include:
- Purchase Orders
- Vendor Management
- IT Support Ticketing
- Incident Reporting
- Field Technician Logs
- Asset Depreciation Tracking
- Warranty Tracking
- Expense Management
- Department Budget Tracking

## License

[Your License Here]

## Support

For issues and questions, please contact [Your Contact Information]
