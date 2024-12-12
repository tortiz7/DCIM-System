output "rds_address" {
  value = aws_db_instance.mysql_db.address
}

output "rds_endpoint"{
  value = aws_db_instance.mysql_db.endpoint
}

output "redis_endpoint" {
  description = "Primary endpoint of the Redis Replication Group"
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
}

output "redis_reader_endpoint" {
  description = "Reader endpoint for the Redis Replication Group"
  value       = aws_elasticache_replication_group.redis.reader_endpoint_address
}


output "rds_sg_id" {
    value = aws_security_group.rds_sg.id
}

output "mysql_db"{
  value = aws_db_instance.mysql_db.id
}