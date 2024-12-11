#!/bin/bash
set -e

# echo "Waiting for database..."
# until python3 -c "import MySQLdb; MySQLdb.connect(
#     host='${DATABASE_HOST}', 
#     user='${DATABASE_USER}', 
#     passwd='${DATABASE_PASSWORD}', 
#     db='${DATABASE_NAME}'
# )" 2>/dev/null
# do
#     echo "Database is unavailable - sleeping"
#     sleep 3
# done

# echo "Waiting for Redis..."
# until redis-cli -h "${REDIS_HOST}" -p "${REDIS_PORT}" ping 2>/dev/null | grep -q "PONG"
# do
#     echo "Redis is unavailable - sleeping"
#     sleep 3
# done

echo "Initializing Ralph..."
ralph migrate --noinput
ralph collectstatic --noinput
ralph sitetree_resync_apps

if [ -z "${RALPH_API_TOKEN}" ]; then
    # Create superuser if not already exist
    echo "Creating superuser 'admin'..."
    if ! ralph shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print(User.objects.filter(username='admin').exists())" | grep True; then
        ralph createsuperuser --username admin --email admin@example.com --noinput
        echo "from django.contrib.auth import get_user_model; User = get_user_model(); u = User.objects.get(username='admin'); u.set_password('admin'); u.save()" | ralph shell
        echo "Superuser created with username=admin and password=admin"
    else
        echo "Superuser 'admin' already exists"
    fi
fi

echo "Starting Gunicorn..."
exec gunicorn ralph.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120