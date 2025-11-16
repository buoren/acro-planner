"""
Core API endpoints (health, root, favicon, debug).
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from database import get_db
from utils.system_settings import get_frontend_url

router = APIRouter(tags=["core"])


@router.get("/")
async def root():
    """Root endpoint - redirect to /app for React Native app"""
    return RedirectResponse(url="/app", status_code=302)


@router.get("/health")
async def health_check():
    return {"status": "healthy"}


@router.get("/favicon.ico")
async def favicon():
    """Return a simple favicon to prevent 404 errors"""
    # Simple 1x1 transparent PNG as favicon
    favicon_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x00\x01\x00\x18\xdd\x8d\xb4\x1c\x00\x00\x00\x00IEND\xaeB`\x82'
    return Response(content=favicon_bytes, media_type="image/png")


@router.get("/access-denied")
async def access_denied(request: Request):
    """Serve access denied page for non-admin users"""
    from database import get_db
    from api.auth import optional_auth
    
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
    
    # Read the HTML template and format it with user data
    with open('static/access_denied.html', 'r') as f:
        access_denied_html = f.read().format(
            user_name=user.get('name', 'Unknown'),
            user_email=user.get('email', 'Unknown'),
            user_role='Admin' if user.get('is_admin') else 'User'
        )
    
    return HTMLResponse(
        content=access_denied_html,
        headers={
            "Content-Security-Policy": "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self';"
        }
    )
