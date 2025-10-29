"""
OAuth authentication module for admin interface protection
"""

import os
import secrets
from typing import Optional
from fastapi import Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from itsdangerous import URLSafeTimedSerializer
import logging

logger = logging.getLogger(__name__)

# OAuth configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))

# Base URL for the application
BASE_URL = os.getenv("BASE_URL", "https://acro-planner-backend-733697808355.us-central1.run.app")

# Initialize OAuth
oauth = OAuth()

# Configure Google OAuth
if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        client_kwargs={
            'scope': 'openid email profile'
        },
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration'
    )
    logger.info("Google OAuth configured successfully")
else:
    logger.warning("Google OAuth not configured - missing GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET")

# Session serializer for secure cookies
serializer = URLSafeTimedSerializer(SECRET_KEY)

def init_oauth_middleware(app):
    """Initialize OAuth middleware"""
    app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
    logger.info("OAuth middleware initialized")

def get_current_user(request: Request) -> Optional[dict]:
    """Get current authenticated user from session"""
    try:
        session = request.session
        if 'user' in session:
            # Verify session integrity
            user_data = session['user']
            if isinstance(user_data, dict) and 'email' in user_data:
                return user_data
    except Exception as e:
        logger.error(f"Error retrieving user from session: {e}")
    return None

def require_auth(request: Request) -> dict:
    """Dependency to require authentication"""
    user = get_current_user(request)
    if not user:
        # Redirect to OAuth login
        auth_url = f"{BASE_URL}/auth/login"
        raise HTTPException(
            status_code=302,
            headers={"Location": auth_url}
        )
    return user

async def oauth_login(request: Request):
    """Initiate OAuth login flow"""
    if not (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET):
        raise HTTPException(
            status_code=503,
            detail="OAuth not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables."
        )
    
    redirect_uri = f"{BASE_URL}/auth/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)

async def oauth_callback(request: Request):
    """Handle OAuth callback"""
    try:
        # Get the authorization code and exchange for token
        token = await oauth.google.authorize_access_token(request)
        
        # Get user info
        user_info = token.get('userinfo')
        if not user_info:
            # Fallback: fetch user info manually
            resp = await oauth.google.parse_id_token(token)
            user_info = resp
        
        if not user_info or 'email' not in user_info:
            raise HTTPException(status_code=400, detail="Failed to get user information")
        
        # Store user in session
        request.session['user'] = {
            'email': user_info['email'],
            'name': user_info.get('name', ''),
            'picture': user_info.get('picture', ''),
            'sub': user_info.get('sub', '')
        }
        
        logger.info(f"User authenticated: {user_info['email']}")
        
        # Redirect to admin interface
        return RedirectResponse(url=f"{BASE_URL}/admin")
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

def logout_user(request: Request):
    """Logout user by clearing session"""
    request.session.clear()
    return RedirectResponse(url=f"{BASE_URL}/")

def is_oauth_configured() -> bool:
    """Check if OAuth is properly configured"""
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)