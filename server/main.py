from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from api.users import router as users_router

# Create all database tables on startup (when database is available)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if os.getenv("DATABASE_URL"):
        try:
            from database import engine, Base
            Base.metadata.create_all(bind=engine)
            print("Database tables created successfully")
        except Exception as e:
            print(f"Database connection skipped: {e}")
            print("Running without database connection")
    yield
    # Shutdown

app = FastAPI(
    title="Acro Planner API",
    description="Backend API for Acro Planner application",
    version="0.1.0",
    lifespan=lifespan
)

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

# Include API routers
app.include_router(users_router)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Legacy endpoint for backward compatibility
# The new endpoint is at /users/register
@app.post("/add_user")
async def add_user_legacy(user_data: dict):
    """Legacy endpoint - redirects to /users/register"""
    from fastapi import Request
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/users/register", status_code=307)