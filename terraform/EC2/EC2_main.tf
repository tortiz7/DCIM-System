# changes:
# 1. server name: use app_server to replace backend server
# 2. Key need to be changed
# 3. ignore userdata now 
# 4. use batsion host instead of frontend_server
# 5. security group for app: alb_sg
# 6. load balancer to app server
locals{
  # pub_key = file("kura_public_key.txt")
  app_private_ips = aws_instance.app_server[*].private_ip
}

variable "ralph_admin_user" {
  description = "Ralph admin username"
  default     = "ralph"
}

variable "ralph_admin_password" {
  description = "Ralph admin password"
  default     = "ralph"  # Change for production
}

# instance for app
resource "aws_instance" "app_server" {
  count = var.app_count
  ami   = "ami-005fc0f236362e99f"
  instance_type = var.instance_type
  vpc_security_group_ids = [aws_security_group.ralph_app_sg.id]
  key_name = "keypair_cloudega_T2"
  subnet_id = var.private_subnet[count.index % length(var.private_subnet)]
  
  user_data = templatefile("${path.module}/nvidia_preinstall.sh", {
    deploy_script = base64encode(templatefile("${path.module}/deploy.sh", {
      aws_lb_dns         = var.alb_dns_name,
      db_name            = var.db_name,
      db_user            = var.db_username,
      db_password        = var.db_password,
      db_endpoint        = var.rds_endpoint,
      redis_endpoint     = var.redis_endpoint,
      redis_port         = var.redis_port,
      ralph_admin_user   = var.ralph_admin_user,
      ralph_admin_password = var.ralph_admin_password,
      RALPH_API_TOKEN = "",
      SECRET_KEY = "",
      github_token = var.github_token
  }))
})


  iam_instance_profile = aws_iam_instance_profile.app_profile.name

  tags = {
    Name = "ralph_app_az${count.index + 1}"
  }

  root_block_device {
    volume_size = 70  # GB minimum for testing
    volume_type = "gp3"
    # Reduced IOPS for testing
    iops        = 1000
    throughput  = 125
    delete_on_termination = true
}

  depends_on = [
    var.postgres_db,
    var.nat_gw
  ]
}

resource "aws_instance" "bastion_host" {
  count = var.bastion_count
  ami = "ami-0866a3c8686eaeeba"                # The Amazon Machine Image (AMI) ID used to launch the EC2 instance.
                                        # Replace this with a valid AMI ID
  instance_type = "t3.micro"                # Specify the desired EC2 instance size.
  # Attach an existing security group to the instance.
  # Security groups control the inbound and outbound traffic to your EC2 instance.
  vpc_security_group_ids = [aws_security_group.ralph_bastion_sg.id]         # Replace with the security group ID, e.g., "sg-01297adb7229b5f08".
  key_name = "keypair_cloudega_T2"                # The key pair name for SSH access to the instance.
  subnet_id = var.public_subnet[count.index % length(var.public_subnet)]
#  user_data = templatefile("kura_key_upload.sh", {
#        pub_key = local.pub_key
#   })
#   # Tagging the resource with a Name label. Tags help in identifying and organizing resources in AWS.
   tags = {
     "Name" : "bastion_az${count.index +1}"         
   }

   depends_on = [
    var.postgres_db,
    var.nat_gw
  ]
}


# Add IAM role and policy for ElastiCache access
resource "aws_iam_role" "app_role" {
  name = "ralph_app_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_instance_profile" "app_profile" {
  name = "ralph_app_profile"
  role = aws_iam_role.app_role.name
}

resource "aws_iam_role_policy" "elasticache_policy" {
  name = "ralph_elasticache_policy"
  role = aws_iam_role.app_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "elasticache:Describe*",
          "elasticache:List*"
        ]
        Resource = "*"
      }
    ]
  })
}

# Create a security group named "tf_made_sg" that allows SSH and HTTP traffic.
# This security group will be associated with the EC2 instance created above.
resource "aws_security_group" "ralph_bastion_sg" { # in order to use securtiy group resouce, must use first "", the second "" is what terraform reconginzes as the name
  name        = "tf_made_sg"
  description = "open ssh traffic"
  vpc_id = var.vpc_id
  # Ingress rules: Define inbound traffic that is allowed.Allow SSH traffic and HTTP traffic on port 8080 from any IP address (use with caution)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  #  ingress {
  #   from_port   = 3000
  #   to_port     = 3000
  #   protocol    = "tcp"
  #   cidr_blocks = ["0.0.0.0/0"]
  #   }

    #  ingress {
    # from_port   = 80
    # to_port     = 80
    # protocol    = "tcp"
    # cidr_blocks = ["0.0.0.0/0"]
    # }
  # Egress rules: Define outbound traffic that is allowed. The below configuration allows all outbound traffic from the instance.
 egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  # Tags for the security group
  tags = {
    "Name"      : "Bastion_SG"                          # Name tag for the security group
    "Terraform" : "true"                                # Custom tag to indicate this SG was created with Terraform
  }
}

resource "aws_security_group" "ralph_app_sg" { # in order to use securtiy group resouce, must use first "", the second "" is what terraform reconginzes as the name
  name        = "tf_made_sg_private"
  description = "host gunicorn"
  vpc_id = var.vpc_id
  # Ingress rules: Define inbound traffic that is allowed. Allow SSH traffic and HTTP traffic on port 8080 from any IP address (use with caution)
   
   ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    } 

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    }   

 ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    # security_groups = [var.alb_sg_id]
    }

  ingress {
    from_port   = 9100
    to_port     = 9100
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    }

  # ingress {
  #   from_port   = 8001
  #   to_port     = 8001
  #   protocol    = "tcp"
  #   security_groups = [var.alb_sg_id]  # Only allow access from ALB
  # }

  ingress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    self      = true
  }

    #   ingress {
    # from_port   = 5432
    # to_port     = 5432
    # protocol    = "tcp"
    # cidr_blocks = ["0.0.0.0/0"]
    # }


    egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

 # Tags for the security group
  tags = {
    "Name"      : "App_SG"                          # Name tag for the security group
    "Terraform" : "true"                                # Custom tag to indicate this SG was created with Terraform
    }
}

  resource "aws_security_group_rule" "backend_to_rds_ingress" {
  type                     = "ingress"
  from_port                = 3306
  to_port                  = 3306
  protocol                 = "tcp"
  security_group_id        = aws_security_group.ralph_app_sg.id
  source_security_group_id = var.rds_sg_id
}

resource "aws_security_group_rule" "allow_alb_to_app" {
  type              = "ingress"
  from_port         = var.app_port
  to_port           = var.app_port
  protocol          = "tcp"
  security_group_id = aws_security_group.ralph_app_sg.id  

  source_security_group_id = var.alb_sg_id  
}

resource "aws_security_group_rule" "redis_access" {
  type              = "ingress"
  from_port         = 6379
  to_port           = 6379
  protocol          = "tcp"
  security_group_id = aws_security_group.ralph_app_sg.id
  source_security_group_id = var.redis_sg_id
}

resource "aws_security_group_rule" "chatbot_access" {
  type              = "ingress"
  from_port         = 8001
  to_port           = 8001
  protocol          = "tcp"
  security_group_id = aws_security_group.ralph_app_sg.id
  source_security_group_id = var.alb_sg_id
}




output "instance_ip" {
 value = [for instance in aws_instance.bastion_host : instance.public_ip]  # Display the public IP address of the EC2 instance after creation.
}