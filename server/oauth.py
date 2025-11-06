"""
OAuth authentication module for admin interface protection
"""

import logging
import os
import secrets

from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from itsdangerous import URLSafeTimedSerializer
from starlette.middleware.sessions import SessionMiddleware
from auth_manager import create_access_token, manager
from utils.roles import get_user_with_roles
from database import get_db
from sqlalchemy.orm import Session

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

async def get_current_user(request: Request) -> dict | None:
    """Get current authenticated user from JWT token"""
    try:
        # Use the JWT-based authentication manager
        from auth_manager import get_current_user as jwt_get_current_user
        return await jwt_get_current_user(request)
    except Exception as e:
        logger.error(f"Error retrieving user from JWT: {e}")
        return None

async def require_auth(request: Request) -> dict:
    """Dependency to require authentication"""
    user = await get_current_user(request)
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

        logger.info(f"User authenticated: {user_info['email']}")

        # Get database session to look up user with roles
        db_gen = get_db()
        db: Session = next(db_gen)
        
        try:
            # Find user by email
            from models import Users
            existing_user = db.query(Users).filter(Users.email == user_info['email']).first()
            
            if not existing_user:
                # Create new user automatically
                from ulid import ULID
                new_user_id = str(ULID())
                new_user = Users(
                    id=new_user_id,
                    email=user_info['email'],
                    name=user_info.get('name', user_info['email'].split('@')[0])
                )
                db.add(new_user)
                db.commit()
                logger.info(f"Created new user in database: {user_info['email']} with ID: {new_user_id}")
                user_id = new_user_id
            else:
                user_id = existing_user.id
                logger.info(f"Found existing user: {user_info['email']} with ID: {user_id}")
            
            # Create JWT token with user ID
            access_token = create_access_token(user_id)
            
            logger.info(f"JWT token created for user: {user_id}")

        finally:
            db.close()

        # Get the stored return URL or default to admin
        return_url = request.session.get('oauth_return_url', f"{BASE_URL}/admin") if hasattr(request, 'session') else f"{BASE_URL}/admin"
        logger.info(f"Redirecting user to: {return_url}")
        
        # Clear the return URL from session if it exists
        if hasattr(request, 'session'):
            request.session.pop('oauth_return_url', None)

        # If returning to Flutter app, include auth success indicator
        if 'storage.googleapis.com' in return_url and 'acro-planner-flutter-app-733697808355' in return_url:
            # Add auth success parameter to URL
            separator = '&' if '?' in return_url else '?'
            return_url = f"{return_url}{separator}auth_success=true&email={user_info['email']}"

        # Create response with JWT cookie
        response = RedirectResponse(url=return_url)
        
        # Set JWT token as HTTP-only cookie
        response.set_cookie(
            key=manager.cookie_name,
            value=access_token,
            httponly=True,
            secure=True,  # HTTPS only
            samesite="none",  # Allow cross-site cookies
            max_age=24 * 60 * 60  # 24 hours
        )
        
        return response

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        # If it's a state mismatch, try redirecting back to login to retry
        if "mismatching_state" in str(e).lower() or "csrf" in str(e).lower():
            logger.warning("State mismatch detected, redirecting to login page")
            return RedirectResponse(url=f"{BASE_URL}/")
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

def logout_user(request: Request):
    """Logout user by clearing JWT cookie"""
    response = RedirectResponse(url=f"{BASE_URL}/")
    
    # Clear the JWT cookie
    response.delete_cookie(
        key=manager.cookie_name,
        secure=True,
        samesite="none"
    )
    
    return response

def is_oauth_configured() -> bool:
    """Check if OAuth is properly configured"""
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)
