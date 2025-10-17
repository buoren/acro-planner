# Claude Context - Acro Planner Project

## Project Overview
Building an Acro Planner application with a FastAPI backend that will be deployed to Google Cloud with MySQL.

## Current Setup

### Backend Server (FastAPI)
- **Location**: `/server` directory (note: originally created at root, then moved to server subdirectory)
- **Framework**: FastAPI with Poetry as package manager
- **Database**: MySQL configured with SQLAlchemy and PyMySQL
- **Deployment Target**: Google Cloud with Cloud SQL (MySQL)

### Completed Tasks
1. ✅ Initialized Poetry project in server directory
2. ✅ Added FastAPI, uvicorn, SQLAlchemy, PyMySQL, python-dotenv dependencies
3. ✅ Created Hello World FastAPI application with:
   - Root endpoint `/` returning "Hello World"
   - Health check endpoint `/health`
4. ✅ Set up MySQL database configuration ready for Google Cloud SQL
5. ✅ Created environment configuration with `.env.example`
6. ✅ Made server work without MySQL for local development (graceful fallback)
7. ✅ Successfully tested endpoints

### Project Structure
```
acro-planner/
├── server/
│   ├── main.py          # FastAPI app with lifespan handler
│   ├── database.py      # SQLAlchemy setup for MySQL/Google Cloud SQL
│   ├── pyproject.toml   # Poetry dependencies
│   ├── poetry.lock      # Locked dependencies
│   └── README.md        # Setup instructions
├── .env.example         # Environment template
└── .gitignore          # Python/Poetry ignores
```

### Key Implementation Details

#### Database Connection (database.py)
- Uses SQLAlchemy with PyMySQL driver
- Connection string format for Google Cloud SQL documented
- Includes connection pooling configuration
- `get_db()` dependency injector for FastAPI

#### Main Application (main.py)
- Lifespan handler that creates database tables on startup
- Gracefully handles missing database connection
- Will only attempt database connection if DATABASE_URL is set

### Running the Server
```bash
cd server
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker and Google Cloud Deployment
- ✅ Created Dockerfile optimized for production (multi-stage, non-root user)
- ✅ Added .dockerignore for efficient builds
- ✅ Created cloudbuild.yaml for Google Cloud Build CI/CD
- ✅ Added comprehensive deployment documentation (DEPLOY.md)
- ✅ Docker image successfully built and tested locally
- Container runs on port 8080 (Google Cloud Run default)
- Health checks configured

### Deployment Commands
```bash
# Build Docker image locally
docker build -t acro-planner-backend server/

# Test locally
docker run -p 8082:8080 acro-planner-backend

# Deploy to Google Cloud Run
gcloud run deploy acro-planner-backend \
  --source server/ \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Terraform Infrastructure (Complete)
- ✅ Complete Terraform configuration for Google Cloud
- ✅ Cloud SQL MySQL instance with automated backups
- ✅ Cloud Run service with auto-scaling
- ✅ Artifact Registry for Docker images
- ✅ IAM roles and service accounts with least privilege
- ✅ Secret Manager for database passwords
- ✅ Cloud Build trigger for CI/CD
- ✅ Deployment script for easy updates

### Infrastructure Files
```
terraform/
├── main.tf              # Provider and API configuration
├── variables.tf         # Input variables
├── outputs.tf          # Output values
├── cloudsql.tf         # Cloud SQL configuration
├── cloudrun.tf         # Cloud Run service
├── iam.tf              # IAM and permissions
├── terraform.tfvars.example  # Example variables
└── README.md           # Setup instructions
```

### Deployment Process
1. Configure Terraform: `cp terraform/terraform.tfvars.example terraform/terraform.tfvars`
2. Initialize: `terraform init`
3. Apply infrastructure: `terraform apply`
4. Deploy application: `./scripts/deploy.sh`

### Flutter Client (Complete)
- ✅ Flutter project created in `clients/acro_planner_app/`
- ✅ API service with HTTP client configured
- ✅ Provider state management setup
- ✅ Environment configuration with .env files
- ✅ Material Design 3 theming (light/dark mode)
- ✅ Real-time backend health check
- ✅ Welcome screen with API connection status
- ✅ Ready for feature development

### Client Structure
```
clients/
└── acro_planner_app/          # Flutter mobile app
    ├── lib/
    │   ├── main.dart          # App entry point
    │   └── services/
    │       └── api_service.dart  # HTTP client
    ├── assets/               # App assets
    ├── .env                  # Environment config
    └── pubspec.yaml         # Dependencies
```

### To run Flutter app:
```bash
cd clients/acro_planner_app
flutter pub get
flutter run
```

### Next Steps (Not Yet Implemented)
- Add actual data models (SQLAlchemy models)
- Implement CRUD operations
- Add authentication/authorization
- Add more API endpoints as needed
- Set up GitHub integration for Cloud Build
- Configure VPC for production security
- Build Flutter app features (sessions, tracking, etc.)

### Important Notes
- Server can run without MySQL for development/testing
- Ready for Google Cloud SQL integration (connection string format included)
- All dependencies installed via Poetry
- Environment variables handled via python-dotenv

### Commands to Remember
- Install dependencies: `poetry install`
- Run server: `poetry run uvicorn main:app --reload`
- Test endpoints: `curl http://localhost:8000/`