# Prospective Pipeline

#### 👋 As we move forward with setting up our infrastructure for Ralph, I wanted to share our deployment strategy. This document outlines how we'll get Ralph up and running across our EC2 instances with a shared team access setup.

## Important Team Notes

Once deployed, we'll all use these initial credentials to access Ralph:

**Username:** cloudega2024

**Email:** team@cloudega.com

**Initial Password:** cloudega2024!

Below is our server initialization script that handles everything from Docker installation to Ralph configuration. It sets up shared team access so we can all log in with the same credentials. This template file will be used alongside our deploy.sh.

```bash
#!/bin/bash

# system updates and Docker installation (keeping your existing Docker setup)
apt-get update
apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git

# add Docker's official GPG key
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# set up the Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine and Docker Compose
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start and enable Docker service
systemctl start docker
systemctl enable docker

# Create working directory and clone Ralph
cd /home/ubuntu
git clone https://github.com/allegro/ralph.git
cd ralph/docker

# Start Ralph containers
docker compose up -d

# Wait for the web container to be ready (give it about 30 seconds)
sleep 30

# Initialize Ralph
docker compose exec -T web ralphctl migrate

# Create team account
echo "from django.contrib.auth import get_user_model; \
User = get_user_model(); \
User.objects.create_superuser( \
    'cloudega2024', \
    'team@cloudega.com', \
    'cloudega2024!' \
) if not User.objects.filter(username='teamralph').exists() else None" | \
docker compose exec -T web python manage.py shell

# load demo data and sync menu
docker compose exec -T web ralphctl demodata
docker compose exec -T web ralphctl sitetree_resync_apps

# write setup information to config file
cat << EOF > /home/ubuntu/ralph_config.txt
Server Name: ${server_name}
Environment: ${environment}
Created On: $(date)
Server Number: ${server_number}
Ralph URL: http://localhost:8080
Default Admin Username: admin
Default Admin Password: admin12345
Note: Please change the default admin password immediately!
EOF

# make sure ubuntu user owns all the files
chown -R ubuntu:ubuntu /home/ubuntu
```

### 👉 What This Script Does

1. Sets up all necessary system dependencies
2. Installs and configures Docker
3. Clones and initializes Ralph
4. Creates our shared team account
5. Loads demo data and configures the menu
6. Saves all important config info locally

<br >

## Jenkins Pipeline Configuration

Here's how the below workflow would actually work:

1. Someone on the team pushes a change to GitHub
2. Jenkins sees the change and kicks off the pipeline
3. If it's the first run, it creates your infrastructure
4. If infrastructure exists, it just updates Ralph on your EC2s

```groovy
pipeline {
    agent any

    environment {
        AWS_DEFAULT_REGION = 'us-east-1'
        APP_NAME = 'ralph'
    }

    stages {
        stage('Setup') {
            steps {
                // clean workspace and get latest code
                cleanWs()
                checkout scm
            }
        }

        // this part just makes sure we're working with the latest version of everything
        // if the infrastructure is already created, Terraform is smart enough to know what's already there
        stage('Deploy Infrastructure') {
            steps {
                // only run Terraform if infrastructure doesn't exist
                script {
                    sh """
                        cd terraform
                        terraform init
                        terraform plan -out=tfplan
                        terraform apply -auto-approve tfplan
                    """
                }
            }
        }

        // this is just making sure Ralph is up-to-date on all our servers. Think maintenance checks
        stage('Deploy Ralph') {
            steps {
                script {
                    def ec2_ips = sh(
                        script: "cd terraform && terraform output -json private_instance_ips | jq -r '.[]'",
                        returnStdout: true
                    ).trim().split('\n')

                    ec2_ips.each { ip ->
                        // first order of business is to check if Ralph is already running
                        def isRalphRunning = sh(
                            script: """
                                ssh ubuntu@${ip} '
                                    if docker ps | grep -q ralph; then
                                        echo "true"
                                    else
                                        echo "false"
                                    fi
                                '
                            """,
                            returnStdout: true
                        ).trim()

                if (isRalphRunning == 'false') {
                    // this is for first time setup
                    sh """
                        ssh ubuntu@${ip} '
                            cd /home/ubuntu
                            git clone https://github.com/allegro/ralph.git
                            cd ralph/docker
                            docker compose up -d
                            sleep 30  # Give containers time to start
                            docker compose exec -T web ralphctl migrate
                            # Create our team account
                            echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('cloudega2024', 'team@cloudega.com', 'cloudega2024!') if not User.objects.filter(username='cloudega2024').exists() else None" | docker compose exec -T web python manage.py shell
                        '
                    """
                } else {
                    // just update existing installation
                    sh """
                        ssh ubuntu@${ip} '
                            cd /home/ubuntu/ralph/docker
                            git pull
                            docker compose pull
                            docker compose up -d
                            docker compose exec -T web ralphctl migrate
                        '
                    """
                }
            }
        }
    }
}
```
