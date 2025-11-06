"""
Authentication and authorization dependencies for API endpoints.
"""

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from auth_manager import require_auth as jwt_require_auth, require_admin as jwt_require_admin, require_host_or_admin as jwt_require_host_or_admin, optional_auth as jwt_optional_auth
from utils.roles import is_admin, is_host_or_admin, get_user_with_roles


def get_current_user_with_roles(
    request: Request,
    db: Session = Depends(get_db)
) -> dict:
    """
    Get current authenticated user with role information.
    
    Returns:
        User dictionary with role information
        
    Raises:
        HTTPException: If user is not authenticated
    """
    # Use the JWT auth manager which already handles user lookup with roles
    return jwt_require_auth(request)


def require_auth(
    request: Request,
    db: Session = Depends(get_db)
) -> dict:
    """
    Dependency to require authentication.
    
    Returns:
        User dictionary with role information
        
    Raises:
        HTTPException: If user is not authenticated
    """
    return jwt_require_auth(request)


def require_admin(
    request: Request,
    db: Session = Depends(get_db)
) -> dict:
    """
    Dependency to require admin role.
    
    Returns:
        User dictionary (admin user)
        
    Raises:
        HTTPException: If user is not admin
    """
    return jwt_require_admin(request)


def require_host_or_admin(
    request: Request,
    db: Session = Depends(get_db)
) -> dict:
    """
    Dependency to require host or admin role.
    
    Returns:
        User dictionary (host or admin user)
        
    Raises:
        HTTPException: If user is not host or admin
    """
    return jwt_require_host_or_admin(request)


def require_attendee(
    request: Request,
    db: Session = Depends(get_db)
) -> dict:
    """
    Dependency to require attendee role.
    
    Args:
        request: FastAPI request object
        db: Database session
        
    Returns:
        User dictionary (attendee user)
        
    Raises:
        HTTPException: If user is not attendee
    """
    user = jwt_require_auth(request)
    if not user.get('is_attendee', False):
        raise HTTPException(
            status_code=403,
            detail="Attendee privileges required"
        )
    return user


def optional_auth(
    request: Request,
    db: Session = Depends(get_db)
) -> dict | None:
    """
    Optional authentication dependency.
    
    Returns:
        User dictionary with role information if authenticated, None otherwise
    """
    return jwt_optional_auth(request)


def require_self_or_admin(user_id: str):
    """
    Factory function to create a dependency that requires the user to be 
    either the same user or an admin.
    
    Args:
        user_id: The user ID being accessed
        
    Returns:
        Dependency function
    """
    def _require_self_or_admin(
        request: Request,
        db: Session = Depends(get_db)
    ) -> dict:
        user = jwt_require_auth(request)
        if user['id'] != user_id and not user.get('is_admin', False):
            raise HTTPException(
                status_code=403,
                detail="Access denied: can only access own data or admin required"
            )
        return user
    
    return _require_self_or_admin