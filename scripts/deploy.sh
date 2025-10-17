#!/bin/bash
# Deploy script for Acro Planner backend

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "terraform/terraform.tfvars" ]; then
    echo -e "${RED}Error: terraform/terraform.tfvars not found${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

echo -e "${GREEN}🚀 Starting deployment process...${NC}"

# Get Terraform outputs
cd terraform
REGISTRY_URL=$(terraform output -raw artifact_registry_url 2>/dev/null || echo "")
REGION=$(terraform output -raw region 2>/dev/null || echo "us-central1")
SERVICE_ACCOUNT=$(terraform output -raw service_account_email 2>/dev/null || echo "")

if [ -z "$REGISTRY_URL" ]; then
    echo -e "${RED}Error: Could not get Terraform outputs. Run 'terraform apply' first.${NC}"
    exit 1
fi

cd ..

# Configure Docker for Artifact Registry
echo -e "${YELLOW}Configuring Docker authentication...${NC}"
REGISTRY_HOST=$(echo $REGISTRY_URL | cut -d'/' -f1)
gcloud auth configure-docker $REGISTRY_HOST --quiet

# Build Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -t ${REGISTRY_URL}/acro-planner-backend:latest ./server

# Push to Artifact Registry
echo -e "${YELLOW}Pushing image to Artifact Registry...${NC}"
docker push ${REGISTRY_URL}/acro-planner-backend:latest

# Deploy to Cloud Run
echo -e "${YELLOW}Deploying to Cloud Run...${NC}"
gcloud run deploy acro-planner-backend \
  --image=${REGISTRY_URL}/acro-planner-backend:latest \
  --region=${REGION} \
  --service-account=${SERVICE_ACCOUNT} \
  --platform=managed

echo -e "${GREEN}✅ Deployment complete!${NC}"

# Get the service URL
SERVICE_URL=$(gcloud run services describe acro-planner-backend --region=${REGION} --format='value(status.url)')
echo -e "${GREEN}🌐 Service URL: ${SERVICE_URL}${NC}"

# Test the deployment
echo -e "${YELLOW}Testing deployment...${NC}"
curl -s ${SERVICE_URL}/health | jq '.' || echo "Health check endpoint: ${SERVICE_URL}/health"