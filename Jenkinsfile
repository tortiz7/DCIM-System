pipeline {
    // Execute pipeline on the designated build node configured for our deployment requirements
    agent {
        node {
            label 'cloudega-build-node'
        }
    }

    // Define critical environment variables for deployment configuration
    // These settings align with project requirements and infrastructure specifications
    environment {
        AWS_DEFAULT_REGION = 'us-east-1'  // Standardized region for project deployment
        APP_NAME = 'ralph'
        // SSH key location for secure instance access
        SSH_KEY_PATH = '/home/ubuntu/.ssh/shafee-jenkins-keypair.pem'
    }

    stages {
        // Initialize clean workspace and retrieve latest codebase
        // Ensures consistent deployment environment for each pipeline run
        stage('Setup') {
            steps {
                cleanWs()
                checkout scm
            }
        }

        // Execute infrastructure deployment using Terraform configurations
        // Utilizes secure credential management for sensitive information
        stage('Deploy Infrastructure') {
            steps {
                script {
                    // Access required credentials from Jenkins secure storage
                    // Critical for maintaining security of deployment process
                    withCredentials([
                        string(credentialsId: 'TF_VAR_db_username', variable: 'TF_VAR_db_username'),
                        string(credentialsId: 'TF_VAR_db_password', variable: 'TF_VAR_db_password'),
                        string(credentialsId: 'TF_VAR_dockerhub_user', variable: 'TF_VAR_dockerhub_user'),
                        string(credentialsId: 'TF_VAR_dockerhub_pass', variable: 'TF_VAR_dockerhub_pass'),
                        string(credentialsId: 'TF_VAR_region', variable: 'TF_VAR_region')
                    ]) {
                        sh """
                            cd terraform
                            terraform init
                            terraform plan -out=tfplan
                            terraform apply -auto-approve tfplan
                        """
                    }
                }
            }
        }

        // Validate instance configuration and service readiness
        // Ensures all required services are operational before deployment
        stage('Verify Instance Setup') {
            steps {
                script {
                    // Retrieve instance information from Terraform outputs
                    def ec2_ips = sh(
                        script: "cd terraform && terraform output -json private_instance_ips | jq -r '.[]'",
                        returnStdout: true
                    ).trim().split('\n')

                    def bastionIp = sh(
                        script: "cd terraform && terraform output -json bastion_public_ip | jq -r '.'",
                        returnStdout: true
                    ).trim()

                    // Configure SSH access through bastion host with security parameters
                    def sshOptions = "-o StrictHostKeyChecking=no -o 'ProxyCommand=ssh -o StrictHostKeyChecking=no -W %h:%p -i ${SSH_KEY_PATH} ubuntu@${bastionIp}' -i ${SSH_KEY_PATH}"

                    // Verify essential services on each instance
                    // Ensures Docker and monitoring services are operational
                    ec2_ips.each { ip ->
                        timeout(time: 5, unit: 'MINUTES') {
                            waitUntil {
                                def setupComplete = sh(
                                    script: """
                                        set -x
                                        echo "Verifying setup on ${ip} through bastion ${bastionIp}..."
                                        ssh ${sshOptions} ubuntu@${ip} '
                                            test -f /home/ubuntu/.setup_complete && 
                                            systemctl is-active --quiet docker && 
                                            systemctl is-active --quiet node_exporter
                                        '
                                        echo "Verification completed successfully"
                                    """,
                                    returnStatus: true
                                ) == 0
                                
                                if (!setupComplete) {
                                    sleep(15)
                                }
                                return setupComplete
                            }
                        }
                    }
                }
            }
        }

        // Deploy Ralph application to verified instances
        // Includes database migration and initial system configuration
        stage('Deploy Ralph') {
            steps {
                script {
                    withCredentials([
                        string(credentialsId: 'RALPH_SUPERUSER_USERNAME', variable: 'SUPERUSER_NAME'),
                        string(credentialsId: 'RALPH_SUPERUSER_PASSWORD', variable: 'SUPERUSER_PASSWORD')
                    ]) {
                        def ec2_ips = sh(
                            script: "cd terraform && terraform output -json private_instance_ips | jq -r '.[]'",
                            returnStdout: true
                        ).trim().split('\n')

                        def bastionIp = sh(
                            script: "cd terraform && terraform output -json bastion_public_ip | jq -r '.'",
                            returnStdout: true
                        ).trim()

                        def sshOptions = "-o StrictHostKeyChecking=no -o 'ProxyCommand=ssh -o StrictHostKeyChecking=no -W %h:%p -i ${SSH_KEY_PATH} ubuntu@${bastionIp}' -i ${SSH_KEY_PATH}"

                        // Execute deployment process for each instance
                        // Includes new deployment or update based on current state
                        ec2_ips.each { ip ->
                            def isRalphRunning = sh(
                                script: """
                                    ssh ${sshOptions} ubuntu@${ip} '
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
                                echo "Initiating new Ralph deployment on ${ip}"
                                sh """
                                    ssh ${sshOptions} ubuntu@${ip} '
                                        cd /home/ubuntu
                                        
                                        # TODO: Change repo to Cloudega repo
                                        git clone https://github.com/allegro/ralph.git
                                        cd ralph/docker
                                        
                                        docker compose up -d
                                        sleep 30

                                        # Create the necessary directory structure first
                                        sudo mkdir -p /etc/ralph/conf.d
                                        
                                        docker compose exec -T web ralphctl migrate
                                        docker compose exec -T web ralphctl shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('${SUPERUSER_NAME}', 'team@cloudega.com', '${SUPERUSER_PASSWORD}') if not User.objects.filter(username='${SUPERUSER_NAME}').exists() else None"
                                        docker compose exec -T web ralphctl demodata
                                        docker compose exec -T web ralphctl sitetree_resync_apps
                                        
                                        echo "LOGIN_REDIRECT_URL = /" >> /etc/ralph/conf.d/settings.conf
                                        echo "ALLOWED_HOSTS = [\\"*\\"]" >> /etc/ralph/conf.d/settings.conf
                                    '
                                """
                                echo "Ralph deployment completed successfully on ${ip}"
                            } else {
                                echo "Updating existing Ralph deployment on ${ip}"
                                sh """
                                    ssh ${sshOptions} ubuntu@${ip} '
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
        }
    }

    // Pipeline completion handling
    post {
        success {
            echo "Pipeline execution completed successfully. Ralph deployment is operational."
        }
        failure {
            echo "Pipeline execution encountered errors. Please review logs for troubleshooting."
        }
    }
}