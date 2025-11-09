"""
Password reset utilities for forgot password functionality.
"""

import secrets
import smtplib
import uuid
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import os
from sqlalchemy.orm import Session
from models import PasswordResetToken, Users


def generate_reset_token() -> str:
    """Generate a secure random token for password reset."""
    return secrets.token_urlsafe(32)


def create_reset_token(db: Session, user_id: str, expires_hours: int = 24) -> str:
    """
    Create a password reset token for a user.
    
    Args:
        db: Database session
        user_id: User ID to create token for
        expires_hours: Token expiration time in hours
        
    Returns:
        Reset token string
    """
    # Deactivate any existing tokens for this user
    existing_tokens = db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user_id,
        PasswordResetToken.used == False
    ).all()
    
    for token in existing_tokens:
        token.used = True
    
    # Create new token
    reset_token = generate_reset_token()
    expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
    
    token_record = PasswordResetToken(
        id=str(uuid.uuid4()),
        user_id=user_id,
        token=reset_token,
        expires_at=expires_at,
        used=False
    )
    
    db.add(token_record)
    db.commit()
    db.refresh(token_record)
    
    return reset_token


def verify_reset_token(db: Session, token: str) -> Optional[str]:
    """
    Verify a password reset token and return the user ID if valid.
    
    Args:
        db: Database session
        token: Reset token to verify
        
    Returns:
        User ID if token is valid, None otherwise
    """
    token_record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token,
        PasswordResetToken.used == False,
        PasswordResetToken.expires_at > datetime.utcnow()
    ).first()
    
    if token_record:
        return token_record.user_id
    return None


def use_reset_token(db: Session, token: str) -> bool:
    """
    Mark a password reset token as used.
    
    Args:
        db: Database session
        token: Reset token to mark as used
        
    Returns:
        True if token was successfully marked as used, False otherwise
    """
    token_record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == token,
        PasswordResetToken.used == False,
        PasswordResetToken.expires_at > datetime.utcnow()
    ).first()
    
    if token_record:
        token_record.used = True
        db.commit()
        return True
    return False


def send_reset_email(email: str, reset_token: str, base_url: str) -> bool:
    """
    Send password reset email to user using Gmail API.
    
    Args:
        email: User's email address
        reset_token: Password reset token
        base_url: Base URL for the application
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    try:
        # Try Gmail API first
        from utils.gmail_service import send_reset_email_gmail
        
        gmail_success = send_reset_email_gmail(email, reset_token, base_url)
        if gmail_success:
            return True
        
        print("Gmail API failed, falling back to SMTP...")
        
        # Fall back to SMTP if Gmail API fails
        return _send_reset_email_smtp(email, reset_token, base_url)
        
    except Exception as e:
        print(f"Failed to send reset email: {e}")
        return False


def _send_reset_email_smtp(email: str, reset_token: str, base_url: str) -> bool:
    """
    Send password reset email via SMTP (fallback method).
    
    Args:
        email: User's email address
        reset_token: Password reset token
        base_url: Base URL for the application
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    try:
        # Get email configuration from environment variables
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        from_email = os.getenv('FROM_EMAIL', smtp_username)
        
        if not smtp_username or not smtp_password:
            print("SMTP credentials not configured. Email not sent.")
            return False
        
        # Create reset URL using backend redirect endpoint
        reset_url = f"{base_url}/auth/password-reset-redirect?token={reset_token}"
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = email
        msg['Subject'] = "Password Reset Request - Acro Planner"
        
        # Email body
        body = f"""
        Hello,
        
        You requested a password reset for your Acro Planner account.
        
        Click the link below to reset your password:
        {reset_url}
        
        This link will expire in 24 hours.
        
        If you didn't request this password reset, please ignore this email.
        
        Best regards,
        The Acro Planner Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        text = msg.as_string()
        server.sendmail(from_email, email, text)
        server.quit()
        
        return True
        
    except Exception as e:
        print(f"Failed to send reset email via SMTP: {e}")
        return False