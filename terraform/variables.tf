variable region{
  type = string
}

variable access_key{
  type = string
  sensitive = true
}

variable secret_key{
  type = string
  sensitive = true
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
  default = "g4dn.xlarge"

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
  default     = "ralph_ng"
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
  default = 80
}

variable "bastion_port" {
  default = 22
}

variable "ssh_private_key" {
  type = string
  sensitive = true
}

variable "github_token" {
  type = string
  sensitive = true
}