"""
Admin interface and admin-related API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from auth_manager import get_current_user
from utils.system_settings import get_frontend_url, set_system_setting

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("")
async def admin_interface(request: Request, db: Session = Depends(get_db)):
    """Serve the protected admin interface"""
    try:
        # Get current user with roles
        user = await get_current_user(request)
        
        if not user:
            # User not authenticated, redirect to login
            return RedirectResponse(url="/auth/login?admin=true", status_code=302)
        
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


@router.get("/current-frontend-url")
async def get_current_frontend_url(db: Session = Depends(get_db)):
    """Get the current frontend URL from system settings."""
    try:
        frontend_url = get_frontend_url(db)
        return {
            "success": True,
            "frontend_url": frontend_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get frontend URL: {str(e)}")