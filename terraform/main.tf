# Terraform configuration and AWS provider definition
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.50"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }

  # Standard configuration for production:
  # backend "s3" {
  #   bucket         = "my-terraform-state-bucket"
  #   key            = "state/aws-claude-chatbot.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "my-terraform-lock-table"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region
}
