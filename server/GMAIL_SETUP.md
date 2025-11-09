# Gmail API Setup for Acro Planner

This guide explains how to set up Gmail API for sending password reset emails.

## Option 1: Service Account (Recommended for Production)

### 1. Create a Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project: `acro-session-planner`
3. Navigate to "IAM & Admin" → "Service Accounts"
4. Click "Create Service Account"
5. Name: `gmail-sender-service`
6. Description: `Service account for sending emails via Gmail API`
7. Click "Create and Continue"

### 2. Enable Gmail API

1. Go to "APIs & Services" → "Library"
2. Search for "Gmail API"
3. Click "Enable"

### 3. Create Service Account Key

1. Go back to "IAM & Admin" → "Service Accounts"
2. Click on your service account
3. Go to "Keys" tab
4. Click "Add Key" → "Create New Key"
5. Select "JSON"
6. Download the JSON file

### 4. Set up Domain-Wide Delegation (if using Google Workspace)

1. In Service Account details, check "Enable Google Workspace Domain-wide Delegation"
2. Go to Google Workspace Admin Console
3. Navigate to Security → API Controls → Domain-wide Delegation
4. Add your service account with Gmail API scope: `https://www.googleapis.com/auth/gmail.send`

### 5. Environment Variables

Set these environment variables in your Cloud Run deployment:

```bash
GMAIL_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'  # Full JSON content
GMAIL_SENDER_EMAIL='noreply@yourdomain.com'  # Must be a verified sender
```

## Option 2: OAuth2 (For Development/Testing)

### 1. Create OAuth2 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to "APIs & Services" → "Credentials"
3. Click "Create Credentials" → "OAuth client ID"
4. Application type: "Desktop application"
5. Name: `acro-planner-gmail`
6. Download the JSON file

### 2. Environment Variables

```bash
GMAIL_CREDENTIALS_PATH='/path/to/credentials.json'
GMAIL_TOKEN_PATH='/tmp/gmail_token.json'  # Will be created automatically
GMAIL_SENDER_EMAIL='your-email@gmail.com'
```

### 3. First-time Setup

The first time you run the application, it will open a browser for OAuth authorization. This creates a token file for future use.

## Option 3: App Passwords (Simple but Less Secure)

If you want to keep using SMTP with Gmail:

1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. Use these environment variables:

```bash
SMTP_USERNAME='your-email@gmail.com'
SMTP_PASSWORD='your-app-password'  # 16-character app password
SMTP_SERVER='smtp.gmail.com'
SMTP_PORT='587'
FROM_EMAIL='your-email@gmail.com'
```

## Testing

Test the email functionality by calling the forgot password endpoint:

```bash
curl -X POST "https://your-app.run.app/auth/forgot-password" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

## Troubleshooting

### Common Issues

1. **"Gmail credentials not found"**
   - Ensure `GMAIL_SERVICE_ACCOUNT_JSON` or `GMAIL_CREDENTIALS_PATH` is set
   - Verify the JSON format is valid

2. **"Authentication failed"**
   - Check if Gmail API is enabled in Google Cloud Console
   - Verify service account permissions
   - For domain-wide delegation, ensure proper setup in Google Workspace Admin

3. **"Invalid sender"**
   - For service accounts, the sender email must be authorized
   - For personal Gmail, use the authenticated user's email

### Logs

Check Cloud Run logs for detailed error messages:

```bash
gcloud run services logs read acro-planner-backend --region=us-central1
```

## Security Notes

- Store credentials securely as environment variables
- Use service accounts for production
- Regularly rotate service account keys
- Limit API scopes to minimum required (`gmail.send` only)
- Monitor API usage in Google Cloud Console