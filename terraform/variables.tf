 variable aws_access_key{
    type = string
    sensitive = true
 }                                                    # Replace with your AWS access key ID (leave empty if using IAM roles or env vars)
 
 variable aws_secret_key{
    type = string
    sensitive = true
 }                                        # Replace with your AWS secret access key (leave empty if using IAM roles or env vars)

variable region{
  type = string
}

 variable dockerhub_user{
    type = string
    sensitive = true
 }

  variable dockerhub_pass{
    type = string
    sensitive = true
 }        

 variable instance_type{
  type = string
  default = "t2.micro"

 }  

variable "bastion_count"{
  type = number
  default = 2
}

variable "app_count"{
  type = number
  default = 2
}
 variable "db_instance_class" {
  description = "The instance type of the RDS instance"
  default     = "db.t3.micro"
}

variable "db_name" {
  description = "The name of the database to create when the DB instance is created"
  type        = string
  default     = "ecommerce"
}

variable "db_username" {
  description = "Username for the master DB user"
  type        = string
  sensitive = true
}

variable "db_password" {
  description = "Password for the master DB user"
  type        = string
  sensitive = true
}

variable "alb_name" {
  default = "app-alb"
}

variable "app_port" {
  default = 8000
}

variable "bastion_port" {
  default = 22
}