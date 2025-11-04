"""
Authentication and authorization dependencies for API endpoints.
"""

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from oauth import get_current_user
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
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    # Get user with role information
    user_id = user.get('sub')
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid user session"
        )
    
    user_with_roles = get_user_with_roles(db, user_id)
    if not user_with_roles:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # Merge session data with role data
    return {
        **user_with_roles,
        "session_email": user.get('email'),
        "session_name": user.get('name'),
        "auth_method": user.get('auth_method', 'oauth')
    }


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
    return get_current_user_with_roles(request, db)


def require_admin(
    user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
) -> dict:
    """
    Dependency to require admin role.
    
    Args:
        user: Current authenticated user
        db: Database session
        
    Returns:
        User dictionary (admin user)
        
    Raises:
        HTTPException: If user is not admin
    """
    if not user or not user.get('is_admin', False):
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    
    return user


def require_host_or_admin(
    user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
) -> dict:
    """
    Dependency to require host or admin role.
    
    Args:
        user: Current authenticated user
        db: Database session
        
    Returns:
        User dictionary (host or admin user)
        
    Raises:
        HTTPException: If user is not host or admin
    """
    if not user or not (user.get('is_host', False) or user.get('is_admin', False)):
        raise HTTPException(
            status_code=403,
            detail="Host or admin privileges required"
        )
    
    return user


def require_attendee(
    user: dict = Depends(require_auth),
    db: Session = Depends(get_db)
) -> dict:
    """
    Dependency to require attendee role.
    
    Args:
        user: Current authenticated user
        db: Database session
        
    Returns:
        User dictionary (attendee user)
        
    Raises:
        HTTPException: If user is not attendee
    """
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
    try:
        return get_current_user_with_roles(request, db)
    except HTTPException:
        return None


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
        user: dict = Depends(require_auth)
    ) -> dict:
        if user['id'] != user_id and not user.get('is_admin', False):
            raise HTTPException(
                status_code=403,
                detail="Access denied: can only access own data or admin required"
            )
        return user
    
    return _require_self_or_admin