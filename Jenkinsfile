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
                // Clean the Jenkins workspace to ensure a fresh start for each build.
                cleanWs()
                // Check out the current branch's code from SCM (GitHub).
                checkout scm
            }
        }

        stage('Deploy Infrastructure') {
            steps {
                script {
                    // Injecting Terraform variables and AWS credentials into the environment.
                    withCredentials([
                        string(credentialsId: 'TF_VAR_db_username', variable: 'TF_VAR_db_username'),
                        string(credentialsId: 'TF_VAR_db_password', variable: 'TF_VAR_db_password'),
                        string(credentialsId: 'TF_VAR_dockerhub_user', variable: 'TF_VAR_dockerhub_user'),
                        string(credentialsId: 'TF_VAR_dockerhub_pass', variable: 'TF_VAR_dockerhub_pass'),
                        string(credentialsId: 'TF_VAR_region', variable: 'TF_VAR_region'),
                        usernamePassword(credentialsId: 'aws-credentials', usernameVariable: 'AWS_ACCESS_KEY_ID', passwordVariable: 'AWS_SECRET_ACCESS_KEY')
                    ]) {
                        // Initialize Terraform with the remote S3 backend, plan changes, and apply them.
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

        stage('Verify Instance Setup') {
            steps {
                script {
                    // Retrieve private instance IPs and bastion IP from Terraform outputs
                    def ec2_ips = sh(
                        script: "cd terraform && terraform output -json private_instance_ips | jq -r '.[]'",
                        returnStdout: true
                    ).trim().split('\n')

                    def bastionIp = sh(
                        script: "cd terraform && terraform output -json bastion_public_ip | jq -r '.'",
                        returnStdout: true
                    ).trim()

                    // Construct SSH options to go through the bastion host.
                    def sshOptions = "-o StrictHostKeyChecking=no -o 'ProxyCommand=ssh -o StrictHostKeyChecking=no -W %h:%p -i ${SSH_KEY_PATH} ubuntu@${bastionIp}' -i ${SSH_KEY_PATH}"

                    // Verify setup on each instance: check setup_complete file, docker, node_exporter
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
                                    // If not set up, wait 15 seconds and try again.
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
                    // Inject Ralph superuser credentials.
                    withCredentials([
                        string(credentialsId: 'RALPH_SUPERUSER_USERNAME', variable: 'SUPERUSER_NAME'),
                        string(credentialsId: 'RALPH_SUPERUSER_PASSWORD', variable: 'SUPERUSER_PASSWORD')
                    ]) {
                        // Get instance IPs again to deploy Ralph onto them.
                        def ec2_ips = sh(
                            script: "cd terraform && terraform output -json private_instance_ips | jq -r '.[]'",
                            returnStdout: true
                        ).trim().split('\n')

                        def bastionIp = sh(
                            script: "cd terraform && terraform output -json bastion_public_ip | jq -r '.'",
                            returnStdout: true
                        ).trim()

                        def sshOptions = "-o StrictHostKeyChecking=no -o 'ProxyCommand=ssh -o StrictHostKeyChecking=no -W %h:%p -i ${SSH_KEY_PATH} ubuntu@${bastionIp}' -i ${SSH_KEY_PATH}"

                        // For each instance, check if Ralph is running. If not, deploy and configure it.
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
                                echo "📦 Time to deploy Ralph on ${ip}!"
                                // Deploy Ralph if it's not already running.
                                sh """
                                    ssh ${sshOptions} ubuntu@${ip} '
                                        cd /home/ubuntu
                                        git clone https://github.com/allegro/ralph.git
                                        cd ralph/docker
                                        
                                        docker compose up -d
                                        sleep 30
                                        
                                        # Run migrations for Ralph
                                        docker compose exec -T web ralphctl migrate

                                        # Create or update superuser
                                        docker compose exec -T web ralphctl shell -c "
from django.contrib.auth import get_user_model; 
User = get_user_model(); 
user, created = User.objects.get_or_create(username=\\"${SUPERUSER_NAME}\\", defaults={\\"email\\":\\"team@cloudega.com\\"});
user.is_staff = True
user.is_superuser = True
user.set_password(\\"${SUPERUSER_PASSWORD}\\")
user.save()
print(f\\"User: {user.username}, Staff: {user.is_staff}, Superuser: {user.is_superuser}\\")
"

                                        # Load demo data and resync site trees
                                        docker compose exec -T web ralphctl demodata
                                        docker compose exec -T web ralphctl sitetree_resync_apps

                                        # Update settings for Ralph in /etc/ralph/conf.d/
                                        docker compose exec -T -u root web bash -c "mkdir -p /etc/ralph/conf.d && touch /etc/ralph/conf.d/settings.conf && chown root:root /etc/ralph/conf.d/settings.conf && chmod 666 /etc/ralph/conf.d/settings.conf"
                                        docker compose exec -T -u root web bash -c "echo \\"LOGIN_REDIRECT_URL = \\"/\\"\\" >> /etc/ralph/conf.d/settings.conf"
                                        docker compose exec -T -u root web bash -c "echo \\"ALLOWED_HOSTS = [\\"*\\"]\\" >> /etc/ralph/conf.d/settings.conf"
                                        docker compose exec -T -u root web bash -c "chmod 644 /etc/ralph/conf.d/settings.conf"
                                    '
                                """
                                echo "🌟 Ralph is now configured and ready on ${ip}!"
                            } else {
                                echo "🔄 Just refreshing Ralph on ${ip}"
                                // If Ralph is already running, just update it.
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

    post {
        success {
            echo "🎉 Pipeline completed successfully! Ralph should be ready to roll!"
        }
        failure {
            echo "⚠️ Something went wrong. Check the logs above for details."
        }
    }
}
