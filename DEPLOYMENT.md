# Deployment Guide

## Production Deployment Checklist

### 1. Environment Setup

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Set Environment Variables**
   - Copy `.env.example` to `.env`
   - Update all values, especially `SECRET_KEY` and database credentials
   - Set `DEBUG=False` for production

### 2. Database Setup

1. **Create PostgreSQL Database**
```sql
CREATE DATABASE inventory_db;
CREATE USER inventory_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE inventory_db TO inventory_user;
```

2. **Run Migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

3. **Create Superuser**
```bash
python manage.py createsuperuser
```

4. **Initialize Default Data**
```bash
python manage.py init_defaults
python manage.py init_maintenance_actions
```

### 3. Static Files & Media

1. **Collect Static Files**
```bash
python manage.py collectstatic --noinput
```

2. **Configure Media Directory**
   - Ensure `media/` directory exists and is writable
   - Set proper permissions: `chmod 755 media/`

### 4. Gunicorn Configuration

Create `gunicorn_config.py`:
```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
```

Run Gunicorn:
```bash
gunicorn -c gunicorn_config.py inventory_system.wsgi:application
```

### 5. Nginx Configuration

Create `/etc/nginx/sites-available/inventory`:
```nginx
upstream inventory_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 100M;

    location /static/ {
        alias /path/to/Inventory-Web/staticfiles/;
    }

    location /media/ {
        alias /path/to/Inventory-Web/media/;
    }

    location / {
        proxy_pass http://inventory_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/inventory /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. Systemd Service (Optional)

Create `/etc/systemd/system/inventory.service`:
```ini
[Unit]
Description=Inventory Management System Gunicorn
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/Inventory-Web
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn -c gunicorn_config.py inventory_system.wsgi:application

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable inventory
sudo systemctl start inventory
```

### 7. SSL/HTTPS Setup (Recommended)

Use Let's Encrypt:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 8. Database Backups

Set up automated backups with cron:
```bash
# Add to crontab (crontab -e)
0 2 * * * pg_dump -U inventory_user inventory_db > /backups/inventory_$(date +\%Y\%m\%d).sql
```

### 9. Security Checklist

- [ ] Change default `SECRET_KEY`
- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up SSL/HTTPS
- [ ] Configure firewall rules
- [ ] Set up database backups
- [ ] Configure log rotation
- [ ] Review file permissions
- [ ] Set up monitoring/alerting

### 10. Monitoring

Consider setting up:
- Application monitoring (Sentry, Rollbar)
- Server monitoring (Prometheus, Grafana)
- Log aggregation (ELK Stack, Papertrail)

## Troubleshooting

### Common Issues

1. **Static files not loading**
   - Check `STATIC_ROOT` path
   - Verify Nginx static file configuration
   - Run `collectstatic` again

2. **Database connection errors**
   - Verify PostgreSQL is running
   - Check database credentials in `.env`
   - Verify user permissions

3. **Permission errors**
   - Check file permissions on `media/` and `staticfiles/`
   - Verify user running Gunicorn has proper permissions

4. **502 Bad Gateway**
   - Check if Gunicorn is running
   - Verify upstream server in Nginx config
   - Check Gunicorn logs
