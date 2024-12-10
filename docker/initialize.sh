#!/bin/bash
set -e

# Wait for database
echo "Waiting for database..."
until python3 -c "import MySQLdb; MySQLdb.connect(host='db', user='$DATABASE_USER', passwd='$DATABASE_PASSWORD', db='$DATABASE_NAME')" 2>/dev/null
do
    echo "Database is unavailable - sleeping"
    sleep 1
done

# Wait for Redis
echo "Waiting for Redis..."
until redis-cli -h redis ping 2>/dev/null
do
    echo "Redis is unavailable - sleeping"
    sleep 1
done

# Initialize Ralph
echo "Initializing Ralph..."
python3 manage.py migrate --noinput
python3 manage.py collectstatic --noinput
python3 manage.py sitetree_resync_apps

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn ralph.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120