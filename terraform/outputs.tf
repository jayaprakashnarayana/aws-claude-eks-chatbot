output "vpc_id" {
  value       = aws_vpc.main.id
  description = "The ID of the created VPC."
}

output "eks_cluster_name" {
  value       = aws_eks_cluster.eks.name
  description = "The name of the EKS cluster."
}

output "eks_cluster_endpoint" {
  value       = aws_eks_cluster.eks.endpoint
  description = "The endpoint URL of the EKS cluster."
}

output "eks_cluster_certificate_authority_data" {
  value       = aws_eks_cluster.eks.certificate_authority[0].data
  description = "Certificate authority data for the EKS cluster."
}

output "backend_ecr_repository_url" {
  value       = aws_ecr_repository.backend.repository_url
  description = "URL of the backend ECR repository."
}

output "frontend_ecr_repository_url" {
  value       = aws_ecr_repository.frontend.repository_url
  description = "URL of the frontend ECR repository."
}

output "backend_irsa_role_arn" {
  value       = aws_iam_role.backend_irsa.arn
  description = "ARN of the IAM role for backend Service Account (IRSA)."
}
