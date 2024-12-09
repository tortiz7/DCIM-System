#!/bin/bash

set -e

# Log setup progress
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
echo "Starting system setup..."

# System updates with added dependencies
apt-get update
apt-get install -y \
   ca-certificates \
   curl \
   gnupg \
   lsb-release \
   git \
   jq \
   netcat \
   mysql-client

# Node Exporter setup (unchanged from your script)
[Previous Node Exporter setup section remains exactly the same]

# Create directories with proper permissions
mkdir -p /var/local/ralph/{media,static,logs} /usr/share/ralph/static /etc/ralph/conf.d
chown -R www-data:www-data /var/local/ralph /usr/share/ralph/static

# Generate secret key
SECRET_KEY=$(openssl rand -base64 32)

# Enhanced Ralph settings
cat <<EOF > /etc/ralph/conf.d/settings.conf
ALLOWED_HOSTS=${aws_lb_dns},localhost,127.0.0.1
DATABASE_NAME=${db_name}
DATABASE_USER=${db_user}
DATABASE_PASSWORD=${db_password}
DATABASE_HOST=${db_endpoint}
REDIS_HOST=${redis_endpoint}
REDIS_PORT=${redis_port}
SECRET_KEY=${SECRET_KEY}
DEBUG=False
STATIC_ROOT=/usr/share/ralph/static
MEDIA_ROOT=/var/local/ralph/media
LOG_DIR=/var/local/ralph/logs
CHATBOT_ENABLED=true
EOF

# Enhanced prerequisites check
check_prerequisites() {
   FREE_SPACE=$(df -h / | awk 'NR==2 {print $4}' | sed 's/G//')
   if [ $FREE_SPACE -lt 20 ]; then
       echo "❌ Insufficient disk space. Need at least 20GB free."
       exit 1
   fi
   
   if ! command -v nvidia-smi &> /dev/null; then
       echo "❌ NVIDIA drivers not properly installed"
       exit 1
   fi
   
   if ! docker info | grep -q "Runtimes:.*nvidia"; then
       echo "❌ NVIDIA Docker runtime not configured"
       exit 1
   fi

   if ! command -v docker &> /dev/null; then
       echo "❌ Docker not installed"
       exit 1
   }
}

check_prerequisites

# Wait for external services
echo "Waiting for database connection..."
until nc -z ${db_endpoint} 3306; do
    echo "⏳ Database not ready - waiting..."
    sleep 5
done

echo "Waiting for Redis connection..."
until nc -z ${redis_endpoint} ${redis_port}; do
    echo "⏳ Redis not ready - waiting..."
    sleep 5
done

# Verify database connection
until mysql -h${db_endpoint} -u${db_user} -p${db_password} -e "SELECT 1" ${db_name}; do
    echo "⏳ Database connection not ready - retrying..."
    sleep 5
done

mkdir -p /opt/ralph/model
chmod 777 /opt/ralph/model

# Start services
cd /opt/ralph/source/docker
echo "Starting services..."
docker compose up -d

# Simple wait for services
echo "Waiting for services to start..."
sleep 45

# Initialize database
echo "Initializing database..."
docker compose exec -T web ralphctl migrate

# Create superuser and get API token
echo "Creating superuser and retrieving API token..."
RALPH_API_TOKEN=$(docker compose exec -T web python3 << 'EOF' | grep RALPH_API_TOKEN | cut -d'=' -f2
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
User = get_user_model()

if not User.objects.filter(username="admin").exists():
   user = User.objects.create_superuser("admin", "admin@example.com", "admin")
   print("Superuser created successfully")
else:
   user = User.objects.get(username="admin")
   print("Superuser already exists")

token, created = Token.objects.get_or_create(user=user)
print(f"RALPH_API_TOKEN={token.key}")
EOF
)

# Verify token exists
if [ -z "$RALPH_API_TOKEN" ]; then
   echo "❌ Failed to retrieve API token"
   exit 1
else
   echo "✅ API token retrieved successfully"
fi

# Add chatbot settings after token generation
echo "CHATBOT_URL=http://chatbot:8001" >> /etc/ralph/conf.d/settings.conf
echo "RALPH_API_TOKEN=${RALPH_API_TOKEN}" >> /etc/ralph/conf.d/settings.conf

# Update environment file with all variables
cat > /opt/ralph/docker/.env << EOF
db_name=${db_name}
db_user=${db_user}
db_password=${db_password}
EOF

# Initialize Ralph with demo data
echo "Importing demo data..."
docker compose exec -T web ralphctl demodata
docker compose exec -T web ralphctl sitetree_resync_apps

# Simple chatbot connectivity check
sleep 15
if curl -m 5 -sf "http://localhost:8001/health/" &>/dev/null; then
   echo "✅ Chatbot responding"
else
   echo "⚠️ Chatbot not responding, but continuing deployment"
fi

echo "🚀 Ralph deployment completed!"