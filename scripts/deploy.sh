#!/bin/bash
# Deploy script for Acro Planner Backend

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

echo -e "${GREEN}🚀 Starting backend deployment...${NC}"

# Load OAuth environment variables from .env.oauth file
if [ -f ".env.oauth" ]; then
    echo -e "${YELLOW}Loading OAuth environment variables from .env.oauth...${NC}"
    
    # Export OAuth variables from .env.oauth file
    GOOGLE_CLIENT_ID=$(grep -E "^AUTH_GOOGLE_ID=" .env.oauth | cut -d'=' -f2)
    GOOGLE_CLIENT_SECRET=$(grep -E "^AUTH_GOOGLE_SECRET=" .env.oauth | cut -d'=' -f2)
    SECRET_KEY=$(grep -E "^AUTH_SECRET=" .env.oauth | cut -d'=' -f2)
    
    export GOOGLE_CLIENT_ID
    export GOOGLE_CLIENT_SECRET
    export SECRET_KEY
    
    echo -e "${GREEN}✅ OAuth environment variables loaded from .env.oauth file${NC}"
else
    echo -e "${YELLOW}⚠️  .env.oauth file not found - OAuth will not be configured${NC}"
fi

# Get Terraform outputs
cd terraform
REGISTRY_URL=$(terraform output -raw artifact_registry_url 2>/dev/null || echo "")
REGION=$(terraform output -raw region 2>/dev/null || echo "us-central1")
SERVICE_ACCOUNT=$(terraform output -raw service_account_email 2>/dev/null || echo "")
CLOUD_SQL_CONNECTION=$(terraform output -raw cloud_sql_connection_name 2>/dev/null || echo "")

# Get database password from secret manager
DATABASE_PASSWORD=$(gcloud secrets versions access latest --secret="acro-planner-mysql-password" 2>/dev/null || echo "")

if [ -z "$REGISTRY_URL" ]; then
    echo -e "${RED}Error: Could not get Terraform outputs. Run 'terraform apply' first.${NC}"
    exit 1
fi

cd ..

# Configure Docker for Artifact Registry
echo -e "${YELLOW}Configuring Docker authentication...${NC}"
REGISTRY_HOST=$(echo $REGISTRY_URL | cut -d'/' -f1)
gcloud auth configure-docker $REGISTRY_HOST --quiet

# Build Backend Docker image for Linux/AMD64
echo -e "${YELLOW}Building backend Docker image for Linux/AMD64...${NC}"
docker build --platform linux/amd64 -t ${REGISTRY_URL}/acro-planner-backend:latest ./server

# Push image to Artifact Registry
echo -e "${YELLOW}Pushing backend image to Artifact Registry...${NC}"
docker push ${REGISTRY_URL}/acro-planner-backend:latest

# Deploy Backend to Cloud Run
echo -e "${YELLOW}Deploying backend to Cloud Run...${NC}"

# Construct DATABASE_URL
if [ -n "$CLOUD_SQL_CONNECTION" ] && [ -n "$DATABASE_PASSWORD" ]; then
    DATABASE_URL="mysql+pymysql://acro_user:${DATABASE_PASSWORD}@/acro_planner?unix_socket=/cloudsql/${CLOUD_SQL_CONNECTION}"
    echo -e "${GREEN}✅ Database configuration found${NC}"
else
    echo -e "${YELLOW}⚠️  Database configuration not found - running without database${NC}"
    DATABASE_URL=""
fi

if [ -n "$GOOGLE_CLIENT_ID" ] && [ -n "$GOOGLE_CLIENT_SECRET" ] && [ -n "$SECRET_KEY" ]; then
    echo -e "${YELLOW}Deploying with OAuth configuration...${NC}"
    if [ -n "$DATABASE_URL" ]; then
        gcloud run deploy acro-planner-backend \
          --image=${REGISTRY_URL}/acro-planner-backend:latest \
          --region=${REGION} \
          --service-account=${SERVICE_ACCOUNT} \
          --platform=managed \
          --allow-unauthenticated \
          --add-cloudsql-instances=${CLOUD_SQL_CONNECTION} \
          --set-env-vars="GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}" \
          --set-env-vars="GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}" \
          --set-env-vars="SECRET_KEY=${SECRET_KEY}" \
          --set-env-vars="DATABASE_URL=${DATABASE_URL}" \
          --set-env-vars="BASE_URL=https://acro-planner-backend-733697808355.us-central1.run.app"
    else
        gcloud run deploy acro-planner-backend \
          --image=${REGISTRY_URL}/acro-planner-backend:latest \
          --region=${REGION} \
          --service-account=${SERVICE_ACCOUNT} \
          --platform=managed \
          --allow-unauthenticated \
          --set-env-vars="GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}" \
          --set-env-vars="GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}" \
          --set-env-vars="SECRET_KEY=${SECRET_KEY}" \
          --set-env-vars="BASE_URL=https://acro-planner-backend-733697808355.us-central1.run.app"
    fi
else
    echo -e "${YELLOW}Deploying without OAuth configuration...${NC}"
    if [ -n "$DATABASE_URL" ]; then
        gcloud run deploy acro-planner-backend \
          --image=${REGISTRY_URL}/acro-planner-backend:latest \
          --region=${REGION} \
          --service-account=${SERVICE_ACCOUNT} \
          --platform=managed \
          --allow-unauthenticated \
          --add-cloudsql-instances=${CLOUD_SQL_CONNECTION} \
          --set-env-vars="DATABASE_URL=${DATABASE_URL}"
    else
        gcloud run deploy acro-planner-backend \
          --image=${REGISTRY_URL}/acro-planner-backend:latest \
          --region=${REGION} \
          --service-account=${SERVICE_ACCOUNT} \
          --platform=managed \
          --allow-unauthenticated
    fi
fi

echo -e "${GREEN}✅ Backend deployment complete!${NC}"

# Get the service URL
BACKEND_SERVICE_URL=$(gcloud run services describe acro-planner-backend --region=${REGION} --format='value(status.url)')

echo -e "${GREEN}🌐 Backend URL: ${BACKEND_SERVICE_URL}${NC}"
echo -e "${GREEN}🌐 Admin Interface: ${BACKEND_SERVICE_URL}/admin${NC}"

# Test the deployment
echo -e "${YELLOW}Testing backend deployment...${NC}"
curl -s ${BACKEND_SERVICE_URL}/health | jq '.' || echo "Backend health check: ${BACKEND_SERVICE_URL}/health"

echo -e "${GREEN}🎉 Backend deployed successfully!${NC}"
echo ""
echo -e "${YELLOW}The admin interface is available at:${NC}"
echo "${BACKEND_SERVICE_URL}/admin"
echo ""
if [ -n "$GOOGLE_CLIENT_ID" ] && [ -n "$GOOGLE_CLIENT_SECRET" ] && [ -n "$SECRET_KEY" ]; then
    echo -e "${GREEN}🔐 OAuth authentication is enabled for the admin interface${NC}"
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Ensure Google OAuth redirect URI includes: ${BACKEND_SERVICE_URL}/auth/callback"
    echo "2. Ensure authorized JavaScript origins include: ${BACKEND_SERVICE_URL}"
    echo "3. Visit ${BACKEND_SERVICE_URL}/admin to access the protected admin interface"
else
    echo -e "${YELLOW}⚠️  OAuth authentication is NOT configured. The admin interface is unprotected.${NC}"
    echo -e "${YELLOW}To enable OAuth protection:${NC}"
    echo "1. Create .env.oauth with AUTH_GOOGLE_ID, AUTH_GOOGLE_SECRET, and AUTH_SECRET"
    echo "2. Re-run the deployment script"
fi