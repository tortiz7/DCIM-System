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

        stage('Verify Instance Setup') {
            steps {
                script {
                    def ec2_ips = sh(
                        script: "cd terraform && terraform output -json private_instance_ips | jq -r '.[]'",
                        returnStdout: true
                    ).trim().split('\\n')

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
                                    sleep 15
                                }
                                return setupComplete
                            }
                        }
                    }
                }
            }
        }

        stage('Test') {
            steps {
                script {
                    echo "🔧 Running placeholder tests..."
                    sh 'echo "No real tests yet. Passing by default."'
                }
            }
        }

        stage('Build and Push Docker Image') {
            steps {
                script {
                    withCredentials([
                        string(credentialsId: 'TF_VAR_dockerhub_user', variable: 'DOCKERHUB_USER'),
                        string(credentialsId: 'TF_VAR_dockerhub_pass', variable: 'DOCKERHUB_PASS')
                    ]) {
                        echo "🔨 Building Docker image for Ralph..."

                        sh """
                            docker login -u $DOCKERHUB_USER -p $DOCKERHUB_PASS
                            docker build -t shafeekuralabs/ralph:latest -f docker/Dockerfile-prod .
                            docker push shafeekuralabs/ralph:latest
                        """
                        echo "✅ Docker image pushed to DockerHub as shafeekuralabs/ralph:latest"
                    }
                }
            }
        }
        
        stage('Security Scan') {
            steps {
                echo "🔒 Scanning Docker image for vulnerabilities..."
                sh """
                    mkdir -p /home/ubuntu/trivy-archives
                    mkdir -p /home/ubuntu/trivy-cache
                        
                    # Run the vulnerability scan with caching and vuln-only scanners
                    docker run --rm \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        -v /home/ubuntu/trivy-cache:/root/.cache/ \
                        aquasec/trivy:latest image --scanners vuln --severity HIGH,CRITICAL shafeekuralabs/ralph:latest > trivy-report.txt

                    cp trivy-report.txt /home/ubuntu/trivy-archives/
                """
                archiveArtifacts artifacts: 'trivy-report.txt', fingerprint: true
                echo "✅ Security scan report saved in both the build artifacts and /home/ubuntu/trivy-archives/"
            }
        }

        stage('Deploy Ralph') {
            steps {
                script {
                    withCredentials([
                        string(credentialsId: 'RALPH_SUPERUSER_USERNAME', variable: 'SUPERUSER_NAME'),
                        string(credentialsId: 'RALPH_SUPERUSER_PASSWORD', variable: 'SUPERUSER_PASSWORD'),
                        string(credentialsId: 'GITHUB_TOKEN', variable: 'GITHUB_TOKEN')
                    ]) {
                        def ec2_ips = sh(
                            script: "cd terraform && terraform output -json private_instance_ips | jq -r '.[]'",
                            returnStdout: true
                        ).trim().split('\\n')

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
                                echo "📦 Time to deploy Ralph on ${ip}!"
                                sh """
                                    ssh ${sshOptions} ubuntu@${ip} '
                                        cd /home/ubuntu

                                        # Pull and run the image
                                        docker compose pull
                                        docker compose up -d
                                        sleep 30

                                        # Run migrations
                                        docker compose exec -T web ralphctl migrate

                                        # Create or update superuser (all in one line)
                                        docker compose exec -T web ralphctl shell -c "from django.contrib.auth import get_user_model; User=get_user_model(); user,created=User.objects.get_or_create(username=\\"${SUPERUSER_NAME}\\", defaults={\\"email\\":\\"team@cloudega.com\\"}); user.is_staff=True; user.is_superuser=True; user.set_password(\\"${SUPERUSER_PASSWORD}\\"); user.save(); print(f\\"User: {user.username}, Staff: {user.is_staff}, Superuser: {user.is_superuser}\\")"

                                        # Load demo data
                                        docker compose exec -T web ralphctl demodata
                                        docker compose exec -T web ralphctl sitetree_resync_apps

                                        # Adjust permissions for /etc/ralph/conf.d/settings.conf
                                        docker compose exec -T -u root web bash -c "mkdir -p /etc/ralph/conf.d && touch /etc/ralph/conf.d/settings.conf && chown root:root /etc/ralph/conf.d/settings.conf && chmod 644 /etc/ralph/conf.d/settings.conf"
                                    '
                                """
                                echo "🌟 Ralph is now configured and ready on ${ip}!"
                            } else {
                                echo "🔄 Ralph is already running on ${ip}, updating it..."
                                sh """
                                    ssh ${sshOptions} ubuntu@${ip} '
                                        cd /home/ubuntu/ralph-pipeline-test/docker
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

        stage('Smoke Test') {
            steps {
                script {
                    echo "🔎 Running a smoke test against the load balancer..."
                    def alb_dns = sh(
                        script: "cd terraform && terraform output -json alb_dns_name | jq -r '.'",
                        returnStdout: true
                    ).trim()

                    // Simple curl check to verify a 200 response from the Ralph login page
                    def status = sh(script: "curl -s -o /dev/null -w '%{http_code}' http://${alb_dns}/login/", returnStdout: true).trim()

                    if (status != '200') {
                        error("Smoke test failed! Expected 200 OK from ${alb_dns}/login/ but got ${status}")
                    }

                    echo "✅ Smoke test passed! The Ralph application is responding as expected."
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
