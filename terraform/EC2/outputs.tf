output "app_sg_id" {
    value = aws_security_group.app_sg.id
}

output "bastion_server_ids" {
  value = [for instance in aws_instance.bastion_server : instance.id]
}

output "app_server_ids" {
  value = [for instance in aws_instance.app_server : instance.id]
}