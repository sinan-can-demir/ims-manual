resource "aws_db_subnet_group" "main" {
  name       = "${local.name_prefix}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${local.name_prefix}-db-subnet-group"
  }
}

resource "random_password" "db" {
  length  = 32
  special = false # avoid characters that need URL-encoding in DATABASE_URL
}

# Portfolio/dev-appropriate settings, not production-grade:
# single-AZ (no Multi-AZ), no deletion protection, no final snapshot on
# destroy. Fine for this project's current stage; revisit before anything
# that needs real uptime/durability guarantees.
resource "aws_db_instance" "main" {
  identifier     = "${local.name_prefix}-db"
  engine         = "postgres"
  engine_version = "15"

  instance_class    = var.db_instance_class
  allocated_storage = var.db_allocated_storage
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = var.db_name
  username = var.db_username
  password = random_password.db.result
  port     = 5432

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  multi_az                = false
  backup_retention_period = 3
  deletion_protection     = false
  skip_final_snapshot     = true

  tags = {
    Name = "${local.name_prefix}-db"
  }
}
