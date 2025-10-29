from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
import os

from api.users import router as users_router
from oauth import (
    init_oauth_middleware, 
    require_auth, 
    oauth_login, 
    oauth_callback, 
    logout_user,
    get_current_user,
    is_oauth_configured
)

# Create all database tables on startup (when database is available)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    database_url = os.getenv("DATABASE_URL")
    print(f"DATABASE_URL environment variable: {'SET' if database_url else 'NOT SET'}")
    
    if database_url:
        try:
            from database import engine, Base
            print(f"Attempting to connect to database...")
            
            # Test connection first
            from sqlalchemy import text
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                print("Database connection test: SUCCESS")
            
            # Import models to register them with Base
            print("Importing models...")
            import models
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
async def root(request: Request, user: dict = Depends(require_auth)):
    """Root endpoint - requires authentication, redirects to admin after login"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/admin", status_code=302)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/admin")
async def admin_interface(request: Request, user: dict = Depends(require_auth)):
    """Serve the protected admin interface"""
    return FileResponse('static/admin.html')

# OAuth Authentication Routes
@app.get("/auth/login")
async def login(request: Request):
    """Initiate OAuth login"""
    return await oauth_login(request)

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

# Legacy endpoint for backward compatibility
# The new endpoint is at /users/register
@app.post("/add_user")
async def add_user_legacy(user_data: dict):
    """Legacy endpoint - redirects to /users/register"""
    from fastapi import Request
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/users/register", status_code=307)