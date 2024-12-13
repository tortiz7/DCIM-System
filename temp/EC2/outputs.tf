output "app_sg_id" {
    value = aws_security_group.ralph_app_sg.id
}

output "app_server_ids" {
    value = [for instance in aws_instance.app_server : instance.id]
}

output "bastion_public_ip" {
    value       = try(aws_instance.bastion_host[0].public_ip, "")
    description = "Public IP of the bastion host"
}

output "private_instance_ips" {
    value       = [for instance in aws_instance.app_server : instance.private_ip]
    description = "Private IPs of the application servers"
}