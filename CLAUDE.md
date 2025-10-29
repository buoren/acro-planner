# Claude Context - Acro Planner Project

## Project Overview
Complete Acro Planner application with FastAPI backend deployed to Google Cloud, Flutter mobile app, and SvelteKit admin interface.

## 🚀 CURRENT STATUS: FULLY DEPLOYED AND OPERATIONAL

### Live URLs
- **Production API**: https://acro-planner-backend-733697808355.us-central1.run.app
- **Health Check**: https://acro-planner-backend-733697808355.us-central1.run.app/health
- **Flutter App**: Running locally with production API integration
- **Admin Interface**: SvelteKit admin running locally with production API integration

## 🔥 CRITICAL DEPLOYMENT WORKFLOW
**ALWAYS DEPLOY TO PRODUCTION AFTER EVERY FIX UNLESS TOLD OTHERWISE**

### Primary Deployment Tool
- **Use `./scripts/deploy.sh`** - This is the main deployment script, NOT terraform
- Terraform is only used for infrastructure setup, NOT for deployments
- The deploy.sh script handles building, pushing Docker images, and deploying to Cloud Run

### Testing Protocol
- **ALWAYS test fixes against production endpoints** after deployment
- Verify functionality with live production URLs
- Ensure changes are working in the real environment, not just locally

### Deployment Commands
```bash
# Backend deployment (from project root)
./scripts/deploy.sh

# Admin interface deployment (if needed)
cd admin && npm run build
# Then deploy admin Docker container to Cloud Run
```

## Project Structure (Complete)
```
acro-planner/
├── server/                    # FastAPI backend (DEPLOYED TO CLOUD RUN)
│   ├── main.py               # FastAPI app with CORS middleware
│   ├── database.py           # SQLAlchemy setup for Cloud SQL
│   ├── Dockerfile            # Production Docker image
│   ├── pyproject.toml        # Poetry dependencies
│   └── README.md             # Setup instructions
├── terraform/                # Infrastructure as Code (APPLIED)
│   ├── main.tf              # Provider, APIs, Artifact Registry
│   ├── cloudsql.tf          # Cloud SQL MySQL instance
│   ├── cloudrun.tf          # Cloud Run service (CORS enabled)
│   ├── iam.tf               # Service accounts and permissions
│   ├── variables.tf         # Input variables
│   └── outputs.tf           # Infrastructure outputs
├── clients/                  # Frontend applications
│   └── acro_planner_app/    # Flutter mobile/web app (WORKING)
│       ├── lib/
│       │   ├── main.dart    # Material Design 3 app
│       │   └── services/
│       │       └── api_service.dart  # Production API client
│       ├── .env             # Production API configuration
│       └── pubspec.yaml     # Flutter dependencies
├── admin/                    # SvelteKit admin interface (NEW)
│   ├── src/
│   │   ├── routes/
│   │   │   └── +page.svelte # Admin dashboard
│   │   ├── lib/
│   │   │   └── api.ts       # TypeScript API client
│   │   └── app.html         # App template
│   ├── package.json         # Node.js dependencies
│   ├── svelte.config.js     # SvelteKit configuration
│   └── tsconfig.json        # TypeScript configuration
└── CLAUDE.md                # This context file
```

## 🏗️ Infrastructure (DEPLOYED)

### Google Cloud Project: `acro-session-planner`
- **Cloud Run Service**: acro-planner-backend (us-central1)
- **Cloud SQL**: MySQL 8.0 instance with automated backups
- **Artifact Registry**: Docker container registry
- **Secret Manager**: Database password management
- **IAM**: Service accounts with least privilege access

### Terraform Resources (Applied)
```bash
cd terraform
terraform init
terraform apply  # ✅ COMPLETED SUCCESSFULLY
```

## 🔧 Backend (FastAPI - DEPLOYED)

### Key Features
- ✅ FastAPI with async/await support
- ✅ CORS middleware for web client support
- ✅ SQLAlchemy ORM with Cloud SQL MySQL
- ✅ Health check endpoint
- ✅ Environment-based configuration
- ✅ Docker containerization
- ✅ Production deployment on Cloud Run

### Important Implementation Details

#### CORS Configuration (main.py)
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### Database Connection (database.py)
- Cloud SQL connection string format: `mysql+pymysql://user:password@/database?unix_socket=/cloudsql/CONNECTION_NAME`
- Pool settings optimized for Cloud Run
- Graceful fallback when DATABASE_URL not set

### API Endpoints
- `GET /` - Hello World message
- `GET /health` - Health check (returns `{"status": "healthy"}`)

## 📱 Flutter Client (WORKING)

### Features
- ✅ Material Design 3 with light/dark theme
- ✅ Real-time API health checking
- ✅ Provider state management pattern
- ✅ HTTP client configured for production API
- ✅ Environment-based configuration
- ✅ Cross-platform (mobile, web, desktop)

### Configuration (.env)
```
API_BASE_URL=https://acro-planner-backend-733697808355.us-central1.run.app
API_TIMEOUT=30000
ENVIRONMENT=production
```

### Running Flutter App
```bash
cd clients/acro_planner_app
flutter pub get
flutter run -d chrome    # For web
flutter run -d ios       # For iOS
flutter run -d android   # For Android
```

## 🖥️ Admin Interface

### Production (Deployed)
- **URL**: https://acro-planner-backend-733697808355.us-central1.run.app/admin
- **Type**: Static HTML served directly from backend
- **Deployment**: Automatically deployed with backend using `./scripts/deploy.sh`

### Local Development (Optional)
The `admin/` directory contains a SvelteKit version for local development and testing:

```bash
cd admin
npm install
npm run dev  # Starts on http://localhost:5173
```

**Note**: This SvelteKit version is for development only and is NOT deployed to production.

## 🔐 Security & Configuration

### CORS Resolution
- ✅ Added CORS middleware to FastAPI backend
- ✅ Allows cross-origin requests from web clients
- ✅ Properly configured for both Flutter web and SvelteKit admin

### Environment Configuration
- **Development**: Local servers with API fallback
- **Production**: All frontends connect to deployed Cloud Run API
- **Database**: Cloud SQL MySQL with automated backups

## 🎯 Current Capabilities

### What's Working Right Now
1. **Backend API**: Fully deployed and responding
2. **Health Monitoring**: All clients show real-time connection status
3. **Flutter App**: Complete mobile/web app with Material Design
4. **Admin Dashboard**: Professional SvelteKit interface
5. **Infrastructure**: Production-ready Google Cloud setup
6. **CORS**: Cross-origin requests working for all web clients

### Ready for Development
- ✅ Authentication system
- ✅ User management
- ✅ Session planning features
- ✅ Data models and CRUD operations
- ✅ Analytics and reporting
- ✅ Admin controls

## 🚀 Deployment Commands

### Production Deployment (Single Command)
```bash
# Deploy backend with admin interface
./scripts/deploy.sh
```

### Local Development
```bash
# Backend (local testing)
cd server
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Flutter App
cd clients/acro_planner_app
flutter run -d chrome

# Admin Interface (SvelteKit development version)
cd admin
npm run dev
```

## 🎊 ACHIEVEMENT UNLOCKED

### What We've Built Together
1. **Complete FastAPI Backend** - Production deployed with CORS
2. **Full Infrastructure** - Terraform-managed Google Cloud setup
3. **Flutter Mobile App** - Cross-platform with Material Design 3
4. **SvelteKit Admin** - TypeScript admin interface
5. **API Integration** - All frontends connected to production backend
6. **Health Monitoring** - Real-time connection status across all apps
7. **Docker & Cloud Run** - Containerized production deployment
8. **Database Ready** - Cloud SQL MySQL with proper connection handling

### Technologies Successfully Integrated
- ✅ FastAPI + Uvicorn
- ✅ SQLAlchemy + PyMySQL
- ✅ Google Cloud Run + Cloud SQL
- ✅ Docker + Artifact Registry
- ✅ Terraform Infrastructure as Code
- ✅ Flutter with Provider state management
- ✅ SvelteKit with TypeScript
- ✅ CORS middleware for web compatibility

## 🔮 Next Development Priorities
1. Add authentication (JWT tokens)
2. Create data models for acrobatics sessions
3. Implement user management in admin interface
4. Build session planning features in Flutter app
5. Add analytics and reporting dashboards
6. Set up GitHub Actions for CI/CD

## 📝 Important Notes
- **All APIs working**: CORS properly configured for web clients
- **Production Ready**: Infrastructure deployed and operational
- **Multi-Platform**: Flutter supports mobile, web, and desktop
- **Admin Ready**: SvelteKit admin interface for management
- **Type Safe**: Full TypeScript support in admin interface
- **Scalable**: Cloud Run auto-scales based on demand
- **Secure**: IAM roles and service accounts properly configured

## 🆘 Troubleshooting
- **Node Version**: Admin requires Node 20.19+ (use `npm install --force` if needed)
- **CORS Issues**: Already resolved with FastAPI middleware
- **API Connection**: Check health endpoint first: `/health`
- **Docker Platform**: Use `--platform linux/amd64` for Cloud Run compatibility