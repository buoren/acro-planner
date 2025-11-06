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
    print(f"[AUTH_DEBUG] get_current_user_with_roles called for path: {request.url.path}")
    print(f"[AUTH_DEBUG] Request method: {request.method}")
    print(f"[AUTH_DEBUG] Request headers: {dict(request.headers)}")
    
    try:
        user = get_current_user(request)
        print(f"[AUTH_DEBUG] get_current_user returned: {user}")
        
        if not user:
            print(f"[AUTH_DEBUG] No user found, raising 401")
            raise HTTPException(
                status_code=401,
                detail="Authentication required"
            )
    except Exception as e:
        print(f"[AUTH_DEBUG] Exception in get_current_user: {type(e).__name__}: {str(e)}")
        raise
    
    # Get user with role information
    user_id = user.get('sub')
    print(f"[AUTH_DEBUG] Extracted user_id: {user_id}")
    
    if not user_id:
        print(f"[AUTH_DEBUG] No user_id in session, raising 401")
        raise HTTPException(
            status_code=401,
            detail="Invalid user session"
        )
    
    # First try lookup by user_id (for existing OAuth users)
    user_with_roles = get_user_with_roles(db, user_id)
    print(f"[AUTH_DEBUG] get_user_with_roles by ID returned: {user_with_roles}")
    
    if not user_with_roles:
        # Try lookup by email (for existing users who might have signed up with email)
        from models import Users
        email = user.get('email')
        print(f"[AUTH_DEBUG] Trying lookup by email: {email}")
        
        db_user = db.query(Users).filter(Users.email == email).first()
        if db_user:
            print(f"[AUTH_DEBUG] Found existing user by email: {db_user.id}")
            # User exists with email - return their data using their existing ID
            # This allows admin users to log in with OAuth using their email
            existing_user_id = db_user.id
            user_with_roles = get_user_with_roles(db, existing_user_id)
            
            # Update the session to use the existing user's database ID instead of OAuth sub
            # This way existing users can use OAuth login
            user_with_roles['oauth_sub'] = user_id  # Store OAuth sub for reference
            user_with_roles['auth_method'] = 'oauth'
            print(f"[AUTH_DEBUG] Using existing user {existing_user_id}, roles: {user_with_roles}")
        else:
            print(f"[AUTH_DEBUG] No user found by email either, auto-creating OAuth user")
            # Auto-create OAuth user (for Flutter app)
            from utils.roles import add_attendee_role
            import datetime
            
            try:
                # Create new OAuth user
                new_user = Users(
                    id=user_id,  # Use OAuth sub as user ID
                    email=user.get('email'),
                    name=user.get('name'),
                    password_hash=None,  # OAuth users don't have passwords
                    salt=None,
                    oauth_only=True,  # Mark as OAuth-only user
                    created_at=datetime.datetime.utcnow(),
                    updated_at=datetime.datetime.utcnow()
                )
                
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                
                print(f"[AUTH_DEBUG] Created OAuth user {user_id} in database")
                
                # Add default attendee role
                try:
                    add_attendee_role(db, user_id)
                    print(f"[AUTH_DEBUG] Added attendee role to OAuth user {user_id}")
                except Exception as e:
                    print(f"[AUTH_DEBUG] Failed to add attendee role: {e}")
                    # Continue anyway
                
                # Now get user with roles
                user_with_roles = get_user_with_roles(db, user_id)
                print(f"[AUTH_DEBUG] After creation, get_user_with_roles returned: {user_with_roles}")
                
            except Exception as e:
                print(f"[AUTH_DEBUG] Failed to create OAuth user: {type(e).__name__}: {str(e)}")
                db.rollback()
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create user account"
                )
    
    if not user_with_roles:
        print(f"[AUTH_DEBUG] Still no user_with_roles after all attempts")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user information"
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
    print(f"[AUTH_DEBUG] require_admin called, user received: {user}")
    print(f"[AUTH_DEBUG] User is_admin: {user.get('is_admin', False) if user else 'No user'}")
    
    if not user or not user.get('is_admin', False):
        print(f"[AUTH_DEBUG] Admin check failed, raising 403")
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    
    print(f"[AUTH_DEBUG] Admin check passed, returning user")
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