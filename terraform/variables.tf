variable "project_name" {
  type        = string
  default     = "aws-claude-chatbot"
  description = "The name of the project, used for prefixing resource names."
}

variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "The target AWS region for deployment."
}

variable "vpc_cidr" {
  type        = string
  default     = "10.0.0.0/16"
  description = "CIDR block for the VPC."
}

variable "availability_zones" {
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
  description = "List of availability zones to use."
}

variable "kubernetes_version" {
  type        = string
  default     = "1.29"
  description = "Version of Kubernetes to deploy."
}
