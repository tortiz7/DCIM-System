resource "aws_db_instance" "mysql_db" {
  identifier           = "ralphng"
  engine               = "mysql"
  engine_version       = "5.7"
  instance_class       = var.db_instance_class
  allocated_storage    = 20
  storage_type         = "standard"
  db_name              = var.db_name
  username             = var.db_username
  password             = var.db_password
  skip_final_snapshot  = true

  db_subnet_group_name   = aws_db_subnet_group.rds_subnet_group.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]

  tags = {
    Name = "Ralph Mysql DB"
  }
}

resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "rds_subnet_group"
  subnet_ids = var.private_subnet

  tags = {
    Name = "RDS subnet group"
  }
}

resource "aws_security_group" "rds_sg" {
  name        = "rds_sg"
  description = "Security group for RDS"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "RDS Security Group"
  }
}

resource "aws_security_group_rule" "rds_ingress" {
  type                     = "ingress"
  from_port                = 3306
  to_port                  = 3306
  protocol                 = "tcp"
  security_group_id        = aws_security_group.rds_sg.id  
  source_security_group_id = var.app_sg_id            
}

resource "aws_elasticache_subnet_group" "cache_subnet_group" {
  name       = "cache-subnet-group"
  subnet_ids = var.private_subnet

  tags = {
    Name = "Cache Subnet Group"
  }
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id          = "my-redis-replication-group"
  description                   = "Multi-AZ Redis Replication Group"
  engine                        = "redis"
  engine_version                = "6.x"
  node_type                     = "cache.t3.medium"
  num_cache_clusters            = 2  # 1 primary + 1 replica
  automatic_failover_enabled    = true
  multi_az_enabled              = true
  subnet_group_name             = aws_elasticache_subnet_group.cache_subnet_group.name
  security_group_ids            = [aws_security_group.redis_sg.id]

  tags = {
    Name = "Redis Replication Group"
  }
}



resource "aws_security_group" "redis_sg" {
  name        = "redis-sg"
  description = "Security group for Redis"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [] # Add any necessary IP ranges
    security_groups = [var.app_sg_id] # Allow from your app security group
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "Redis Security Group"
  }
}

output "redis_primary_endpoint" {
  description = "Primary endpoint of the Redis Replication Group"
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
}

output "redis_reader_endpoint" {
  description = "Reader endpoint for the Redis Replication Group"
  value       = aws_elasticache_replication_group.redis.reader_endpoint_address
}




