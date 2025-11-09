# Claude Context - Acro Planner Project

## Project Overview
Complete Acro Planner application with FastAPI backend deployed to Google Cloud, Flutter mobile/web app deployed to GCS, and admin interface served from backend.

## 🚀 CURRENT STATUS: FULLY DEPLOYED AND OPERATIONAL

### Live Production URLs
- **Production API**: https://acro-planner-backend-733697808355.us-central1.run.app
- **Health Check**: https://acro-planner-backend-733697808355.us-central1.run.app/health
- **Admin Interface**: https://acro-planner-backend-733697808355.us-central1.run.app/admin (OAuth-protected)
- **Flutter Web App**: https://storage.googleapis.com/acro-planner-flutter-app-733697808355/release_20251105_210028/index.html

## 🌐 USER ACCESS GUIDE

### For Regular Users (Flutter App Access)
**Primary URL**: https://storage.googleapis.com/acro-planner-flutter-app-733697808355/release_20251105_210028/index.html
- Main user interface for acrobatics session planning
- Material Design 3 responsive interface
- Works on mobile, tablet, and desktop browsers
- Supports both light and dark themes
- Real-time API connectivity status

### For Admin Users (Administrative Access)
**Admin URL**: https://acro-planner-backend-733697808355.us-central1.run.app/admin
- OAuth 2.0 authentication required (Google account)
- Administrative dashboard for user management
- Content Security Policy configured for admin functionality
- Automatically redirects to Google OAuth if not authenticated
- Returns to admin interface after successful authentication

### For Developers (Testing & Development)
**API Base URL**: https://acro-planner-backend-733697808355.us-central1.run.app
- Direct API access for testing endpoints
- Health check: `/health`
- Authentication endpoints: `/auth/login`, `/auth/callback`, `/auth/logout`
- User management: `/users/register`, `/users/login`
- All endpoints support CORS for web client development

### Authentication Flow URLs
1. **Login Initiation**: `/auth/login` (supports `?admin=true` for admin flows)
2. **OAuth Callback**: `/auth/callback` (handles Google OAuth responses)
3. **User Status Check**: `/auth/me` (returns current authentication state)
4. **Logout**: `/auth/logout` (clears session and redirects)

## 🔥 CRITICAL DEPLOYMENT WORKFLOW
**ALWAYS DEPLOY TO PRODUCTION AFTER EVERY FIX UNLESS TOLD OTHERWISE**

### ⚠️ CRITICAL RULE: NO CHANGE IS COMPLETE UNTIL DEPLOYED
- **Code changes are NOT considered tested or done until deployed to production**
- **Always deploy and verify in production environment before marking tasks complete**
- **Never assume local testing is sufficient - production deployment is the final validation**

### Primary Deployment Tools
1. **Backend Deployment**: `./scripts/deploy.sh`
   - Builds and deploys backend to Cloud Run
   - Includes admin interface as static files
   - Updates OAuth environment variables
   - NOT terraform (terraform is only for infrastructure)

2. **Frontend Deployment**: `./scripts/deploy-frontend.sh`
   - Builds Flutter web app with timestamped subdirectory base href
   - Deploys to Google Cloud Storage bucket with cache-busting subdirectories
   - Configures public access for static hosting
   - **NEVER manually run flutter build + gsutil - ALWAYS use this script**
   - **SUBDIRECTORY APPROACH MANDATORY** - ensures proper resource loading

### Testing Protocol
- **ALWAYS test fixes against production endpoints** after deployment
- **NO TASK IS COMPLETE without production deployment and verification**
- Verify functionality with live production URLs
- Ensure changes are working in the real environment, not just locally
- Mark todos as completed ONLY after successful production deployment

### Deployment Commands
```bash
# Backend deployment (from project root)
./scripts/deploy.sh

# Flutter web app deployment (from project root)
./scripts/deploy-frontend.sh

# Both can be run independently as needed
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
├── .env.oauth                # OAuth credentials for backend authentication
├── scripts/                  # Deployment scripts
│   ├── deploy.sh            # Backend deployment to Cloud Run
│   ├── deploy-frontend.sh   # Flutter web deployment to GCS
│   └── set-env-vars.sh      # OAuth environment setup
└── CLAUDE.md                # This context file
```

## 🏗️ Infrastructure (DEPLOYED)

### Google Cloud Project: `acro-session-planner`
- **Cloud Run Service**: acro-planner-backend (us-central1)
- **Cloud SQL**: MySQL 8.0 instance with automated backups
- **Artifact Registry**: Docker container registry for backend images
- **Cloud Storage Bucket**: acro-planner-flutter-app-733697808355 (static web hosting)
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
- ✅ OAuth 2.0 authentication (Google provider)
- ✅ CORS middleware for web client support
- ✅ SQLAlchemy ORM with Cloud SQL MySQL
- ✅ Health check endpoint
- ✅ Static admin interface served at /admin
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
- `GET /admin` - Admin interface (OAuth-protected, redirects to login)
- `GET /login` - OAuth login page
- `GET /auth/google` - Google OAuth callback
- `POST /api/users` - Create new user
- `GET /api/users` - List all users (paginated)

## 📱 Flutter Client (DEPLOYED)

### Features
- ✅ Material Design 3 with light/dark theme
- ✅ Real-time API health checking
- ✅ Provider state management pattern
- ✅ HTTP client configured for production API
- ✅ Environment-based configuration
- ✅ Cross-platform (mobile, web, desktop)
- ✅ Web version deployed to Google Cloud Storage

### Configuration (.env)
```
API_BASE_URL=https://acro-planner-backend-733697808355.us-central1.run.app
API_TIMEOUT=30000
ENVIRONMENT=production
```

### Access Methods
- **Web (Production)**: https://storage.googleapis.com/acro-planner-flutter-app-733697808355/index.html
- **Local Development**:
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
- **Type**: Static HTML served directly from backend (`server/static/admin.html`)
- **Authentication**: OAuth 2.0 with Google provider
- **Deployment**: Automatically deployed with backend using `./scripts/deploy.sh`
- **OAuth Credentials**: Stored in `.env.oauth` (not committed to git) The production admin uses the static HTML file in `server/static/`.

## 🔐 Security & Configuration

### OAuth 2.0 Authentication
- **Provider**: Google OAuth
- **Client ID**: `733697808355-6e0pbdfaedl0ito1ucklgo1okq2k727s.apps.googleusercontent.com`
- **Protected Routes**: `/admin` endpoint requires authentication
- **Session Management**: Encrypted sessions with AUTH_SECRET

### CORS Configuration
- ✅ Added CORS middleware to FastAPI backend
- ✅ Allows cross-origin requests from web clients
- ✅ Properly configured for Flutter web app

### Environment Configuration
- **Development**: Local servers with hot reload
- **Production**: All services deployed to Google Cloud
- **Database**: Cloud SQL MySQL with automated backups
- **Storage**: GCS bucket for Flutter web static hosting

## 🎯 Current Capabilities

### What's Working Right Now
1. **Backend API**: Fully deployed and responding with OAuth authentication
2. **Health Monitoring**: All clients show real-time connection status
3. **Flutter Web App**: Deployed to GCS with Material Design 3 UI
4. **Admin Dashboard**: OAuth-protected interface served from backend
5. **Infrastructure**: Production-ready Google Cloud setup
6. **Static Hosting**: GCS bucket serving Flutter web app
7. **CORS**: Cross-origin requests working for all web clients

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

### Flutter Frontend Deployment
```bash
# Deploy Flutter frontend using deployment script
./scripts/deploy-frontend.sh

# Follow the script's instructions to update backend environment variable
```

**⚠️ Critical Flutter Deployment Note**: 
The `deploy-frontend.sh` script automatically handles the correct `--base-href` flag required when deploying to subdirectories. Without this flag, Flutter apps will get 404 errors on assets when deployed to Google Cloud Storage subdirectories.

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