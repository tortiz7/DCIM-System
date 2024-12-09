resource "aws_security_group" "alb_sg" {
  name   = "alb_sg"
  vpc_id = var.vpc_id

  ingress {
    description = "Allow HTTP traffic"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "ALB Security Group"
  }
}

resource "aws_lb" "app_alb" {
  name               = var.alb_name
  internal           = false  
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = var.public_subnet

  enable_deletion_protection = false

  tags = {
    Name = "Ralph Application Load Balancer"
  }
}

# Update ALB_main.tf
resource "aws_lb_target_group" "app_tg" {
  name     = "app-target-group"
  port     = 80  # Ralph web port
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    protocol            = "HTTP"
    path                = "/login/"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2 
    unhealthy_threshold = 2
    matcher             = "200,302"
  }

  tags = {
    Name = "Ralph App Target Group"
  }
}

resource "aws_lb_target_group_attachment" "app_tg_attachment" {
  count            = var.app_count  
  target_group_arn = aws_lb_target_group.app_tg.arn
  target_id        = var.app_server_ids[count.index]  
  port             = 80 
}

resource "aws_lb_listener" "http_listener" {
  load_balancer_arn = aws_lb.app_alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app_tg.arn
  }
}

resource "aws_lb_listener_rule" "chatbot" {
  listener_arn = aws_lb_listener.http_listener.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app_tg.arn
  }

  condition {
    path_pattern {
      values = ["/chatbot/*"]
    }
  }
}