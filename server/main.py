import os
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from api.users import router as users_router
from api.auth import require_admin
from database import get_db
from oauth import (
    get_current_user,
    init_oauth_middleware,
    is_oauth_configured,
    logout_user,
    oauth_callback,
    oauth_login,
    require_auth,
)


# Create all database tables on startup (when database is available)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    database_url = os.getenv("DATABASE_URL")
    print(f"DATABASE_URL environment variable: {'SET' if database_url else 'NOT SET'}")

    if database_url:
        try:
            from database import Base, engine
            print("Attempting to connect to database...")

            # Test connection first
            from sqlalchemy import text
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                print("Database connection test: SUCCESS")

            # Import models to register them with Base
            print("Importing models...")
            print(f"Loaded models: {list(Base.metadata.tables.keys())}")

            # Create tables
            print("Creating database tables...")
            Base.metadata.create_all(bind=engine)
            print("Database tables created successfully")

            # Verify tables exist and check for schema compatibility
            with engine.connect() as conn:
                result = conn.execute(text("SHOW TABLES"))
                tables = [row[0] for row in result.fetchall()]
                print(f"Tables in database: {tables}")

                # Check if users table has correct UUID column size
                if "users" in tables:
                    try:
                        result = conn.execute(text("DESCRIBE users"))
                        columns = {row[0]: row[1] for row in result.fetchall()}

                        # Check if id column is VARCHAR(36) for UUID compatibility
                        id_column_type = columns.get('id', '')
                        print(f"Users table id column type: {id_column_type}")

                        if 'varchar(36)' not in id_column_type.lower():
                            print("Schema mismatch detected: ID column not configured for UUID")
                            print("Dropping and recreating tables with correct UUID schema...")

                            # Drop all tables in correct order (respecting foreign keys)
                            conn.execute(text('SET FOREIGN_KEY_CHECKS = 0'))
                            for table in ['hosts', 'attendees', 'event_slots', 'events', 'capabilities', 'locations', 'equipment', 'users']:
                                conn.execute(text(f'DROP TABLE IF EXISTS {table}'))
                            conn.execute(text('SET FOREIGN_KEY_CHECKS = 1'))
                            conn.commit()

                            # Recreate tables with correct schema
                            Base.metadata.create_all(bind=engine)
                            print("Tables recreated with UUID-compatible schema")
                        else:
                            print("Schema check passed: UUID-compatible columns detected")

                    except Exception as schema_error:
                        print(f"Schema check error: {schema_error}")
                        print("Proceeding with existing tables")

        except Exception as e:
            print(f"Database error during startup: {type(e).__name__}: {str(e)}")
            print("Running without database connection")
    else:
        print("No DATABASE_URL set, running without database connection")
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
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8081",
    ]
    
    if environment == "production":
        return production_origins
    else:
        # In development, allow both production and development origins
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
    
    # Content Security Policy (restrictive for API, but skip for admin/auth routes that set their own CSP)
    if not any(request.url.path.startswith(path) for path in ['/admin', '/auth', '/', '/access-denied']):
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
app.include_router(users_router)

@app.get("/")
async def root(request: Request):
    """Root endpoint - serve login page for unauthenticated users, redirect authenticated users to admin"""
    # Ensure session is initialized
    if not hasattr(request, 'session'):
        # This shouldn't happen with SessionMiddleware, but let's be safe
        request.session = {}

    user = get_current_user(request)
    if user:
        # User is already authenticated, redirect to admin
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/admin", status_code=302)
    else:
        # User not authenticated, serve login page
        # Initialize session to ensure OAuth state can be stored
        if 'session_init' not in request.session:
            request.session['session_init'] = True
        
        from fastapi.responses import HTMLResponse
        with open('static/login.html', 'r') as f:
            content = f.read()
        
        return HTMLResponse(
            content=content,
            headers={
                "Content-Security-Policy": "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data: https://lh3.googleusercontent.com; font-src 'self'; connect-src 'self';"
            }
        )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/favicon.ico")
async def favicon():
    """Return a simple favicon to prevent 404 errors"""
    from fastapi.responses import Response
    # Simple 1x1 transparent PNG as favicon
    favicon_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x1c\x00\x00\x00\x00IEND\xaeB`\x82'
    return Response(content=favicon_bytes, media_type="image/png")

@app.get("/debug/routes")
async def debug_routes():
    """Debug endpoint to list all registered routes"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods) if route.methods else [],
                "name": getattr(route, 'name', None)
            })
    return {"routes": routes}

@app.get("/debug/users-test")
async def debug_users_test():
    """Debug endpoint to test basic users routing without auth"""
    return {"message": "Users routing works", "status": "ok"}

@app.get("/admin")
async def admin_interface(request: Request, db: Session = Depends(get_db)):
    """Serve the protected admin interface"""
    from fastapi.responses import HTMLResponse, RedirectResponse
    from api.auth import get_current_user_with_roles
    
    try:
        # Get current user with roles
        user = get_current_user_with_roles(request, db)
        
        # Check if user is admin
        if not user.get('is_admin', False):
            print(f"[ADMIN_DEBUG] Non-admin user {user.get('email')} attempting to access admin interface")
            return RedirectResponse(url="/access-denied", status_code=302)
        
        print(f"[ADMIN_DEBUG] Admin user authenticated: {user.get('email')}")
        
        # Read the admin HTML file
        with open('static/admin.html', 'r') as f:
            content = f.read()
        
        # Return with relaxed CSP for admin interface
        return HTMLResponse(
            content=content,
            headers={
                "Content-Security-Policy": "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data: https://lh3.googleusercontent.com; font-src 'self';"
            }
        )
    except HTTPException as e:
        # If not authenticated, redirect to login
        if e.status_code == 401:
            return RedirectResponse(url="/login", status_code=302)
        # For any other error, redirect to access-denied
        return RedirectResponse(url="/access-denied", status_code=302)

@app.get("/access-denied")
async def access_denied(request: Request):
    """Serve access denied page for non-admin users"""
    from fastapi.responses import HTMLResponse
    from api.auth import optional_auth
    from database import get_db
    
    # Get database session
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Try to get current user (optional - won't fail if not authenticated)
        user = optional_auth(request, db)
    finally:
        db.close()
    
    # If no user, show generic message
    if not user:
        user = {'name': 'Guest', 'email': 'Not logged in', 'is_admin': False}
    
    access_denied_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Access Denied - Acro Planner</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0;
                color: white;
            }}
            .container {{
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 3rem;
                text-align: center;
                max-width: 500px;
                box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
                border: 1px solid rgba(255, 255, 255, 0.18);
            }}
            h1 {{
                font-size: 2.5rem;
                margin-bottom: 1rem;
                color: #ff6b6b;
            }}
            .emoji {{
                font-size: 4rem;
                margin-bottom: 1rem;
            }}
            .user-info {{
                background: rgba(255, 255, 255, 0.1);
                padding: 1rem;
                border-radius: 10px;
                margin: 1.5rem 0;
            }}
            .btn {{
                background: linear-gradient(45deg, #74b9ff, #0984e3);
                color: white;
                border: none;
                padding: 0.75rem 1.5rem;
                border-radius: 8px;
                text-decoration: none;
                display: inline-block;
                margin: 0.5rem;
                transition: transform 0.3s ease;
            }}
            .btn:hover {{
                transform: translateY(-2px);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="emoji">🚫</div>
            <h1>Access Denied</h1>
            <p>Sorry, you don't have permission to access the admin interface.</p>
            
            <div class="user-info">
                <p><strong>Logged in as:</strong> {user.get('name', 'Unknown')}</p>
                <p><strong>Email:</strong> {user.get('email', 'Unknown')}</p>
                <p><strong>Role:</strong> {'Admin' if user.get('is_admin') else 'User'}</p>
            </div>
            
            <p>If you believe this is an error, please contact your administrator.</p>
            
            <div>
                <a href="/" class="btn">Go to Home</a>
                <a href="/auth/logout" class="btn">Logout</a>
            </div>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(
        content=access_denied_html,
        headers={
            "Content-Security-Policy": "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self';"
        }
    )

# OAuth Authentication Routes
@app.get("/auth/login")
async def login(request: Request):
    """Initiate OAuth login"""
    return await oauth_login(request)

@app.post("/auth/login/password")
async def password_login(request: Request):
    """Handle password-based login"""
    try:
        from pydantic import BaseModel

        class LoginRequest(BaseModel):
            email: str
            password: str

        # Parse request body
        body = await request.json()
        login_data = LoginRequest(**body)

        # Check if database is available
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise HTTPException(status_code=503, detail="Database not available")

        # Authenticate user
        from sqlalchemy.orm import Session

        from database import get_db
        from models import Users
        from utils.auth import verify_password

        # Get database session
        db_gen = get_db()
        db: Session = next(db_gen)

        try:
            # Find user by email
            user = db.query(Users).filter(Users.email == login_data.email).first()

            if not user:
                raise HTTPException(status_code=401, detail="Invalid email or password")
            
            # Check if user is OAuth-only
            if user.oauth_only:
                raise HTTPException(
                    status_code=401, 
                    detail="This account uses OAuth login only. Please use the 'Login with Google' button."
                )

            # Verify password
            if not verify_password(login_data.password, user.password_hash, user.salt):
                raise HTTPException(status_code=401, detail="Invalid email or password")

            # Create session (same format as OAuth)
            session_data = {
                'email': user.email,
                'name': user.name,
                'picture': '',  # No picture for password login
                'sub': user.id,  # Use user ID as sub
                'auth_method': 'password'
            }
            request.session['user'] = session_data
            
            # Debug logging
            print(f"PASSWORD_LOGIN: Created session for user {user.email}")
            print(f"PASSWORD_LOGIN: Session data: {session_data}")
            print(f"PASSWORD_LOGIN: Request headers: {dict(request.headers)}")
            print(f"PASSWORD_LOGIN: Response cookies will be set for domain: {request.url.hostname}")

            return {"success": True, "message": "Login successful", "redirect": "/admin"}

        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.get("/auth/callback")
async def auth_callback(request: Request):
    """Handle OAuth callback"""
    return await oauth_callback(request)

@app.get("/auth/logout")
async def logout(request: Request):
    """Logout user"""
    return logout_user(request)

@app.get("/auth/me")
async def get_me(request: Request):
    """Get current user info"""
    user = get_current_user(request)
    if user:
        return {"user": user, "authenticated": True}
    return {"user": None, "authenticated": False}

@app.get("/auth/status")
async def auth_status():
    """Check OAuth configuration status"""
    return {
        "oauth_configured": is_oauth_configured(),
        "message": "OAuth is configured" if is_oauth_configured() else "OAuth not configured - set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"
    }

@app.post("/auth/promote-to-admin")
async def promote_current_user_to_admin(request: Request):
    """Promote current user to admin (temporary endpoint for initial setup)"""
    from oauth import get_current_user
    from sqlalchemy.orm import Session
    from database import get_db
    from utils.roles import add_admin_role
    
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = user.get('sub')
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user session")
    
    # Get database session
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        # Add admin role
        add_admin_role(db, user_id)
        return {"success": True, "message": "User promoted to admin successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to promote user: {str(e)}")
    finally:
        db.close()

# Legacy endpoint for backward compatibility
# The new endpoint is at /users/register
@app.post("/add_user")
async def add_user_legacy(user_data: dict):
    """Legacy endpoint - redirects to /users/register"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/users/register", status_code=307)
