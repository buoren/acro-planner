# Google Cloud Deployment Guide

## Prerequisites

1. Install Google Cloud SDK:
```bash
# macOS
brew install google-cloud-sdk

# Or download from: https://cloud.google.com/sdk/docs/install
```

2. Authenticate and set project:
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

3. Enable required APIs:
```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

## Deployment Options

### Option 1: Deploy with Cloud Build (Recommended for CI/CD)

1. Set up Cloud Build trigger (one-time setup):
```bash
# Connect your GitHub repository to Cloud Build
# Visit: https://console.cloud.google.com/cloud-build/triggers
```

2. Deploy manually using Cloud Build:
```bash
# From repository root
gcloud builds submit --config=server/cloudbuild.yaml
```

3. Or push to main branch to trigger automatic deployment (if trigger is set up)

### Option 2: Deploy with Cloud Run Button (Quick Deploy)

1. Build and push image locally:
```bash
# Set your project ID
export PROJECT_ID=your-project-id

# Build the Docker image
cd server
docker build -t gcr.io/$PROJECT_ID/acro-planner-backend .

# Push to Container Registry
docker push gcr.io/$PROJECT_ID/acro-planner-backend

# Deploy to Cloud Run
gcloud run deploy acro-planner-backend \
  --image gcr.io/$PROJECT_ID/acro-planner-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080
```

### Option 3: Direct Deployment from Source

```bash
# Deploy directly from source code
cd server
gcloud run deploy acro-planner-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080
```

## Environment Variables for Production

When deploying with database connection:

```bash
gcloud run deploy acro-planner-backend \
  --set-env-vars="DATABASE_URL=mysql+pymysql://user:password@/dbname?unix_socket=/cloudsql/PROJECT:REGION:INSTANCE" \
  --set-cloudsql-instances=PROJECT:REGION:INSTANCE
```

## Testing the Deployment

After deployment, you'll receive a URL like:
```
https://acro-planner-backend-xxxxx-uc.a.run.app
```

Test the endpoints:
```bash
# Test root endpoint
curl https://acro-planner-backend-xxxxx-uc.a.run.app/

# Test health check
curl https://acro-planner-backend-xxxxx-uc.a.run.app/health
```

## Monitoring

View logs:
```bash
gcloud run services logs read acro-planner-backend
```

View service details:
```bash
gcloud run services describe acro-planner-backend --region us-central1
```

## Local Docker Testing

Test the Docker container locally before deploying:
```bash
cd server

# Build
docker build -t acro-planner-backend .

# Run
docker run -p 8080:8080 acro-planner-backend

# Test
curl http://localhost:8080/
```

## Cost Optimization

- Cloud Run charges only for actual usage (per request)
- Set `--min-instances=0` to scale to zero when not in use
- Use `--max-instances` to limit scaling and control costs
- Current configuration uses 512Mi memory and 1 CPU (adjust as needed)

## Troubleshooting

1. **Build fails**: Check that all dependencies are in `pyproject.toml`
2. **Deploy fails**: Ensure Cloud Run API is enabled
3. **Container won't start**: Check logs with `gcloud run services logs read`
4. **Database connection fails**: Verify Cloud SQL proxy permissions and connection string