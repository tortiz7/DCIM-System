output "alb_sg_id" {
    value = aws_security_group.alb_sg.id
}

output "alb_dns_name" {
    value = aws_lb.app_alb.dns_name
    description = "DNS name of the application load balancer"
}