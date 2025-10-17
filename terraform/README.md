# Terraform Infrastructure for Acro Planner

This Terraform configuration sets up the complete Google Cloud infrastructure for the Acro Planner application.

## Infrastructure Components

### 1. Cloud SQL (MySQL)
- MySQL 8.0 instance with automated backups
- Database and user creation
- Password stored in Secret Manager
- Query insights enabled for monitoring

### 2. Cloud Run
- Serverless container deployment
- Auto-scaling (0-10 instances)
- Health checks configured
- Connected to Cloud SQL via proxy

### 3. Artifact Registry
- Docker repository for container images
- Automated permissions for CI/CD

### 4. IAM & Security
- Service accounts with least privilege
- Secret Manager for sensitive data
- Proper role bindings for all services

### 5. CI/CD (Cloud Build)
- Automated deployment trigger
- GitHub integration ready
- Build and deploy pipeline

## Prerequisites

1. **Google Cloud Project**: Create a new project or use existing
2. **Google Cloud SDK**: Install and authenticate
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```
3. **Terraform**: Install version 1.0 or later
4. **Enable billing**: Ensure billing is enabled for your project

## Initial Setup

### 1. Configure Variables

Copy the example variables file and update with your values:
```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your project ID:
```hcl
project_id = "your-actual-project-id"
```

### 2. Initialize Terraform

```bash
cd terraform
terraform init
```

### 3. Plan and Apply

Review the changes:
```bash
terraform plan
```

Create the infrastructure:
```bash
terraform apply
```

This will create:
- Cloud SQL instance (takes 5-10 minutes)
- Artifact Registry repository
- Service accounts and IAM bindings
- Initial Cloud Run service (will fail until first image is pushed)

### 4. Build and Push Initial Image

After Terraform completes, authenticate Docker and push the first image:

```bash
# Configure Docker for Artifact Registry
gcloud auth configure-docker $(terraform output -raw artifact_registry_url | cut -d'/' -f1)

# Build and tag the image
cd ../server
docker build -t $(terraform output -raw artifact_registry_url)/acro-planner-backend:latest .

# Push to Artifact Registry
docker push $(terraform output -raw artifact_registry_url)/acro-planner-backend:latest

# Deploy to Cloud Run
gcloud run deploy acro-planner-backend \
  --image=$(terraform output -raw artifact_registry_url)/acro-planner-backend:latest \
  --region=$(terraform output -raw region) \
  --service-account=$(terraform output -raw service_account_email)
```

## Outputs

After applying, Terraform will output:
- `cloud_run_url`: URL of your deployed application
- `cloud_sql_connection_name`: Connection string for Cloud SQL
- `artifact_registry_url`: Docker registry URL
- `deployment_commands`: Helper commands for deployment

## Daily Usage

### Deploy Updates

After infrastructure is created, deploy updates using:

```bash
# From repo root
cd server
docker build -t [REGISTRY_URL]/acro-planner-backend:latest .
docker push [REGISTRY_URL]/acro-planner-backend:latest
gcloud run deploy acro-planner-backend --image=[REGISTRY_URL]/acro-planner-backend:latest --region=us-central1
```

Or use Cloud Build (after setting up GitHub connection):
```bash
gcloud builds submit --config=server/cloudbuild.yaml
```

### Connect to Database

To connect to the Cloud SQL instance:
```bash
gcloud sql connect $(terraform output -raw cloud_sql_connection_name) --user=acro_user
```

### View Logs

```bash
gcloud run services logs read acro-planner-backend --region=us-central1
```

## Cost Optimization

Default configuration is optimized for development:
- `db-f1-micro` Cloud SQL instance (~$15/month)
- Cloud Run scales to zero (pay per request)
- Minimal storage (10GB)

For production, consider:
- Larger Cloud SQL instance
- Set `min_instances = 1` for Cloud Run
- Enable deletion protection
- Use private IP for Cloud SQL

## Cleanup

To destroy all resources:
```bash
terraform destroy
```

⚠️ **Warning**: This will delete all data including the database!

## Troubleshooting

### Cloud Run fails to start
- Check logs: `gcloud run services logs read acro-planner-backend`
- Verify image exists in Artifact Registry
- Ensure service account has correct permissions

### Cannot connect to Cloud SQL
- Verify Cloud SQL Admin API is enabled
- Check service account has `cloudsql.client` role
- Ensure Cloud SQL proxy is configured in Cloud Run

### Terraform apply fails
- Ensure all APIs are enabled
- Check billing is enabled
- Verify you have owner/editor permissions

## Security Notes

- Database password is auto-generated and stored in Secret Manager
- Cloud SQL currently allows all IPs (for development) - restrict in production
- Service accounts use least privilege principle
- Consider using VPC connector for production