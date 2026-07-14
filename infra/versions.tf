terraform {
  required_version = ">= 1.9"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Bootstrap this bucket and table once via the AWS CLI before the first
  # `terraform init` — see README.md. Terraform can't create the backend
  # it's about to store its own state in.
  backend "s3" {
    bucket         = "ims-terraform-state"
    key            = "ims-api/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "ims-terraform-locks"
    encrypt        = true
  }
}
