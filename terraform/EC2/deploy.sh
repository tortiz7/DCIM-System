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
   jq \
   netcat

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

# Verify prerequisites
check_prerequisites() {
   echo "Checking prerequisites..."
   
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
   
   echo "✅ All prerequisites met"
}

check_prerequisites

# Clone Ralph repository
echo "Cloning modified Ralph repository..."
git clone -b deployment-test https://${github_token}@github.com/tortiz7/DCIM-System.git /opt/ralph/source
cd /opt/ralph/source

# Create required directories
mkdir -p /etc/ralph/conf.d
mkdir -p /var/log/ralph
mkdir -p /opt/ralph/docker
mkdir -p /opt/ralph/docker/model

# Enable required kernel settings
sysctl -w net.bridge.bridge-nf-call-iptables=1
sysctl -w net.bridge.bridge-nf-call-ip6tables=1

# Write environment variables to file
echo "Setting up environment configuration..."
cat > /opt/ralph/source/docker/.env << EOF
DATABASE_NAME=${db_name}
DATABASE_USER=${db_user}
DATABASE_PASSWORD=${db_password}
DATABASE_HOST=${db_endpoint}
REDIS_HOST=${redis_endpoint}
REDIS_PORT=${redis_port}
ALLOWED_HOSTS="${aws_lb_dns},localhost,127.0.0.1"
CHATBOT_ENABLED=true
CHATBOT_URL=http://chatbot:8001
EXPORT ALB_DOMAIN=${aws_lb_dns}
EOF

# Verify the environment file
echo "Verifying environment file:"
if [ ! -f /opt/ralph/source/docker/.env ]; then
    echo "❌ Environment file not created properly"
    exit 1
fi

# Start services
cd /opt/ralph/source/docker
echo "Building and starting containers..."
docker compose up -d --build web nginx chatbot

# Wait for web service to be healthy
echo "Waiting for web service to be healthy..."
TIMEOUT=300  # 5 minutes timeout
start_time=$(date +%s)
while true; do
    if docker compose ps | grep web | grep -q "(healthy)"; then
        echo "✅ Web service is healthy"
        break
    fi
    
    current_time=$(date +%s)
    elapsed_time=$((current_time - start_time))
    
    if [ $elapsed_time -ge $TIMEOUT ]; then
        echo "❌ Timeout waiting for web service to become healthy"
        exit 1
    fi
    
    echo "Waiting for web service... ($elapsed_time seconds elapsed)"
    sleep 10
done

# Initialize database
echo "Initializing database..."
docker compose exec -T web ralphctl migrate
if [ $? -ne 0 ]; then
    echo "❌ Database migration failed"
    exit 1
fi

echo "Loading demo data..."
docker compose exec -T web ralphctl demodata
docker compose exec -T web ralphctl sitetree_resync_apps

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

# Add chatbot settings to Ralph configuration
echo "Configuring chatbot settings..."
echo "CHATBOT_URL=http://chatbot:8001" >> /etc/ralph/conf.d/settings.conf
echo "RALPH_API_TOKEN=${RALPH_API_TOKEN}" >> /etc/ralph/conf.d/settings.conf

# Update environment file with complete configuration
cat > /opt/ralph/source/docker/.env << EOF
DATABASE_NAME=${db_name}
DATABASE_USER=${db_user}
DATABASE_PASSWORD=${db_password}
DATABASE_HOST=${db_endpoint}
REDIS_HOST=${redis_endpoint}
REDIS_PORT=${redis_port}
ALLOWED_HOSTS="${aws_lb_dns},localhost,127.0.0.1"
CHATBOT_ENABLED=true
CHATBOT_URL=http://chatbot:8001
RALPH_API_TOKEN=${RALPH_API_TOKEN}
ALB_DOMAIN=${aws_lb_dns}
EOF

# Restart all services to pick up new configuration
echo "Restarting all services with API token..."
docker compose down
docker compose up -d --build

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
TIMEOUT=300  # 5 minutes timeout
start_time=$(date +%s)
while true; do
    if docker compose ps | grep -q "(healthy)" && [ $(docker compose ps | grep -c "(healthy)") -ge 3 ]; then
        echo "✅ All services are healthy"
        break
    fi
    
    current_time=$(date +%s)
    elapsed_time=$((current_time - start_time))
    
    if [ $elapsed_time -ge $TIMEOUT ]; then
        echo "❌ Timeout waiting for services to become healthy"
        docker compose logs
        exit 1
    fi
    
    echo "Waiting for services... ($elapsed_time seconds elapsed)"
    sleep 10
done

# Verify Chatbot can connect to Ralph
echo "Verifying Chatbot connection to Ralph..."
if ! docker compose logs chatbot | grep -q "Connected to Ralph API"; then
    echo "⚠️ Chatbot connection to Ralph cannot be verified - check logs for details"
    docker compose logs chatbot
else
    echo "✅ Chatbot successfully connected to Ralph"
fi

# Finalize deployment process
echo "🚀 Ralph deployment completed successfully!"
echo "Access the application at http://${aws_lb_dns}"