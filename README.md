# AWS Claude EKS AI Chatbot: E2E Enterprise Architecture & Deployment

This repository contains a clean, production-grade, end-to-end working model of an AI Chatbot powered by **Claude 3.5 Sonnet**, running on **AWS EKS** (Elastic Kubernetes Service), managed via **Terraform (IaC)**, and continuously deployed using **GitHub Actions**.

The system is architected for maximum security, scalability, and efficiency.

---

## 🌟 Architecture Highlights

1. **IAM Roles for Service Accounts (IRSA)**: The FastAPI backend pods run with a specific Kubernetes Service Account mapped to an AWS IAM Role. It invokes Claude on **AWS Bedrock** directly without storing permanent AWS access keys in Kubernetes secrets.
2. **Network Isolation**: All worker nodes run in private subnets. Traffic to Bedrock, ECR, and S3 is routed securely through **AWS VPC Endpoints (PrivateLink)**, keeping traffic internal to the AWS network.
3. **Application Load Balancer (ALB)**: Handled by the AWS Load Balancer Controller, the ALB terminates TLS and handles path-based routing:
   - `/api/*` -> Backend API Service (FastAPI)
   - `/*` -> Frontend Web UI Service (Vite + React)
4. **CI/CD Security via OIDC**: GitHub Actions authenticates with AWS using OpenID Connect (OIDC) federated identity, completely eliminating the need for long-lived credentials in GitHub repository secrets.

---

## 📂 Project Structure

- **`terraform/`**: Infrastructure as Code (IaC) defining VPC, subnets, NAT, VPC Endpoints, ECR Repositories, EKS Cluster, node groups, and IAM Roles (including IRSA).
- **`backend/`**: FastAPI python server using the Claude SDK and AWS Bedrock Converse stream API, featuring Server-Sent Events (SSE) for real-time text streaming.
- **`frontend/`**: Vite + React single-page app displaying a glassmorphic dashboard interface, system instruction controls, and streaming chat history.
- **`k8s/`**: Kubernetes manifests defining Namespace, Service Account (IRSA), Deployments, Services, and AWS ALB Ingress.
- **`.github/workflows/`**: Continuous Integration (testing) and Continuous Deployment (ECR image building and EKS deployment).

---

## 🚀 Deployment Guide

### Phase 1: Deploying AWS Infrastructure (Terraform)

1. Navigate to the terraform directory:
   ```bash
   cd terraform
   ```
2. Initialize Terraform:
   ```bash
   terraform init
   ```
3. Plan and verify resources:
   ```bash
   terraform plan
   ```
4. Deploy the infrastructure (EKS cluster creation takes ~15 minutes):
   ```bash
   terraform apply -auto-approve
   ```
5. Note down the outputs, specifically the ECR repository URLs and EKS cluster endpoint.

---

### Phase 2: Secure AWS OIDC Role for GitHub Actions

To allow GitHub Actions to deploy to EKS, you need to create an OIDC Identity Provider in AWS IAM.

1. Go to **AWS IAM Console** -> **Identity Providers** -> **Add Provider**.
   - Select **OpenID Connect**.
   - Provider URL: `https://token.actions.githubusercontent.com`
   - Audience: `sts.amazonaws.com`
2. Create an IAM Role named `github-actions-eks-deploy-role` with the following **Trust Relationship** (replace `<YOUR_ORGANIZATION>/<YOUR_REPO>` with your GitHub details):
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Principal": {
           "Federated": "arn:aws:iam::<AWS_ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
         },
         "Action": "sts:AssumeRoleWithWebIdentity",
         "Condition": {
           "StringEquals": {
             "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
           },
           "StringLike": {
             "token.actions.githubusercontent.com:repo": "<YOUR_ORGANIZATION>/<YOUR_REPO>:*"
           }
         }
       }
     ]
   }
   ```
3. Attach a policy to this role allowing ECR image push/pull, EKS cluster description (`eks:DescribeCluster`), and standard permissions required to manage deployments.

---

### Phase 3: Setup GitHub Secrets

Configure the following environment variables in your GitHub Repository settings (**Settings** -> **Secrets and variables** -> **Actions**):

- **Variables**:
  - `AWS_REGION`: e.g., `us-east-1`
  - `EKS_CLUSTER_NAME`: `aws-claude-chatbot-eks`
  - `BACKEND_ECR_REPO`: `aws-claude-chatbot-backend`
  - `FRONTEND_ECR_REPO`: `aws-claude-chatbot-frontend`
- **Secrets**:
  - `GHA_AWS_ROLE_ARN`: The ARN of the `github-actions-eks-deploy-role` role created in Phase 2.

Push your changes to the `main` branch, and the GitHub Actions runner will automatically build, test, and deploy the application to your Kubernetes cluster.

---

## 💻 Running Locally for Development

### Backend API (FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Set your environment variables:
   ```bash
   export LLM_PROVIDER="anthropic" # or bedrock if you have AWS local credentials
   export ANTHROPIC_API_KEY="your-api-key"
   ```
4. Run the API:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

### Frontend (Vite + React)

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the dev server:
   ```bash
   npm run dev
   ```
   *Vite is configured to proxy `/api` calls directly to `http://localhost:8000` automatically.*
