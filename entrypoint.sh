#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."

# Wait until DATABASE_URL is reachable
until python - <<'PYEOF'
import os, psycopg2
from urllib.parse import urlparse
u = urlparse(os.environ['DATABASE_URL'])
psycopg2.connect(
    dbname=u.path.lstrip('/'),
    user=u.username,
    password=u.password,
    host=u.hostname,
    port=u.port or 5432,
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

# Start Gunicorn — Railway injects PORT
exec gunicorn inventory_system.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
