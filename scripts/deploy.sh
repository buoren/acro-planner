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

# Load Gmail environment variables from .env.gmail file
if [ -f ".env.gmail" ]; then
    echo -e "${YELLOW}Loading Gmail environment variables from .env.gmail...${NC}"
    
    # Export Gmail variables from .env.gmail file
    # Note: We need to handle the JSON carefully as it contains special characters
    GMAIL_SERVICE_ACCOUNT_JSON=$(grep -E "^GMAIL_SERVICE_ACCOUNT_JSON=" .env.gmail | cut -d"'" -f2)
    GMAIL_SENDER_EMAIL=$(grep -E "^GMAIL_SENDER_EMAIL=" .env.gmail | cut -d'=' -f2)
    GMAIL_IMPERSONATION_EMAIL=$(grep -E "^GMAIL_IMPERSONATION_EMAIL=" .env.gmail | cut -d'=' -f2)
    FRONTEND_URL=$(grep -E "^FRONTEND_URL=" .env.gmail | cut -d'=' -f2)
    
    export GMAIL_SERVICE_ACCOUNT_JSON
    export GMAIL_SENDER_EMAIL
    export GMAIL_IMPERSONATION_EMAIL
    export FRONTEND_URL
    
    echo -e "${GREEN}✅ Gmail environment variables loaded from .env.gmail file${NC}"
else
    echo -e "${YELLOW}⚠️  .env.gmail file not found - Gmail API will not be configured${NC}"
fi

# Get Terraform outputs
cd terraform
REGISTRY_URL=$(terraform output -raw artifact_registry_url 2>/dev/null || echo "")
REGION=$(terraform output -raw region 2>/dev/null || echo "us-central1")
SERVICE_ACCOUNT=$(terraform output -raw service_account_email 2>/dev/null || echo "")
CLOUD_SQL_CONNECTION=$(terraform output -raw cloud_sql_connection_name 2>/dev/null || echo "")

# Get database password from secret manager
DATABASE_PASSWORD=$(gcloud secrets versions access latest --secret="acro-planner-mysql-password" 2>/dev/null || echo "")

# Get OAuth secret key from secret manager
SECRET_KEY=$(gcloud secrets versions access latest --secret="oauth-secret-key" 2>/dev/null || echo "")
export SECRET_KEY

if [ -z "$REGISTRY_URL" ]; then
    echo -e "${RED}Error: Could not get Terraform outputs. Run 'terraform apply' first.${NC}"
    exit 1
fi

cd ..

# Build React Native App for Web
echo -e "${GREEN}📱 Building React Native app for web...${NC}"
if [ -d "clients/acro-planner-mobile" ]; then
    cd clients/acro-planner-mobile
    
    # Check if node_modules exists, if not install dependencies
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing React Native dependencies...${NC}"
        npm install
    fi
    
    # Build for web
    echo -e "${YELLOW}Building React Native web bundle...${NC}"
    npx expo export --platform web --output-dir ../../server/static/app
    
    # Fix paths in the generated HTML to include /app prefix
    echo -e "${YELLOW}Fixing asset paths for /app route...${NC}"
    cd ../../server/static/app
    
    # Show original content for debugging
    echo -e "${YELLOW}Original paths in index.html:${NC}"
    grep -E "(script|href=)" index.html || echo "No script/href tags found"
    
    # Fix favicon path
    sed -i.bak 's|href="/favicon.ico"|href="/app/favicon.ico"|g' index.html
    
    # Fix JavaScript bundle path
    sed -i.bak 's|src="/_expo/|src="/app/_expo/|g' index.html
    
    # Show fixed content for debugging
    echo -e "${YELLOW}Fixed paths in index.html:${NC}"
    grep -E "(script|href=)" index.html || echo "No script/href tags found"
    
    # Clean up backup file
    rm -f index.html.bak
    
    cd ../../..
    echo -e "${GREEN}✅ React Native app built successfully${NC}"
else
    echo -e "${YELLOW}⚠️  React Native app directory not found, skipping app build${NC}"
fi

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
    
    # Create comprehensive environment variables file
    TEMP_ENV_FILE="/tmp/all_env_vars_$(date +%s).yaml"
    cat > "$TEMP_ENV_FILE" <<EOF
GOOGLE_CLIENT_ID: '${GOOGLE_CLIENT_ID}'
GOOGLE_CLIENT_SECRET: '${GOOGLE_CLIENT_SECRET}'
SECRET_KEY: '${SECRET_KEY}'
BASE_URL: 'https://acro-planner-backend-733697808355.us-central1.run.app'
EOF
    
    # Add database URL if available
    if [ -n "$DATABASE_URL" ]; then
        echo "DATABASE_URL: '${DATABASE_URL}'" >> "$TEMP_ENV_FILE"
    fi
    
    # Add Gmail environment variables if available
    if [ -n "$GMAIL_SERVICE_ACCOUNT_JSON" ] && [ -n "$GMAIL_SENDER_EMAIL" ] && [ -n "$GMAIL_IMPERSONATION_EMAIL" ]; then
        cat >> "$TEMP_ENV_FILE" <<EOF
GMAIL_SERVICE_ACCOUNT_JSON: '${GMAIL_SERVICE_ACCOUNT_JSON}'
GMAIL_SENDER_EMAIL: '${GMAIL_SENDER_EMAIL}'
GMAIL_IMPERSONATION_EMAIL: '${GMAIL_IMPERSONATION_EMAIL}'
FRONTEND_URL: '${FRONTEND_URL}'
EOF
        echo -e "${GREEN}✅ Including Gmail API configuration${NC}"
    fi
    
    if [ -n "$DATABASE_URL" ]; then
        gcloud run deploy acro-planner-backend \
          --image=${REGISTRY_URL}/acro-planner-backend:latest \
          --region=${REGION} \
          --service-account=${SERVICE_ACCOUNT} \
          --platform=managed \
          --allow-unauthenticated \
          --add-cloudsql-instances=${CLOUD_SQL_CONNECTION} \
          --env-vars-file="${TEMP_ENV_FILE}"
    else
        gcloud run deploy acro-planner-backend \
          --image=${REGISTRY_URL}/acro-planner-backend:latest \
          --region=${REGION} \
          --service-account=${SERVICE_ACCOUNT} \
          --platform=managed \
          --allow-unauthenticated \
          --env-vars-file="${TEMP_ENV_FILE}"
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

# Clean up temporary Gmail env file if it exists
if [ -n "$TEMP_ENV_FILE" ] && [ -f "$TEMP_ENV_FILE" ]; then
    rm -f "$TEMP_ENV_FILE"
    echo -e "${GREEN}🧹 Cleaned up temporary environment file${NC}"
fi

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