# Configure the AWS provider block. This tells Terraform which cloud provider to use and 
# how to authenticate (access key, secret key, and region) when provisioning resources.
# Note: Hardcoding credentials is not recommended for production use. Instead, use environment variables
# or IAM roles to manage credentials securely.
provider "aws" {
  region = var.region
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