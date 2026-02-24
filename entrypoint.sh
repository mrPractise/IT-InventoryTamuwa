#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
# Wait until postgres is ready
while ! python -c "
import psycopg2, os
psycopg2.connect(
    dbname=os.environ.get('DB_NAME','inventory_db'),
    user=os.environ.get('DB_USER','postgres'),
    password=os.environ.get('DB_PASSWORD','postgres'),
    host=os.environ.get('DB_HOST','db'),
    port=os.environ.get('DB_PORT','5432'),
)
" 2>/dev/null; do
  echo "  db not ready — sleeping 1s"
  sleep 1
done
echo "PostgreSQL is ready."

# Apply migrations
python manage.py migrate --noinput

# Create superuser if not exists (uses env vars)
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER_USERNAME', '$DJANGO_SUPERUSER_EMAIL', '$DJANGO_SUPERUSER_PASSWORD')
    print('Superuser created.')
else:
    print('Superuser already exists.')
" 2>/dev/null || true

# Start Gunicorn
exec gunicorn inventory_system.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
