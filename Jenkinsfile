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

        stage('Verify Instance Setup') {
            steps {
                script {
                    def ec2_ips = sh(
                        script: "cd terraform && terraform output -json private_instance_ips | jq -r '.[]'",
                        returnStdout: true
                    ).trim().split('\n')

                    def bastionIp = sh(
                        script: "cd terraform && terraform output -json bastion_public_ip | jq -r '.'",
                        returnStdout: true
                    ).trim()

                    def sshOptions = "-o StrictHostKeyChecking=no -o 'ProxyCommand=ssh -o StrictHostKeyChecking=no -W %h:%p -i ${SSH_KEY_PATH} ubuntu@${bastionIp}' -i ${SSH_KEY_PATH}"

                    ec2_ips.each { ip ->
                        timeout(time: 5, unit: 'MINUTES') {
                            waitUntil {
                                def setupComplete = sh(
                                        script: """
                                            set -x  # Enable debug mode
                                            echo "Attempting to connect to ${ip} through bastion ${bastionIp}..."
                                            ssh ${sshOptions} ubuntu@${ip} '
                                                test -f /home/ubuntu/.setup_complete && 
                                                systemctl is-active --quiet docker && 
                                                systemctl is-active --quiet node_exporter
                                            '
                                            echo "Connection and verification completed successfully"
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
                                echo "📦 Time to welcome Ralph to its new home on ${ip}!"
                                sh """
                                    ssh ${sshOptions} ubuntu@${ip} '
                                        cd /home/ubuntu
                                        git clone https://github.com/allegro/ralph.git
                                        cd ralph/docker
                                        
                                        docker compose -f /home/ubuntu/docker-compose.yml up -d
                                        
                                        sleep 30
                                        
                                        docker compose -f /home/ubuntu/docker-compose.yml exec -T web ralphctl migrate
                                        
                                        echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('\\"$SUPERUSER_NAME\\"', '\\"team@cloudega.com\\"', '\\"$SUPERUSER_PASSWORD\\"') if not User.objects.filter(username='\\"$SUPERUSER_NAME\\"').exists() else None" | docker compose -f /home/ubuntu/docker-compose.yml exec -T web python ralphctl shell
                                        
                                        docker compose -f /home/ubuntu/docker-compose.yml exec -T web ralphctl demodata
                                        
                                        docker compose -f /home/ubuntu/docker-compose.yml exec -T web ralphctl sitetree_resync_apps
                                    '
                                """
                                echo "🌟 Ralph is now ready to rock on ${ip}!"
                            } else {
                                echo "🔄 Just giving Ralph a quick refresh on ${ip}"
                                sh """
                                    ssh ${sshOptions} ubuntu@${ip} '
                                        cd /home/ubuntu/ralph/docker
                                        git pull
                                        docker compose -f /home/ubuntu/docker-compose.yml pull
                                        docker compose -f /home/ubuntu/docker-compose.yml up -d
                                        docker compose -f /home/ubuntu/docker-compose.yml exec -T web ralphctl migrate
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