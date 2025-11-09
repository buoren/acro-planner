"""
Gmail API service for sending emails via Google Cloud.
"""

import base64
import os
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']


class GmailService:
    """Gmail API service for sending emails."""
    
    def __init__(self):
        self.service = None
        self.credentials_path = os.getenv('GMAIL_CREDENTIALS_PATH')
        self.token_path = os.getenv('GMAIL_TOKEN_PATH', '/tmp/gmail_token.json')
        
    def authenticate(self) -> bool:
        """Authenticate with Gmail API using OAuth2."""
        try:
            creds = None
            
            # Load existing token
            if os.path.exists(self.token_path):
                with open(self.token_path, 'r') as token:
                    creds_data = json.load(token)
                    creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
            
            # If there are no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not self.credentials_path or not os.path.exists(self.credentials_path):
                        print("Gmail credentials not found. Set GMAIL_CREDENTIALS_PATH environment variable.")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
            
            # Build the Gmail service
            self.service = build('gmail', 'v1', credentials=creds)
            return True
            
        except Exception as e:
            print(f"Gmail authentication failed: {e}")
            return False
    
    def authenticate_with_service_account(self) -> bool:
        """Authenticate using a service account (for production)."""
        try:
            from google.oauth2 import service_account
            
            service_account_info = os.getenv('GMAIL_SERVICE_ACCOUNT_JSON')
            if not service_account_info:
                print("GMAIL_SERVICE_ACCOUNT_JSON environment variable not set.")
                return False
            
            # Parse the service account JSON
            service_account_data = json.loads(service_account_info)
            
            # Create credentials from service account
            credentials = service_account.Credentials.from_service_account_info(
                service_account_data,
                scopes=SCOPES
            )
            
            # For Gmail API, we need to delegate domain-wide authority
            gmail_user = os.getenv('GMAIL_IMPERSONATION_EMAIL')
            if gmail_user:
                credentials = credentials.with_subject(gmail_user)
            
            self.service = build('gmail', 'v1', credentials=credentials)
            return True
            
        except Exception as e:
            print(f"Service account authentication failed: {e}")
            return False
    
    def create_message(self, sender: str, to: str, subject: str, body: str, 
                      body_html: Optional[str] = None) -> dict:
        """Create a message for an email."""
        try:
            if body_html:
                # Create multipart message with both plain text and HTML
                message = MIMEMultipart('alternative')
                message['to'] = to
                message['from'] = sender
                message['subject'] = subject
                
                # Create plain text and HTML parts
                text_part = MIMEText(body, 'plain')
                html_part = MIMEText(body_html, 'html')
                
                message.attach(text_part)
                message.attach(html_part)
            else:
                # Create plain text message
                message = MIMEText(body)
                message['to'] = to
                message['from'] = sender
                message['subject'] = subject
            
            # Encode the message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            return {'raw': raw_message}
        
        except Exception as e:
            print(f"Error creating message: {e}")
            raise
    
    def send_message(self, sender: str, to: str, subject: str, body: str,
                    body_html: Optional[str] = None) -> bool:
        """Send an email message."""
        try:
            # Try service account authentication first (for production)
            if not self.service:
                if not self.authenticate_with_service_account():
                    # Fall back to OAuth2 (for development)
                    if not self.authenticate():
                        return False
            
            # Create and send the message
            message = self.create_message(sender, to, subject, body, body_html)
            result = self.service.users().messages().send(
                userId='me', body=message).execute()
            
            print(f"Email sent successfully. Message ID: {result['id']}")
            return True
            
        except HttpError as e:
            print(f"Gmail API error: {e}")
            return False
        except Exception as e:
            print(f"Error sending email: {e}")
            return False


def send_reset_email_gmail(email: str, reset_token: str, base_url: str) -> bool:
    """
    Send password reset email using Gmail API.
    
    Args:
        email: User's email address
        reset_token: Password reset token
        base_url: Base URL for the application
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    try:
        gmail_service = GmailService()
        
        # Get sender email from environment
        sender_email = os.getenv('GMAIL_SENDER_EMAIL', 'noreply@acroplanner.com')
        
        # Create reset URL using backend redirect endpoint
        reset_url = f"{base_url}/auth/password-reset-redirect?token={reset_token}"
        
        subject = "Password Reset Request - Acro Planner"
        
        # Plain text version
        body_text = f"""
Hello,

You requested a password reset for your Acro Planner account.

Click the link below to reset your password:
{reset_url}

This link will expire in 24 hours.

If you didn't request this password reset, please ignore this email.

Best regards,
The Acro Planner Team
"""
        
        # HTML version
        body_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .button {{ 
            display: inline-block; 
            padding: 12px 24px; 
            background-color: #007bff; 
            color: white; 
            text-decoration: none; 
            border-radius: 5px; 
            margin: 20px 0;
        }}
        .footer {{ margin-top: 30px; font-size: 14px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Password Reset Request</h2>
        </div>
        
        <p>Hello,</p>
        
        <p>You requested a password reset for your Acro Planner account.</p>
        
        <p>Click the button below to reset your password:</p>
        
        <p style="text-align: center;">
            <a href="{reset_url}" class="button">Reset My Password</a>
        </p>
        
        <p>Or copy and paste this link into your browser:</p>
        <p style="word-break: break-all; font-size: 12px;">{reset_url}</p>
        
        <p><strong>This link will expire in 24 hours.</strong></p>
        
        <div class="footer">
            <p>If you didn't request this password reset, please ignore this email.</p>
            <p>Best regards,<br>The Acro Planner Team</p>
        </div>
    </div>
</body>
</html>
"""
        
        return gmail_service.send_message(
            sender=sender_email,
            to=email,
            subject=subject,
            body=body_text.strip(),
            body_html=body_html
        )
        
    except Exception as e:
        print(f"Failed to send reset email via Gmail API: {e}")
        return False