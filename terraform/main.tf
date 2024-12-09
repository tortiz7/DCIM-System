# Configure the AWS provider block. This tells Terraform which cloud provider to use and 
# how to authenticate (access key, secret key, and region) when provisioning resources.
# Note: Hardcoding credentials is not recommended for production use. Instead, use environment variables
# or IAM roles to manage credentials securely.
provider "aws" {
  region = var.region
  access_key = var.access_key
  secret_key = var.secret_key
}


module "VPC"{
  source = "./VPC"
} 

module "EC2"{
  source = "./EC2"
  vpc_id = module.VPC.vpc_id
  public_subnet = module.VPC.public_subnet
  private_subnet = module.VPC.private_subnet
  instance_type = var.instance_type
  region = var.region
  app_count = var.app_count
  bastion_count = var.bastion_count
  db_name = var.db_name
  db_username = var.db_username
  db_password = var.db_password
  rds_address = module.RDS.rds_address
  rds_endpoint = module.RDS.rds_endpoint
  postgres_db = module.RDS.postgres_db
  rds_sg_id = module.RDS.rds_sg_id
  alb_sg_id = module.ALB.alb_sg_id
  app_port = var.app_port
  dockerhub_user = var.dockerhub_user
  dockerhub_pass = var.dockerhub_pass
  nat_gw = module.VPC.nat_gw
  redis_endpoint = module.RDS.redis_endpoint
  redis_port = module.RDS.redis_port
  redis_sg_id = module.RDS.redis_sg_id
  alb_dns_name = module.ALB.alb_dns_name
  ssh_private_key = var.ssh_private_key
}

module "RDS"{
  source = "./RDS"
  db_instance_class = var.db_instance_class
  db_name           = var.db_name
  db_username       = var.db_username
  db_password       = var.db_password
  vpc_id            = module.VPC.vpc_id
  private_subnet    = module.VPC.private_subnet
  app_sg_id     = module.EC2.app_sg_id

}

module "ALB"{
  source = "./ALB"
  alb_name = var.alb_name
  app_port = var.app_port
  app_count = var.app_count
  bastion_count = var.bastion_count
  app_server_ids = module.EC2.app_server_ids
  #bastion_server_ids = module.EC2.bastion_server_ids
  public_subnet = module.VPC.public_subnet
  vpc_id = module.VPC.vpc_id

}

output "bastion_public_ip" {
    value       = module.EC2.bastion_public_ip
    description = "Public IP of the bastion host for SSH access"
}

output "private_instance_ips" {
    value       = module.EC2.private_instance_ips
    description = "Private IPs of all application instances"
}

output "alb_dns_name" {
    value       = module.ALB.alb_dns_name
    description = "DNS name of the Application Load Balancer"
    sensitive   = false
}

# resource "null_resource" "docker_build" {
#   provisioner "local-exec" {
#     command = <<EOT
#     echo "${var.ssh_private_key}" > /tmp/docker_ssh_key
#     chmod 600 /tmp/docker_ssh_key
#     DOCKER_BUILDKIT=1 docker build --ssh default=/tmp/docker_ssh_key -t tortiz7/ralph_chatbot_v2:latest .
#     EOT
#   }
# }