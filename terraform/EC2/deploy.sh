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

# Install Docker
# echo "Installing Docker..."
# if ! command -v docker &> /dev/null; then
#     mkdir -p /etc/apt/keyrings
#     curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

#     echo \
#     "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
#     $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

#     apt-get update
#     apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

#     # Start and enable Docker service
#     systemctl start docker
#     systemctl enable docker

#     # Add ubuntu user to docker group
#     usermod -aG docker ubuntu
# fi

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

# Essential setup
mkdir -p /etc/ralph/conf.d
mkdir -p /var/log/ralph
mkdir -p /opt/ralph/docker

# Copy docker-compose file (passed from Terraform)
echo "${docker_compose_content}" > /opt/ralph/docker/docker-compose.yml

# Configure Ralph settings
cat <<EOF > /etc/ralph/conf.d/settings.conf
ALLOWED_HOSTS=${aws_lb_dns},localhost,127.0.0.1
DATABASE_NAME=${db_name}
DATABASE_USER=${db_user}
DATABASE_PASSWORD=${db_password}
DATABASE_HOST=${db_endpoint}
REDIS_HOST=${redis_endpoint}
REDIS_PORT=${redis_port}
CHATBOT_ENABLED=true
CHATBOT_URL=http://chatbot:8001
EOF

# Add to deploy.sh
check_prerequisites() {
    # Check disk space
    FREE_SPACE=$(df -h / | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ $FREE_SPACE -lt 20 ]; then
        echo "❌ Insufficient disk space. Need at least 50GB free."
        exit 1
    fi
    
    # Verify NVIDIA setup
    if ! command -v nvidia-smi &> /dev/null; then
        echo "❌ NVIDIA drivers not properly installed"
        exit 1
    fi
    
    # Check Docker
    if ! docker info | grep -q "Runtimes:.*nvidia"; then
        echo "❌ NVIDIA Docker runtime not configured"
        exit 1
    fi
}

# Add check before deployment
check_prerequisites

# Start services using Docker Compose
cd /opt/ralph/docker
docker compose pull
docker compose up -d

# Wait for containers to be up and running
echo "Waiting for services to be fully up..."
sleep 60


echo "✅ Ralph and Chatbot deployment completed"

echo "Initializing Ralph with demo data..."
cd /opt/ralph/docker

# # Wait for services to be fully up
# echo "Waiting for services to be ready..."
# sleep 30

echo "Waiting for database to be ready..."
until docker compose exec -T db mysqladmin -u${db_user} -p${db_password} ping --silent; do
    echo "❌ Waiting for DB to be ready..."
    sleep 5
done
echo "✅ Database is ready"

# Create superuser if doesn't exist
echo "Setting up superuser..."
docker compose exec -T web python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
EOF

# Import demo data
echo "Importing demo data..."
docker compose exec -T web ralphctl demodata
if [ $? -ne 0 ]; then
    echo "❌ Demo data import failed"
    exit 1
fi

# Sync site tree
echo "Syncing site tree..."
docker compose exec -T web ralphctl sitetree_resync_apps
if [ $? -ne 0 ]; then
    echo "❌ Site tree sync failed"
    exit 1
fi

echo "✅ Ralph initialization complete with demo data!"