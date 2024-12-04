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
        INFRASTRUCTURE_LOCK = 'ralph-infrastructure-lock'
    }

    stages {
        stage('Setup') {
            steps {
                cleanWs()
                checkout scm
            }
        }

        stage('Check Infrastructure') {
            steps {
                script {
                    // Get a lock to prevent parallel infrastructure modifications
                    lock(resource: env.INFRASTRUCTURE_LOCK) {
                        echo "🔍 Checking if our infrastructure already exists..."
                        
                        def infrastructureExists = false
                        try {
                            // Check for VPC with our specific tag
                            def vpcExists = sh(
                                script: "aws ec2 describe-vpcs --filters 'Name=tag:Name,Values=customVPC' --query 'Vpcs[*]' --output text",
                                returnStdout: true
                            ).trim()
                            
                            // Check for RDS instance
                            def rdsExists = sh(
                                script: "aws rds describe-db-instances --db-instance-identifier ralphng --query 'DBInstances[*]' --output text",
                                returnStdout: true
                            ).trim()
                            
                            // If both exist, we'll consider our infrastructure as existing
                            infrastructureExists = vpcExists != "" && rdsExists != ""
                            
                            if (infrastructureExists) {
                                echo "🌟 Great news! Our infrastructure is already up and running!"
                                env.SKIP_INFRASTRUCTURE = 'true'
                            } else {
                                echo "🏗️ Looks like we need to set up our infrastructure..."
                                env.SKIP_INFRASTRUCTURE = 'false'
                            }
                        } catch (Exception e) {
                            echo "⚠️ Couldn't check infrastructure status. Assuming we need to create it."
                            env.SKIP_INFRASTRUCTURE = 'false'
                        }
                    }
                }
            }
        }

        stage('Deploy or Update Infrastructure') {
            steps {
                script {
                    lock(resource: env.INFRASTRUCTURE_LOCK) {
                        withCredentials([
                            string(credentialsId: 'TF_VAR_db_username', variable: 'TF_VAR_db_username'),
                            string(credentialsId: 'TF_VAR_db_password', variable: 'TF_VAR_db_password'),
                            string(credentialsId: 'TF_VAR_dockerhub_user', variable: 'TF_VAR_dockerhub_user'),
                            string(credentialsId: 'TF_VAR_dockerhub_pass', variable: 'TF_VAR_dockerhub_pass'),
                            string(credentialsId: 'TF_VAR_region', variable: 'TF_VAR_region')
                        ]) {
                            echo "🔍 Checking for infrastructure changes..."
                            sh """
                                cd terraform
                                terraform init
                                terraform workspace select dev || terraform workspace new dev
                                terraform plan -out=tfplan | tee plan.txt
                            """
                            
                            // Check if there are any changes in the plan
                            def planHasChanges = sh(
                                script: "grep -q 'No changes.' plan.txt || true",
                                returnStatus: true
                            ) == 1
                            
                            if (planHasChanges) {
                                echo "🔄 Found changes in infrastructure! Let's apply them..."
                                sh """
                                    cd terraform
                                    terraform apply -auto-approve tfplan
                                """
                                echo "✨ Infrastructure updates have been applied!"
                            } else {
                                echo "👍 Infrastructure is up to date - no changes needed!"
                            }
                            
                            // Clean up plan files
                            sh "rm -f terraform/plan.txt terraform/tfplan"
                        }
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

                    echo "🔍 Verifying our instances are ready to rock..."
                    ec2_ips.each { ip ->
                        timeout(time: 5, unit: 'MINUTES') {
                            waitUntil {
                                def setupComplete = sh(
                                    script: """
                                        ssh ${sshOptions} ubuntu@${ip} '
                                            test -f /home/ubuntu/.setup_complete && 
                                            systemctl is-active --quiet docker && 
                                            systemctl is-active --quiet node_exporter
                                        '
                                    """,
                                    returnStatus: true
                                ) == 0
                                
                                if (!setupComplete) {
                                    echo "⏳ Instance ${ip} is still getting ready. Let's give it a moment..."
                                    sleep(15)
                                } else {
                                    echo "✅ Instance ${ip} is good to go!"
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
                                echo "🚀 Time to deploy Ralph on ${ip}!"
                                sh """
                                    ssh ${sshOptions} ubuntu@${ip} '
                                        cd /home/ubuntu
                                        git clone https://github.com/allegro/ralph.git || (cd ralph && git pull)
                                        cd ralph/docker
                                        
                                        docker compose up -d
                                        
                                        echo "⏳ Giving the containers a moment to warm up..."
                                        sleep 30
                                        
                                        docker compose exec -T web ralphctl migrate
                                        
                                        echo "Creating superuser if it doesn't exist..."
                                        echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('\\"$SUPERUSER_NAME\\"', '\\"team@cloudega.com\\"', '\\"$SUPERUSER_PASSWORD\\"') if not User.objects.filter(username='\\"$SUPERUSER_NAME\\"').exists() else None" | docker compose exec -T web python manage.py shell
                                        
                                        docker compose exec -T web ralphctl demodata
                                        
                                        docker compose exec -T web ralphctl sitetree_resync_apps
                                    '
                                """
                                echo "🌟 Ralph is ready to roll on ${ip}!"
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
            echo "🎉 Pipeline completed successfully! Ralph is ready to rock!"
        }
        failure {
            echo "⚠️ Uh oh! Something went wrong. Check the logs above for details."
        }
    }
}