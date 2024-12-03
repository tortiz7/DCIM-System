output "app_sg_id" {
    value = aws_security_group.app_sg.id
}

output "app_server_ids" {
    value = [for instance in aws_instance.app_server : instance.id]
}

output "private_instance_ips" {
    value       = coalescelist(aws_instance.app_server[*].private_ip, [""])
    description = "Private IPs of the app servers"
}

output "bastion_public_ip" {
    value       = try(aws_instance.bastion_host[0].public_ip, "")
    description = "Public IP of the first bastion host"
}