#!/bin/bash

# Exit on error
set -e

echo "Starting deployment process..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
until PGPASSWORD=nishadpartydbprod psql -h "45.159.230.101" -p 6546 -U "nishadparty_user" -d "nishadpartyprod" -c '\q'; do
  >&2 echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is up - continuing..."

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist
echo "Checking for superuser..."
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print("Creating superuser...")
    User.objects.create_superuser(
        phone_number='9999999999',
        password='admin123'
    )
    print("Superuser created: phone_number=9999999999, password=admin123")
else:
    print("Superuser already exists")
EOF

echo "Deployment tasks completed successfully!"

# Execute the main command
exec "$@"
