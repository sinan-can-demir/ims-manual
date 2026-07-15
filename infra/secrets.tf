# DATABASE_URL is fully derived from the RDS instance + generated password —
# no manual value needed, Terraform's dependency graph wires it automatically.
resource "aws_secretsmanager_secret" "database_url" {
  name = "${local.name_prefix}/database-url"

  tags = {
    Name = "${local.name_prefix}-database-url"
  }
}

resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id     = aws_secretsmanager_secret.database_url.id
  secret_string = "postgresql://${var.db_username}:${random_password.db.result}@${aws_db_instance.main.endpoint}/${var.db_name}"
}

# API_KEY is supplied by the operator (same value API clients need to know),
# not generated — matches today's local .env pattern.
resource "aws_secretsmanager_secret" "api_key" {
  name = "${local.name_prefix}/api-key"

  tags = {
    Name = "${local.name_prefix}-api-key"
  }
}

resource "aws_secretsmanager_secret_version" "api_key" {
  secret_id     = aws_secretsmanager_secret.api_key.id
  secret_string = var.api_key
}
