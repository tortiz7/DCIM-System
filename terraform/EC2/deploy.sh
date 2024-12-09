#!/bin/bash

# Log setup progress
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
echo "Starting system setup..."

# System updates
echo "Updating system packages..."
apt-get update
apt-get install -y \
   ca-certificates \
   curl \
   gnupg \
   lsb-release \
   git \
   jq

# Install Node Exporter for monitoring
echo "Setting up Node Exporter..."
useradd --no-create-home --shell /bin/false node_exporter
wget https://github.com/prometheus/node_exporter/releases/download/v1.6.1/node_exporter-1.6.1.linux-amd64.tar.gz
tar xzf node_exporter-1.6.1.linux-amd64.tar.gz
cp node_exporter-1.6.1.linux-amd64/node_exporter /usr/local/bin/
chown node_exporter:node_exporter /usr/local/bin/node_exporter

# Create Node Exporter service
cat <<EOF > /etc/systemd/system/node_exporter.service
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF

# Start Node Exporter
systemctl daemon-reload
systemctl start node_exporter
systemctl enable node_exporter

# Clean up Node Exporter installation files
rm -rf node_exporter-1.6.1.linux-amd64.tar.gz node_exporter-1.6.1.linux-amd64

# Create setup completion marker
touch /home/ubuntu/.setup_complete
echo "System setup completed successfully"

# Clone Ralph repository
echo "Cloning modified Ralph repository..."
git clone -b deployment-test https://${github_token}@github.com/tortiz7/DCIM-System.git /opt/ralph/source
cd /opt/ralph/source

# Create required directories
mkdir -p /etc/ralph/conf.d
mkdir -p /var/log/ralph
mkdir -p /opt/ralph/docker
mkdir -p /opt/ralph/docker/model

echo "db_name=${db_name}"
echo "db_user=${db_user}"
echo "db_password=${db_password}"
echo "db_endpoint=${db_endpoint}"
echo "redis_endpoint=${redis_endpoint}"
echo "RALPH_API_TOKEN=${RALPH_API_TOKEN}"

sysctl -w net.bridge.bridge-nf-call-iptables=1
sysctl -w net.bridge.bridge-nf-call-ip6tables=1

# Configure initial Ralph settings
cat <<EOF > /etc/ralph/conf.d/settings.conf
ALLOWED_HOSTS=${aws_lb_dns},localhost,127.0.0.1
DATABASE_NAME=${db_name}
DATABASE_USER=${db_user}
DATABASE_PASSWORD=${db_password}
DATABASE_HOST=${db_endpoint}
REDIS_HOST=${redis_endpoint}
REDIS_PORT=${redis_port}
CHATBOT_ENABLED=true
EOF

# Verify prerequisites
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
   fi
}

check_prerequisites

cat > /opt/ralph/docker/.env << EOF
DATABASE_NAME=${db_name}
DATABASE_USER=${db_user}
DATABASE_PASSWORD=${db_password}
DATABASE_HOST=${db_endpoint}
REDIS_HOST=${redis_endpoint}
REDIS_PORT=${redis_port}
RALPH_API_TOKEN=${RALPH_API_TOKEN}
ALLOWED_HOSTS=${aws_lb_dns},localhost,127.0.0.1
CHATBOT_ENABLED=true
CHATBOT_URL=http://chatbot:8001
EOF

echo "Verifying environment variables:"
echo "Current directory: $(pwd)"
echo "Contents of .env file:"
cat .env
echo "Running docker-compose with environment..."

echo "Verifying RDS connection..."
until nc -z -v -w5 ${db_endpoint%:*} ${db_endpoint#*:}; do
    echo "⏳ Waiting for RDS connection..."
    sleep 5
done

echo "Verifying ElastiCache connection..."
until nc -z -v -w5 ${redis_endpoint} ${redis_port}; do
    echo "⏳ Waiting for ElastiCache connection..."
    sleep 5
done

# Start services and build containers
cd /opt/ralph/source/docker
echo "Building and starting containers..."
docker compose --env-file /opt/ralph/docker/.env up --build -d db redis web nginx

# Wait for database
echo "Waiting for database to be ready..."
until docker compose exec -T db mysqladmin -u${db_user} -p${db_password} ping --silent; do
   echo "⏳ Waiting for DB to be ready..."
   sleep 5
done

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

# Restart all services with complete configuration
echo "Restarting all services with API token..."
docker compose down
docker compose up --build -d

# Finalize deployment process
echo "🚀 Ralph deployment completed successfully!"
