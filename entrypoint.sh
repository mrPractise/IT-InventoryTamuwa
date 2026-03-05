#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."

# Wait for DB — handles both DATABASE_URL (Railway) and individual vars (Docker)
until python - <<'PYEOF'
import os, sys
db_url = os.environ.get('DATABASE_URL', '')
if db_url:
    from urllib.parse import urlparse
    import psycopg2
    u = urlparse(db_url)
    psycopg2.connect(
        dbname=u.path.lstrip('/'),
        user=u.username,
        password=u.password,
        host=u.hostname,
        port=u.port or 5432,
    )
else:
    import psycopg2
    psycopg2.connect(
        dbname=os.environ.get('DB_NAME', 'inventory_db'),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', 'postgres'),
        host=os.environ.get('DB_HOST', 'db'),
        port=int(os.environ.get('DB_PORT', '5432')),
    )
PYEOF
do
  echo "  db not ready — sleeping 1s"
  sleep 1
done

echo "PostgreSQL is ready."

# Apply migrations
python manage.py migrate --noinput

# Create superuser if not exists
python manage.py shell -c "
from django.contrib.auth import get_user_model
import os
User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', '')
email    = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')
if username and not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print('Superuser created.')
else:
    print('Superuser already exists.')
" || true

# Start Gunicorn — Railway injects PORT automatically; Docker defaults to 8000
exec gunicorn inventory_system.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
