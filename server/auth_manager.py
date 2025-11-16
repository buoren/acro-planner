"""
JWT-based authentication manager using fastapi-login.

This replaces the session-based authentication system with JWT tokens.
"""

import os
from datetime import timedelta
from typing import Optional
from fastapi import HTTPException, Request
from fastapi_login import LoginManager
from sqlalchemy.orm import Session
from database import get_db
from utils.roles import get_user_with_roles


# Get JWT secret from environment (use SECRET_KEY for consistency with OAuth)
JWT_SECRET = os.getenv("SECRET_KEY", os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-this-in-production"))

# Create LoginManager instance
manager = LoginManager(
    JWT_SECRET, 
    token_url='/auth/token',
    use_cookie=True,  # Enable cookie-based tokens for web clients
    use_header=True   # Also support Authorization header for API clients
)


@manager.user_loader()
def load_user(user_id: str) -> Optional[dict]:
    """
    Load user by ID for JWT token validation.
    
    Args:
        user_id: User ID from JWT token
        
    Returns:
        User dictionary with roles if found, None otherwise
    """
    try:
        print(f"[LOAD_USER] Called with user_id: {user_id}")
        
        # Get database session
        db_gen = get_db()
        db: Session = next(db_gen)
        
        try:
            # Get user with roles
            print(f"[LOAD_USER] Getting user with roles for user_id: {user_id}")
            user_with_roles = get_user_with_roles(db, user_id)
            print(f"[LOAD_USER] get_user_with_roles returned: {user_with_roles}")
            
            if user_with_roles:
                print(f"[LOAD_USER] User found - admin status: {user_with_roles.get('is_admin', False)}")
                print(f"[LOAD_USER] Full user object: {user_with_roles}")
                return user_with_roles
            else:
                print(f"[LOAD_USER] No user found for user_id: {user_id}")
                return None
        finally:
            db.close()
            
    except Exception as e:
        print(f"[LOAD_USER] Error loading user {user_id}: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def create_access_token(user_id: str, expires_delta: Optional[int] = None) -> str:
    """
    Create JWT access token for user.
    
    Args:
        user_id: User ID to include in token
        expires_delta: Token expiration time in minutes (default: 24 hours)
        
    Returns:
        JWT token string
    """
    data = {"sub": user_id}
    if expires_delta:
        return manager.create_access_token(data=data, expires=timedelta(minutes=expires_delta))
    else:
        # Default expiration: 24 hours for better UX
        return manager.create_access_token(data=data, expires=timedelta(hours=24))


async def get_current_user(request: Request) -> Optional[dict]:
    """
    Get current authenticated user from request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User dictionary if authenticated, None otherwise
    """
    try:
        # Debug: Check what cookies are present
        cookie_name = manager.cookie_name
        all_cookies = dict(request.cookies)
        cookie_present = cookie_name in request.cookies
        
        print(f"[AUTH_MANAGER] All cookies available: {list(all_cookies.keys())}")
        print(f"[AUTH_MANAGER] Expected cookie name: '{cookie_name}'")
        print(f"[AUTH_MANAGER] Cookie '{cookie_name}' present: {cookie_present}")
        
        if cookie_present:
            token = request.cookies.get(cookie_name)
            print(f"[AUTH_MANAGER] Token value length: {len(token) if token else 0}")
            print(f"[AUTH_MANAGER] Token first 50 chars: {token[:50] if token else 'None'}...")
            
            # Check for invalid/deleted cookie values
            if not token or token == "" or token == "deleted":
                print(f"[AUTH_MANAGER] Invalid or deleted cookie detected")
                return None
            
            # Manual JWT validation for debugging
            try:
                import jwt
                decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
                print(f"[AUTH_MANAGER] Manual JWT validation SUCCESS: {decoded}")
                user_id = decoded.get('sub')
                print(f"[AUTH_MANAGER] Extracted user_id: {user_id}")
            except Exception as jwt_e:
                print(f"[AUTH_MANAGER] Manual JWT validation FAILED: {jwt_e}")
                return None
                
            # This will validate the JWT token and call load_user()
            # Since load_user is now synchronous, manager() returns the user directly
            try:
                print(f"[AUTH_MANAGER] Calling await manager(request)...")
                user = await manager(request)
                print(f"[AUTH_MANAGER] manager() returned: {user}")
                print(f"[AUTH_MANAGER] manager() returned type: {type(user)}")
                print(f"[AUTH_MANAGER] manager() returned is not None: {user is not None}")
                return user
            except Exception as mgr_e:
                print(f"[AUTH_MANAGER] manager() exception: {type(mgr_e).__name__}: {str(mgr_e)}")
                return None
        else:
            print(f"[AUTH_MANAGER] No cookie present - available cookies: {list(all_cookies.keys())}")
            # No cookie present, no Authorization header to check in this simple case
            return None
    except Exception as e:
        # Handle any authentication errors (invalid token, expired, etc.)
        print(f"[AUTH_MANAGER] Exception in get_current_user: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def require_auth(request: Request) -> dict:
    """
    Require authentication dependency.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User dictionary
        
    Raises:
        HTTPException: If not authenticated
    """
    user = await get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    return user


async def require_admin(request: Request) -> dict:
    """
    Require admin role dependency.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User dictionary (admin user)
        
    Raises:
        HTTPException: If not authenticated or not admin
    """
    user = await require_auth(request)
    if not user.get('is_admin', False):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    return user


async def require_host_or_admin(request: Request) -> dict:
    """
    Require host or admin role dependency.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User dictionary (host or admin user)
        
    Raises:
        HTTPException: If not authenticated or insufficient privileges
    """
    user = await require_auth(request)
    if not (user.get('is_host', False) or user.get('is_admin', False)):
        raise HTTPException(
            status_code=403,
            detail="Host or admin privileges required"
        )
    return user


async def optional_auth(request: Request) -> Optional[dict]:
    """
    Optional authentication dependency.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User dictionary if authenticated, None otherwise
    """
    return await get_current_user(request)


# Export the manager for FastAPI dependency injection
__all__ = [
    'manager',
    'create_access_token', 
    'get_current_user',
    'require_auth',
    'require_admin', 
    'require_host_or_admin',
    'optional_auth'
]