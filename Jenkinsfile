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
                // Clean workspace and get latest code
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

                        // SSH configuration - our tunnel through the infrastructure
                        def sshOptions = "-o StrictHostKeyChecking=no -o ProxyCommand=\"ssh -W %h:%p -i ${SSH_KEY_PATH} ubuntu@${bastionIp}\""

                        ec2_ips.each { ip ->
                            // Check if Ralph is already running on this instance
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
                                echo "📦 Time to welcome Ralph to its new home on ${ip}!"
                                sh """
                                    ssh ${sshOptions} ubuntu@${ip} '
                                        # Setup workspace
                                        cd /home/ubuntu
                                        git clone https://github.com/allegro/ralph.git
                                        cd ralph/docker
                                        
                                        # Start containers
                                        docker compose up -d
                                        
                                        # Wait for services to initialize
                                        sleep 30
                                        
                                        # Migrate database
                                        docker compose exec -T web ralphctl migrate
                                        
                                        # Create superuser using credentials from Jenkins
                                        echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('\\"$SUPERUSER_NAME\\"', '\\"team@cloudega.com\\"', '\\"$SUPERUSER_PASSWORD\\"') if not User.objects.filter(username='\\"$SUPERUSER_NAME\\"').exists() else None" | docker compose exec -T web python manage.py shell
                                        
                                        # Load demo data
                                        docker compose exec -T web ralphctl demodata
                                        
                                        # Sync site tree
                                        docker compose exec -T web ralphctl sitetree_resync_apps
                                        
                                        # Log setup completion with properly escaped dollar sign
                                        echo "Ralph Instance Setup Successfully on \\\$(date)" > /home/ubuntu/ralph_setup.log
                                        
                                        # Set ownership
                                        sudo chown -R ubuntu:ubuntu /home/ubuntu
                                    '
                                """
                                echo "🌟 Ralph is now ready to rock on ${ip}!"
                            } else {
                                echo "🔄 Just giving Ralph a quick refresh on ${ip}"
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
            echo "🎉 Pipeline completed successfully! Ralph is ready to roll!"
        }
        failure {
            echo "⚠️ Something went wrong. Check the logs above for details."
        }
    }
}
