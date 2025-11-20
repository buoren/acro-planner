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
BASE_URL = os.getenv("BASE_URL", "https://acro.vaguely.nl")

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
    """Initialize OAuth middleware with path exclusions"""
    
    # Add session middleware normally - we'll handle exclusions at the endpoint level
    app.add_middleware(
        SessionMiddleware,
        secret_key=SECRET_KEY,
        same_site="none",  # Allow cross-site cookies
        https_only=True,   # Require HTTPS for security
    )
    logger.info("OAuth middleware initialized with session middleware")

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
        
        # Check if this is coming from the React Native app
        is_app_request = request.url.path.startswith('/app')
        referer = request.headers.get('referer', '')
        from_react_native_app = '/app' in referer
        
        # Redirect to OAuth login with appropriate context
        if is_admin_request:
            auth_url = f"{BASE_URL}/auth/login?admin=true"
        elif is_app_request or from_react_native_app:
            # Include return_url to ensure we come back to the React Native app
            auth_url = f"{BASE_URL}/auth/login?return_url={BASE_URL}/app"
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

    # Store the return URL from query parameter or determine from context
    return_url = request.query_params.get('return_url')
    admin_flag = request.query_params.get('admin')
    
    # Check if the request came from the React Native app by looking at the Referer header
    referer = request.headers.get('referer', '')
    from_react_native_app = '/app' in referer
    
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
            # Invalid return URL, determine based on context
            if from_react_native_app:
                request.session['oauth_return_url'] = f"{BASE_URL}/app"
                logger.info(f"Invalid return URL provided but came from React Native app, redirecting to /app")
            else:
                # Get current frontend URL from database
                db_gen = get_db()
                db: Session = next(db_gen)
                try:
                    from utils.system_settings import get_frontend_url
                    default_frontend_url = get_frontend_url(db)
                finally:
                    db.close()
                
                request.session['oauth_return_url'] = default_frontend_url
                logger.warning(f"Invalid return URL provided: {return_url}, defaulting to Flutter app from database: {default_frontend_url}")
    else:
        # No return URL provided, determine based on context
        if from_react_native_app:
            request.session['oauth_return_url'] = f"{BASE_URL}/app"
            logger.info(f"No return URL provided but came from React Native app, redirecting to /app")
        else:
            # Get current frontend URL from database
            db_gen = get_db()
            db: Session = next(db_gen)
            try:
                from utils.system_settings import get_frontend_url
                default_frontend_url = get_frontend_url(db)
            finally:
                db.close()
                
            request.session['oauth_return_url'] = default_frontend_url
            logger.info(f"No return URL provided, defaulting to Flutter app from database: {default_frontend_url}")

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
                
                # Check if this is the first user - if so, make them an admin
                user_count = db.query(Users).count()
                if user_count == 1:
                    from utils.roles import add_admin_role
                    try:
                        add_admin_role(db, user_id)
                        logger.info(f"First user {user_info['email']} promoted to admin automatically")
                    except Exception as e:
                        logger.warning(f"Failed to auto-promote first user to admin: {e}")
                        # Don't fail the login if admin promotion fails
            else:
                user_id = existing_user.id
                logger.info(f"Found existing user: {user_info['email']} with ID: {user_id}")
            
            # Create JWT token with user ID
            access_token = create_access_token(user_id)
            
            logger.info(f"JWT token created for user: {user_id}")
            logger.info(f"JWT token length: {len(access_token)}")
            logger.info(f"JWT token first 50 chars: {access_token[:50]}...")
            logger.info(f"Cookie name: {manager.cookie_name}")
            
            # Test JWT token validation
            try:
                import jwt
                from auth_manager import JWT_SECRET
                decoded = jwt.decode(access_token, JWT_SECRET, algorithms=["HS256"])
                logger.info(f"JWT token validation test: SUCCESS - {decoded}")
            except Exception as jwt_e:
                logger.error(f"JWT token validation test: FAILED - {jwt_e}")

        finally:
            db.close()

        # Get the stored return URL or default to admin
        return_url = request.session.get('oauth_return_url', f"{BASE_URL}/admin") if hasattr(request, 'session') else f"{BASE_URL}/admin"
        
        # If return URL is absolute and points to our domain, convert to relative path
        if return_url.startswith(BASE_URL):
            return_url = return_url.replace(BASE_URL, "")
            if not return_url:
                return_url = "/admin"
        
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
        cookie_name = manager.cookie_name
        cookie_settings = {
            "key": cookie_name,
            "value": access_token,
            "httponly": True,
            "secure": True,
            "samesite": "lax",
            "max_age": 24 * 60 * 60,
            "path": "/",
            "domain": None
        }
        
        logger.info(f"Setting cookie '{cookie_name}' with value length: {len(access_token)}")
        logger.info(f"Cookie settings: {cookie_settings}")
        logger.info(f"Redirect URL: {return_url}")
        
        response.set_cookie(**cookie_settings)
        
        # Verify cookie was set in response headers
        if hasattr(response, 'headers'):
            cookie_header = response.headers.get('Set-Cookie', '')
            logger.info(f"Set-Cookie header: {cookie_header}")
        
        logger.info(f"Cookie set successfully, redirecting to: {return_url}")
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
    cookie_name = manager.cookie_name
    logger.info(f"Logging out user, deleting cookie '{cookie_name}'")
    
    # Get redirect URL - default to root, but check for return URL
    redirect_url = request.query_params.get("return_url", f"{BASE_URL}/")
    
    # If redirect URL is absolute and points to our domain, convert to relative path
    if redirect_url.startswith(BASE_URL):
        redirect_url = redirect_url.replace(BASE_URL, "")
        if not redirect_url:
            redirect_url = "/"
    
    response = RedirectResponse(url=redirect_url)
    
    # Clear the JWT cookie by setting it to "deleted" with immediate expiration
    # Setting to a non-empty invalid value ensures fastapi-login won't treat it as valid
    response.set_cookie(
        key=cookie_name,
        value="deleted",  # Invalid JWT value that will fail validation
        max_age=0,  # Expire immediately
        expires=0,  # Expire immediately
        path="/",  # Must match the path used when setting the cookie
        secure=True,  # Must match secure setting
        httponly=True,  # Must match httponly setting
        samesite="none"  # Must match samesite setting
    )
    
    logger.info(f"Cookie '{cookie_name}' deleted, redirecting to: {redirect_url}")
    return response

def is_oauth_configured() -> bool:
    """Check if OAuth is properly configured"""
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)
