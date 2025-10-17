from fastapi import FastAPI
from contextlib import asynccontextmanager
import os

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

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}