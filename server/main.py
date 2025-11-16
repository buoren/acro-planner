import os
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from api.routes.users import router as users_router
from api.routes.core import router as core_router
from api.routes.auth_routes import router as auth_routes_router
from api.routes.admin import router as admin_router
from api.routes.app import router as app_router
from api.routes.conventions import router as conventions_router
from api.routes.prerequisites import router as prerequisites_router
from api.routes.equipment import router as equipment_router
from api.routes.workshops import router as workshops_router
from api.routes.attendees import router as attendees_router
from api.routes.event_slots import router as event_slots_router
from oauth import (
    init_oauth_middleware,
    is_oauth_configured,
    logout_user,
    oauth_callback,
    oauth_login,
)
from auth_manager import get_current_user


# Verify database connection on startup (read-only, no changes)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    database_url = os.getenv("DATABASE_URL")
    
    # Fail fast if DATABASE_URL is not set
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is required but not set. Application cannot start without a database.")
    
    print(f"DATABASE_URL environment variable: SET")

    # Test database connection (read-only)
    # Fail fast if connection cannot be established
    from database import engine
    print("Attempting to connect to database...")

    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("Database connection test: SUCCESS")
    except Exception as e:
        raise RuntimeError(f"Failed to connect to database: {type(e).__name__}: {str(e)}. Application cannot start without a database connection.")
    
    yield
    # Shutdown

app = FastAPI(
    title="Acro Planner API",
    description="Backend API for Acro Planner application",
    version="0.1.0",
    lifespan=lifespan
)

# Initialize OAuth middleware (must be before CORS)
init_oauth_middleware(app)

# Add CORS middleware with specific allowed origins
# Environment-based CORS configuration for security
def get_allowed_origins():
    """Get allowed CORS origins based on environment"""
    environment = os.getenv("ENVIRONMENT", "development")
    
    # Production origins
    production_origins = [
        "https://acro-planner-backend-733697808355.us-central1.run.app",  # Backend itself
        "https://storage.googleapis.com",  # Flutter app on GCS
    ]
    
    # Development origins
    development_origins = [
        "http://localhost:3000",   # React dev
        "http://localhost:5173",   # SvelteKit dev  
        "http://localhost:8080",   # Flutter dev
        "http://localhost:8081",   # Flutter dev alt port
        "http://localhost:8095",   # Flutter dev alt port 2
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8081",
        "http://127.0.0.1:8095",
    ]
    
    # Always allow development origins for testing
    # In production, we still need to test locally so include development origins
    return production_origins + development_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),  # Specific origins only - NO wildcards
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],  # Specific methods
    allow_headers=["*"],  # Keep headers flexible for now
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Basic security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Content Security Policy (restrictive for API, but skip for admin/auth/app routes that set their own CSP)
    if not any(request.url.path.startswith(path) for path in ['/admin', '/auth', '/app', '/', '/access-denied']):
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none';"
    
    # HTTPS-only headers for production
    environment = os.getenv("ENVIRONMENT", "development")
    if environment == "production":
        # Strict Transport Security (HSTS) - 1 year
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    
    return response

# Request Logging Middleware (for debugging)
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log requests for debugging purposes"""
    import datetime
    
    timestamp = datetime.datetime.now().isoformat()
    method = request.method
    path = request.url.path
    headers = dict(request.headers)
    
    print(f"[{timestamp}] {method} {path}")
    print(f"  User-Agent: {headers.get('user-agent', 'N/A')}")
    print(f"  Referer: {headers.get('referer', 'N/A')}")
    print(f"  Cookie: {'Present' if headers.get('cookie') else 'None'}")
    
    response = await call_next(request)
    
    print(f"  Response: {response.status_code}")
    
    return response

# Rate Limiting Middleware
# Simple in-memory rate limiter - in production, use Redis for distributed rate limiting
rate_limit_storage = defaultdict(lambda: deque())

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware to prevent abuse"""
    
    # Get client IP (considering proxy headers for Cloud Run)
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if not client_ip:
        client_ip = request.headers.get("X-Real-IP", "")
    if not client_ip:
        client_ip = getattr(request.client, "host", "unknown")
    
    # Rate limiting configuration
    current_time = time.time()
    rate_limits = {
        # Endpoint-specific rate limits (requests per minute)
        "/users/register": 5,      # 5 registrations per minute per IP
        "/auth/login": 10,         # 10 login attempts per minute per IP
        "/auth/callback": 20,      # OAuth callbacks
        "/auth/forgot-password": 3, # 3 forgot password attempts per minute per IP
        "/auth/reset-password": 5, # 5 reset attempts per minute per IP
        "default": 100,            # 100 requests per minute per IP for other endpoints
    }
    
    # Get rate limit for this endpoint
    path = request.url.path
    limit = rate_limits.get(path, rate_limits["default"])
    
    # Create key for this IP + endpoint combination
    key = f"{client_ip}:{path}"
    
    # Clean old entries (older than 1 minute)
    requests = rate_limit_storage[key]
    while requests and requests[0] < current_time - 60:
        requests.popleft()
    
    # Check if rate limit exceeded
    if len(requests) >= limit:
        # Create rate limit exceeded exception with headers
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Limit: {limit} requests per minute.",
                "retry_after": 60
            },
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(current_time + 60)),
                "Retry-After": "60"
            }
        )
    
    # Add current request to tracking
    requests.append(current_time)
    
    # Process the request
    response = await call_next(request)
    
    # Add rate limit headers to successful responses
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(limit - len(requests))
    response.headers["X-RateLimit-Reset"] = str(int(current_time + 60))
    
    return response

# SSL/HTTPS enforcement middleware
# Note: In production, SSL should be enforced at the load balancer/reverse proxy level
# For Cloud Run, HTTPS is automatically enforced
# For local development with self-signed certs, you can use:
# uvicorn main:app --ssl-keyfile=./key.pem --ssl-certfile=./cert.pem

# Mount static files for admin interface
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routers
app.include_router(core_router)
app.include_router(users_router)
app.include_router(auth_routes_router)
app.include_router(admin_router)
app.include_router(app_router)
app.include_router(conventions_router)
app.include_router(prerequisites_router)
app.include_router(equipment_router)
app.include_router(workshops_router)
app.include_router(attendees_router)
app.include_router(event_slots_router)
