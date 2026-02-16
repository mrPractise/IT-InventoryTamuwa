# Quick Setup Guide

## Initial Setup (Development)

1. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

2. **Set up environment variables**
   - Copy `.env.example` to `.env`
   - Update database credentials if needed (defaults to SQLite for quick start)

3. **Run migrations**
```bash
python manage.py migrate
```

4. **Create superuser**
```bash
python manage.py createsuperuser
```

5. **Initialize default data**
```bash
python manage.py init_defaults
python manage.py init_maintenance_actions
```

6. **Run development server**
```bash
python manage.py runserver
```

7. **Access the application**
   - Open http://127.0.0.1:8000
   - Login with your superuser credentials
   - Start creating assets!

## Using SQLite (Quick Start)

The system defaults to SQLite for development. No additional database setup needed!

## Switching to PostgreSQL

1. Install PostgreSQL
2. Create database:
```sql
CREATE DATABASE inventory_db;
```

3. Update `.env` file:
```env
DB_NAME=inventory_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

4. Update `inventory_system/settings.py` to use PostgreSQL (uncomment PostgreSQL config)

5. Run migrations again:
```bash
python manage.py migrate
```

## First Steps After Setup

1. **Create Categories**
   - Go to Admin Panel → Categories
   - Add categories like "Laptop", "Desktop", "Monitor", etc.

2. **Create Status Options** (if not using init_defaults)
   - Go to Admin Panel → Status Options
   - Add: In Use, Available, Under Maintenance, Missing, Retired

3. **Create Assets**
   - Go to Assets → Add Asset
   - Fill in required fields
   - QR codes are generated automatically

4. **Assign Users**
   - Create users in Admin Panel
   - Assign assets to users
   - Status automatically changes to "In Use"

## Troubleshooting

### Import Errors
- Make sure all apps are in `INSTALLED_APPS` in `settings.py`
- Run `python manage.py check` to verify configuration

### Template Errors
- Ensure `templates/` directory exists
- Check that `TEMPLATES` setting includes `templates` directory

### Static Files Not Loading
- Run `python manage.py collectstatic`
- Check `STATIC_URL` and `STATIC_ROOT` in settings

### Database Errors
- Verify database credentials
- Check if database exists
- Run `python manage.py migrate` again
