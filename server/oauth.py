"""
OAuth authentication module for admin interface protection
"""

import logging
import os
import secrets

from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse
from itsdangerous import URLSafeTimedSerializer
from starlette.middleware.sessions import SessionMiddleware

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
    app.add_middleware(
        SessionMiddleware, 
        secret_key=SECRET_KEY,
        same_site="none",  # Allow cross-site cookies
        https_only=True    # Require HTTPS for security
    )
    logger.info("OAuth middleware initialized with cross-site cookie support")

def get_current_user(request: Request) -> dict | None:
    """Get current authenticated user from session"""
    try:
        # Debug logging
        logger.info(f"GET_CURRENT_USER: Request headers: {dict(request.headers)}")
        logger.info(f"GET_CURRENT_USER: Cookies: {request.cookies}")
        
        session = request.session
        logger.info(f"GET_CURRENT_USER: Session data: {dict(session)}")
        
        if 'user' in session:
            # Verify session integrity
            user_data = session['user']
            logger.info(f"GET_CURRENT_USER: Found user in session: {user_data}")
            if isinstance(user_data, dict) and 'email' in user_data:
                return user_data
        else:
            logger.info("GET_CURRENT_USER: No user found in session")
    except Exception as e:
        logger.error(f"Error retrieving user from session: {e}")
    return None

def require_auth(request: Request) -> dict:
    """Dependency to require authentication"""
    user = get_current_user(request)
    if not user:
        # Check if this is coming from the admin interface
        is_admin_request = request.url.path.startswith('/admin')
        
        # Redirect to OAuth login with admin flag if needed
        if is_admin_request:
            auth_url = f"{BASE_URL}/auth/login?admin=true"
        else:
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

    # Ensure session is initialized before OAuth flow
    if not hasattr(request, 'session') or request.session is None:
        # Initialize empty session if it doesn't exist
        request.session = {}

    # Store the return URL from query parameter or default to Flutter app
    return_url = request.query_params.get('return_url')
    admin_flag = request.query_params.get('admin')
    
    if admin_flag == 'true':
        # Explicitly requested admin page
        request.session['oauth_return_url'] = f"{BASE_URL}/admin"
        logger.info("Admin flag detected, redirecting to admin page")
    elif return_url:
        # Validate that the return URL is from an allowed source
        if ('storage.googleapis.com' in return_url and 'acro-planner-flutter-app-733697808355' in return_url) or \
           return_url.startswith(BASE_URL):
            request.session['oauth_return_url'] = return_url
            logger.info(f"Storing return URL from query param: {return_url}")
        else:
            # Invalid return URL, default to Flutter app
            request.session['oauth_return_url'] = "https://storage.googleapis.com/acro-planner-flutter-app-733697808355/index.html"
            logger.warning(f"Invalid return URL provided: {return_url}, defaulting to Flutter app")
    else:
        # No return URL provided, default to Flutter app
        request.session['oauth_return_url'] = "https://storage.googleapis.com/acro-planner-flutter-app-733697808355/index.html"
        logger.info("No return URL provided, defaulting to Flutter app")

    redirect_uri = f"{BASE_URL}/auth/callback"

    # Add some debugging
    logger.info(f"Starting OAuth flow with redirect_uri: {redirect_uri}")
    logger.info(f"Session available: {hasattr(request, 'session')}")

    return await oauth.google.authorize_redirect(request, redirect_uri)

async def oauth_callback(request: Request):
    """Handle OAuth callback"""
    try:
        logger.info("OAuth callback received")
        logger.info(f"Session available: {hasattr(request, 'session')}")
        logger.info(f"Query params: {dict(request.query_params)}")

        # Ensure session exists
        if not hasattr(request, 'session'):
            logger.error("No session available in callback")
            raise HTTPException(status_code=400, detail="Session not available")

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

        # Get the stored return URL or default to admin
        return_url = request.session.get('oauth_return_url', f"{BASE_URL}/admin")
        logger.info(f"Redirecting user to: {return_url}")
        
        # Clear the return URL from session
        request.session.pop('oauth_return_url', None)

        # If returning to Flutter app, include auth success indicator
        if 'storage.googleapis.com' in return_url and 'acro-planner-flutter-app-733697808355' in return_url:
            # Add auth success parameter to URL
            separator = '&' if '?' in return_url else '?'
            return_url = f"{return_url}{separator}auth_success=true&email={user_info['email']}"
        
        return RedirectResponse(url=return_url)

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        # If it's a state mismatch, try redirecting back to login to retry
        if "mismatching_state" in str(e).lower() or "csrf" in str(e).lower():
            logger.warning("State mismatch detected, redirecting to login page")
            return RedirectResponse(url=f"{BASE_URL}/")
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

def logout_user(request: Request):
    """Logout user by clearing session"""
    request.session.clear()
    return RedirectResponse(url=f"{BASE_URL}/")

def is_oauth_configured() -> bool:
    """Check if OAuth is properly configured"""
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)
