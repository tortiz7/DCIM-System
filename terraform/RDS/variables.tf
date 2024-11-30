variable "db_instance_class" {
}

variable "db_name" {
}

variable "db_username" {
}

variable "db_password" {
}

 variable "private_subnet"{
    type = list(string)
 }

 variable "vpc_id"{
 }
 
 variable "app_sg_id" {
 }