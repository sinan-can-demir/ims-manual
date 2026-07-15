variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Short name used as a prefix for resource names and tags."
  type        = string
  default     = "ims"
}

variable "environment" {
  description = "Deployment environment name, used in tags."
  type        = string
  default     = "prod"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for the two public subnets (ALB, NAT gateway)."
  type        = list(string)
  default     = ["10.0.0.0/24", "10.0.1.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for the two private subnets (ECS tasks, RDS)."
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24"]
}

variable "container_port" {
  description = "Port the API container listens on."
  type        = number
  default     = 8000
}

variable "db_instance_class" {
  description = "RDS instance class."
  type        = string
  default     = "db.t4g.micro"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB."
  type        = number
  default     = 20
}

variable "db_name" {
  description = "Postgres database name."
  type        = string
  default     = "ims"
}

variable "db_username" {
  description = "Postgres master username."
  type        = string
  default     = "ims_admin"
}

variable "ecs_task_cpu" {
  description = "Fargate task vCPU units (256 = 0.25 vCPU, the cheapest tier)."
  type        = number
  default     = 256
}

variable "ecs_task_memory" {
  description = "Fargate task memory in MB (must pair validly with ecs_task_cpu)."
  type        = number
  default     = 512
}

variable "ecs_desired_count" {
  description = "Number of API tasks to run. Keep at 1 unless the inline `alembic upgrade head` migration step in the container command is replaced with a dedicated one-off migration task (see README.md) — concurrent task starts would otherwise race on migrations."
  type        = number
  default     = 1
}

variable "api_key" {
  description = "Shared API key for the /api routes (same value clients send via the X-API-Key header). Generate with `openssl rand -hex 32`. Supply via terraform.tfvars (gitignored) or TF_VAR_api_key — never commit a real value."
  type        = string
  sensitive   = true
}

variable "cors_origins" {
  description = "Comma-separated list of allowed CORS origins for the API."
  type        = string
  default     = "http://localhost:8501"
}

variable "github_repository" {
  description = "GitHub repo allowed to assume the CD deploy role, as \"owner/repo\"."
  type        = string
  default     = "sinan-can-demir/ims-manual"
}

# On the very first `terraform apply`, the ECR repo is empty — there is no
# image at this tag yet. Push one manually with this tag before the first
# full apply (see README.md's bootstrap steps). Every deploy after that is
# handled by CI, which registers a fresh task definition revision pointing
# at the new image tag directly (Terraform ignores task_definition changes
# on aws_ecs_service after the first apply — see ecs.tf).
variable "api_image_tag" {
  description = "Image tag for the initial task definition."
  type        = string
  default     = "initial"
}
