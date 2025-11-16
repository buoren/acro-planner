"""
Authentication and authorization API endpoints.
"""

import os
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from models import Users
from utils.auth import verify_password, hash_password
from auth_manager import get_current_user, create_access_token, manager
from oauth import oauth_login, oauth_callback, logout_user, is_oauth_configured
from api.schemas import ForgotPasswordRequest, ForgotPasswordResponse, ResetPasswordRequest, ResetPasswordResponse
from utils.password_reset import create_reset_token, send_reset_email, verify_reset_token, use_reset_token
from utils.system_settings import get_frontend_url
from utils.roles import add_admin_role
import logging

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login(request: Request):
    """Initiate OAuth login"""
    return await oauth_login(request)


@router.post("/login/password")
async def password_login(request: Request):
    """Handle password-based login"""
    try:
        from pydantic import BaseModel

        class LoginRequest(BaseModel):
            email: str
            password: str

        # Parse request body
        body = await request.json()
        login_data = LoginRequest(**body)

        # Check if database is available
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise HTTPException(status_code=503, detail="Database not available")

        # Authenticate user
        from database import get_db
        from models import Users
        from utils.auth import verify_password

        # Get database session
        db_gen = get_db()
        db: Session = next(db_gen)

        try:
            # Find user by email
            user = db.query(Users).filter(Users.email == login_data.email).first()

            if not user:
                raise HTTPException(status_code=401, detail="Invalid email or password")
            
            # Check if user is OAuth-only
            if user.oauth_only:
                raise HTTPException(
                    status_code=401, 
                    detail="This account uses OAuth login only. Please use the 'Login with Google' button."
                )

            # Verify password
            if not verify_password(login_data.password, user.password_hash, user.salt):
                raise HTTPException(status_code=401, detail="Invalid email or password")

            # Create JWT token
            from auth_manager import create_access_token, manager
            access_token = create_access_token(user.id)
            
            # Debug logging
            print(f"PASSWORD_LOGIN: Created JWT token for user {user.email}")
            print(f"PASSWORD_LOGIN: User ID: {user.id}")

            # Create JSON response with JWT cookie
            response = JSONResponse({
                "success": True, 
                "message": "Login successful", 
                "redirect": "/admin"
            })
            
            # Set JWT token as HTTP-only cookie
            response.set_cookie(
                key=manager.cookie_name,
                value=access_token,
                httponly=True,
                secure=True,  # HTTPS only
                samesite="lax",  # Changed from "none" to "lax" for better compatibility
                max_age=24 * 60 * 60,  # 24 hours
                path="/",  # Explicitly set path
                domain=None  # Let browser determine domain automatically
            )
            
            return response

        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.get("/callback")
async def auth_callback(request: Request):
    """Handle OAuth callback"""
    return await oauth_callback(request)


@router.get("/logout")
async def logout_get(request: Request):
    """Logout user via GET"""
    return logout_user(request)

@router.post("/logout")
async def logout_post(request: Request):
    """Logout user via POST"""
    return logout_user(request)


@router.get("/me")
async def get_me(request: Request):
    """Get current user info"""
    user = await get_current_user(request)
    if user:
        return {"user": user, "authenticated": True}
    return {"user": None, "authenticated": False}


@router.get("/status")
async def auth_status():
    """Check OAuth configuration status"""
    return {
        "oauth_configured": is_oauth_configured(),
        "message": "OAuth is configured" if is_oauth_configured() else "OAuth not configured - set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"
    }


@router.post("/forgot-password")
async def forgot_password(request_data: dict, db: Session = Depends(get_db)):
    """
    Send password reset email to user.
    
    Request body should contain:
    - email: User's email address
    """
    try:
        # Validate request data
        request_obj = ForgotPasswordRequest(**request_data)
        
        # Find user by email
        user = db.query(Users).filter(Users.email == request_obj.email).first()
        
        if user and not user.oauth_only:
            # Create reset token
            reset_token = create_reset_token(db, user.id)
            
            # Use backend redirect URL instead of frontend URL directly
            base_url = os.getenv("BASE_URL", "https://acro-planner-backend-733697808355.us-central1.run.app")
            
            # Send reset email with backend redirect URL
            email_sent = send_reset_email(user.email, reset_token, base_url)
            
            if email_sent:
                return ForgotPasswordResponse(
                    success=True,
                    message="Password reset email sent successfully. Please check your email."
                )
            else:
                return ForgotPasswordResponse(
                    success=False,
                    message="Failed to send email. Please try again later."
                )
        else:
            # Always return success for security (don't reveal if email exists)
            # But OAuth-only users can't reset password this way
            return ForgotPasswordResponse(
                success=True,
                message="If the email exists and has a password, a reset link has been sent."
            )
            
    except Exception as e:
        print(f"Forgot password error: {e}")
        return ForgotPasswordResponse(
            success=False,
            message="An error occurred. Please try again later."
        )


@router.post("/reset-password")
async def reset_password(request_data: dict, db: Session = Depends(get_db)):
    """
    Reset user password using reset token.
    
    Request body should contain:
    - token: Password reset token
    - new_password: New password
    - confirm_password: Password confirmation
    """
    try:
        # Validate request data
        request_obj = ResetPasswordRequest(**request_data)
        
        # Verify token
        user_id = verify_reset_token(db, request_obj.token)
        
        if not user_id:
            return ResetPasswordResponse(
                success=False,
                message="Invalid or expired reset token."
            )
        
        # Get user
        user = db.query(Users).filter(Users.id == user_id).first()
        
        if not user or user.oauth_only:
            return ResetPasswordResponse(
                success=False,
                message="User not found or cannot reset password."
            )
        
        # Hash new password
        password_hash, salt = hash_password(request_obj.new_password)
        
        # Update user password
        user.password_hash = password_hash
        user.salt = salt
        db.commit()
        
        # Mark token as used
        use_reset_token(db, request_obj.token)
        
        return ResetPasswordResponse(
            success=True,
            message="Password reset successfully. You can now login with your new password."
        )
        
    except Exception as e:
        print(f"Reset password error: {e}")
        return ResetPasswordResponse(
            success=False,
            message="An error occurred. Please try again later."
        )


@router.get("/password-reset-redirect")
async def reset_password_redirect(token: str, request: Request, db: Session = Depends(get_db)):
    """
    Redirect endpoint for password reset links.
    
    This endpoint receives the reset token from email links and redirects 
    to the frontend with the token as a query parameter.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Password reset redirect called with token: {token[:10]}...")
    
    # Get frontend URL from database settings
    frontend_url = get_frontend_url(db)
    
    # Construct the frontend reset password URL with the token
    # Use query parameter instead of fragment to avoid browser redirect issues
    redirect_url = f"{frontend_url}#/reset-password?token={token}"
    
    logger.info(f"Redirecting to: {redirect_url}")
    
    # Return redirect response with explicit headers to prevent middleware interference
    response = RedirectResponse(url=redirect_url, status_code=302)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["Location"] = redirect_url
    
    return response


@router.post("/promote-to-admin")
async def promote_current_user_to_admin(request: Request):
    """Promote current user to admin (temporary endpoint for initial setup)"""
    from oauth import get_current_user
    
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_id = user.get('sub')
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user session")
    
    # Get database session
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        # Add admin role
        add_admin_role(db, user_id)
        return {"success": True, "message": "User promoted to admin successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to promote user: {str(e)}")
    finally:
        db.close()

