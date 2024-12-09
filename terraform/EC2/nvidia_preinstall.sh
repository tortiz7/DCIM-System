#!/bin/bash
exec > >(tee /var/log/user-data.log | logger -t user-data -s 2>/dev/console) 2>&1

echo "Starting system setup..."

# Function to check command status
check_status() {
    if [ $? -eq 0 ]; then
        echo "✅ $1 successful"
    else
        echo "❌ $1 failed"
        exit 1
    fi
}

# Clean up any existing NVIDIA files
echo "0. Cleaning up existing NVIDIA repository files..."
rm -f /etc/apt/sources.list.d/nvidia-container-toolkit.list
rm -f /etc/apt/sources.list.d/nvidia.list
check_status "Cleanup"

echo "1. Adding NVIDIA repository..."
curl -fsSL https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb -O
dpkg -i cuda-keyring_1.1-1_all.deb
check_status "NVIDIA repository setup"

echo "2. Updating package lists..."
apt-get update
check_status "Package list update"

echo "3. Installing system dependencies..."
apt-get install -y linux-headers-$(uname -r) software-properties-common
check_status "System dependencies installation"

echo "4. Installing NVIDIA drivers..."
DEBIAN_FRONTEND=noninteractive apt-get install -y nvidia-driver-535 nvidia-dkms-535
check_status "NVIDIA driver installation"

echo "5. Adding NVIDIA Container Toolkit repository..."
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
    gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

echo "deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://nvidia.github.io/libnvidia-container/stable/ubuntu22.04/$(dpkg --print-architecture) /" | \
    tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
check_status "Repository configuration"

# Install Docker
echo "Installing Docker..."
if ! command -v docker &> /dev/null; then
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    # Start and enable Docker service
    systemctl start docker
    systemctl enable docker

    # Add ubuntu user to docker group
    usermod -aG docker ubuntu
fi

echo "6. Installing NVIDIA Container Toolkit..."
apt-get update
apt-get install -y nvidia-container-toolkit
check_status "Container toolkit installation"

echo "7. Configuring Docker runtime..."
nvidia-ctk runtime configure --runtime=docker
check_status "Docker runtime configuration"

echo "8. Restarting Docker service..."
systemctl restart docker
check_status "Docker restart"

echo "9. Verifying NVIDIA driver installation..."
nvidia-smi
check_status "NVIDIA driver verification"

echo "10. Installing CUDA Toolkit..."
apt-get install -y cuda-toolkit-12-4
check_status "CUDA Toolkit installation"

# Set up CUDA paths
echo 'export PATH=/usr/local/cuda-12.4/bin:$PATH' >> /etc/profile.d/cuda.sh
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.4/lib64:$LD_LIBRARY_PATH' >> /etc/profile.d/cuda.sh
source /etc/profile.d/cuda.sh

# Verify CUDA installation
nvcc --version
check_status "CUDA verification"

echo "✅ NVIDIA setup completed successfully"

# Now decode and run deploy script
echo "Starting Ralph and Chatbot deployment..."
echo "${deploy_script}" | base64 -d > /opt/deploy.sh
chmod +x /opt/deploy.sh
/opt/deploy.sh

echo "✅ System setup completed"