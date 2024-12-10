pipeline {
    agent {
        node {
            label 'cloudega-build-node'
        }
    }

    environment {
        AWS_DEFAULT_REGION = 'us-east-1'
        APP_NAME = 'ralph'
        SSH_KEY_PATH = '/home/ubuntu/.ssh/shafee-jenkins-keypair.pem'
    }

    stages {
        stage('Setup') {
            steps {
                cleanWs()
                checkout scm
            }
        }

        stage('Deploy Infrastructure') {
            steps {
                script {
                    withCredentials([
                        string(credentialsId: 'TF_VAR_db_username', variable: 'TF_VAR_db_username'),
                        string(credentialsId: 'TF_VAR_db_password', variable: 'TF_VAR_db_password'),
                        string(credentialsId: 'TF_VAR_dockerhub_user', variable: 'TF_VAR_dockerhub_user'),
                        string(credentialsId: 'TF_VAR_dockerhub_pass', variable: 'TF_VAR_dockerhub_pass'),
                        string(credentialsId: 'TF_VAR_region', variable: 'TF_VAR_region'),
                        usernamePassword(credentialsId: 'aws-credentials', usernameVariable: 'AWS_ACCESS_KEY_ID', passwordVariable: 'AWS_SECRET_ACCESS_KEY')
                    ]) {
                        sh """
                            cd terraform
                            terraform init -input=false -reconfigure
                            terraform plan -out=tfplan
                            terraform apply -auto-approve tfplan
                        """
                    }
                }
            }
        }

        stage('Get Infrastructure Outputs') {
            steps {
                script {
                    // Get instance IPs, bastion IP, and ALB URL from Terraform outputs dynamically
                    ec2_ips = sh(
                        script: "cd terraform && terraform output -json private_instance_ips | jq -r '.[]'",
                        returnStdout: true
                    ).trim().split('\n')

                    bastionIp = sh(
                        script: "cd terraform && terraform output -json bastion_public_ip | jq -r '.'",
                        returnStdout: true
                    ).trim()

                    albUrl = sh(
                        script: "cd terraform && terraform output -json alb_dns_name | jq -r '.'",
                        returnStdout: true
                    ).trim()

                    // Construct SSH options now that we have bastionIp
                    sshOptions = "-o StrictHostKeyChecking=no -o 'ProxyCommand=ssh -o StrictHostKeyChecking=no -W %h:%p -i ${SSH_KEY_PATH} ubuntu@${bastionIp}' -i ${SSH_KEY_PATH}"
                }
            }
        }

        stage('Verify Instance Setup') {
            steps {
                script {
                    ec2_ips.each { ip ->
                        timeout(time: 5, unit: 'MINUTES') {
                            waitUntil {
                                def setupComplete = (sh(
                                    script: """
                                        ssh ${sshOptions} ubuntu@${ip} '
                                            test -f /home/ubuntu/.setup_complete && 
                                            systemctl is-active --quiet docker && 
                                            systemctl is-active --quiet node_exporter
                                        '
                                    """,
                                    returnStatus: true
                                ) == 0)

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

        stage('Deploy Ralph') {
            steps {
                script {
                    withCredentials([
                        string(credentialsId: 'RALPH_SUPERUSER_USERNAME', variable: 'SUPERUSER_NAME'),
                        string(credentialsId: 'RALPH_SUPERUSER_PASSWORD', variable: 'SUPERUSER_PASSWORD')
                    ]) {
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
                                echo "📦 Ralph not found on ${ip}, deploying fresh..."
                                sh """
                                    ssh ${sshOptions} ubuntu@${ip} '
                                        cd /home/ubuntu
                                        rm -rf ralph
                                        git clone https://github.com/allegro/ralph.git
                                        cd ralph/docker
                                        
                                        docker compose pull
                                        docker compose up -d
                                        sleep 30

                                        docker compose exec -T web ralphctl migrate
                                        docker compose exec -T web ralphctl shell -c "
from django.contrib.auth import get_user_model; 
User = get_user_model(); 
user, created = User.objects.get_or_create(username=\\"${SUPERUSER_NAME}\\", defaults={\\"email\\":\\"team@cloudega.com\\"});
user.is_staff = True
user.is_superuser = True
user.set_password(\\"${SUPERUSER_PASSWORD}\\")
user.save()
"

                                        docker compose exec -T web ralphctl demodata
                                        docker compose exec -T web ralphctl sitetree_resync_apps

                                        # Write the full configuration once, using the ALB URL retrieved dynamically
                                        docker compose exec -T -u root web bash -c "cat > /etc/ralph/conf.d/settings.conf <<EOF
LOGIN_REDIRECT_URL = \\"/\\"
ALLOWED_HOSTS = [\\"*\\"] 
CSRF_TRUSTED_ORIGINS = [\\"http://${albUrl}\\"] 
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
EOF"

                                        docker compose restart web
                                    '
                                """
                                echo "🌟 Ralph is now configured and ready on ${ip}!"
                            } else {
                                echo "🔄 Ralph is running on ${ip}, updating..."
                                sh """
                                    ssh ${sshOptions} ubuntu@${ip} '
                                        cd /home/ubuntu/ralph
                                        git pull
                                        cd docker
                                        docker compose pull
                                        docker compose up -d
                                        docker compose exec -T web ralphctl migrate

                                        # Overwrite settings.conf again with the updated ALB URL
                                        docker compose exec -T -u root web bash -c "cat > /etc/ralph/conf.d/settings.conf <<EOF
LOGIN_REDIRECT_URL = \\"/\\"
ALLOWED_HOSTS = [\\"*\\"] 
CSRF_TRUSTED_ORIGINS = [\\"http://${albUrl}\\"] 
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
EOF"
                                        docker compose restart web
                                    '
                                """
                            }
                        }
                    }
                }
            }
        }
    }

    post {
        success {
            echo "🎉 Pipeline completed successfully! Ralph should be ready to roll!"
        }
        failure {
            echo "⚠️ Something went wrong. Check the logs above for details."
        }
    }
}
