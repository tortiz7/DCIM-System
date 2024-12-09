output "rds_address" {
  value = aws_db_instance.mysql_db.address
}

output "rds_endpoint"{
  value = aws_db_instance.mysql_db.endpoint
}

output "rds_sg_id" {
    value = aws_security_group.rds_sg.id
}

output "postgres_db"{
  value = aws_db_instance.mysql_db.id
}
output "redis_endpoint"{
  value = aws_elasticache_replication_group.redis.primary_endpoint_address
}

output "redis_port"{
  value = 6379
}

output "redis_sg_id"{
  value = aws_security_group.redis_sg.id
}