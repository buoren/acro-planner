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


# Get JWT secret from environment
JWT_SECRET = os.getenv("JWT_SECRET", "your-super-secret-jwt-key-change-this-in-production")

# Create LoginManager instance
manager = LoginManager(
    JWT_SECRET, 
    token_url='/auth/token',
    use_cookie=True,  # Enable cookie-based tokens for web clients
    use_header=True   # Also support Authorization header for API clients
)


@manager.user_loader()
async def load_user(user_id: str) -> Optional[dict]:
    """
    Load user by ID for JWT token validation.
    
    Args:
        user_id: User ID from JWT token
        
    Returns:
        User dictionary with roles if found, None otherwise
    """
    try:
        # Get database session
        db_gen = get_db()
        db: Session = next(db_gen)
        
        try:
            # Get user with roles
            user_with_roles = get_user_with_roles(db, user_id)
            if user_with_roles:
                return user_with_roles
            return None
        finally:
            db.close()
            
    except Exception as e:
        print(f"[AUTH_MANAGER] Error loading user {user_id}: {e}")
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
        # This will validate the JWT token and call load_user()
        user = await manager(request)
        return user
    except Exception as e:
        # Handle any authentication errors (invalid token, expired, etc.)
        if "credentials" in str(e).lower() or "invalid" in str(e).lower() or "expired" in str(e).lower():
            return None
        print(f"[AUTH_MANAGER] Error getting current user: {e}")
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