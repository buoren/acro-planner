"""
Admin interface and admin-related API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from database import get_db
from auth_manager import get_current_user
from utils.system_settings import get_frontend_url, set_system_setting

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("")
async def admin_interface(request: Request, db: Session = Depends(get_db)):
    """Serve the protected admin interface"""
    # Check if user is authenticated
    try:
        # Debug: Log all cookies and headers
        print(f"[ADMIN_DEBUG] All cookies received: {dict(request.cookies)}")
        print(f"[ADMIN_DEBUG] Request headers: {dict(request.headers)}")
        print(f"[ADMIN_DEBUG] Request URL: {request.url}")
        
        # Check for specific cookie
        from auth_manager import manager
        cookie_name = manager.cookie_name
        cookie_present = cookie_name in request.cookies
        print(f"[ADMIN_DEBUG] Expected cookie name: '{cookie_name}'")
        print(f"[ADMIN_DEBUG] Cookie '{cookie_name}' present: {cookie_present}")
        
        if cookie_present:
            cookie_value = request.cookies.get(cookie_name, '')
            print(f"[ADMIN_DEBUG] Cookie value length: {len(cookie_value)}")
            print(f"[ADMIN_DEBUG] Cookie value first 50 chars: {cookie_value[:50]}...")
            
            # Test JWT validation manually
            try:
                import jwt
                from auth_manager import JWT_SECRET
                decoded = jwt.decode(cookie_value, JWT_SECRET, algorithms=["HS256"])
                print(f"[ADMIN_DEBUG] JWT validation SUCCESS: {decoded}")
            except Exception as jwt_e:
                print(f"[ADMIN_DEBUG] JWT validation FAILED: {jwt_e}")
        else:
            print(f"[ADMIN_DEBUG] No cookie found - available cookies: {list(request.cookies.keys())}")
        
        user = await get_current_user(request)
        print(f"[ADMIN_DEBUG] get_current_user returned: {user is not None}")
        print(f"[ADMIN_DEBUG] User type: {type(user)}")
        print(f"[ADMIN_DEBUG] User value: {user}")
        
        # Check if user is a coroutine (async issue) and handle it
        if hasattr(user, '__await__'):
            print(f"[ADMIN_DEBUG] User is a coroutine, treating as None")
            user = None
        
        if user:
            try:
                print(f"[ADMIN_DEBUG] User ID: {user.get('id')}, is_admin: {user.get('is_admin')}")
                print(f"[ADMIN_DEBUG] All user fields: {user}")
            except AttributeError as e:
                print(f"[ADMIN_DEBUG] User object error: {e}")
                user = None
        
        if not user:
            # Redirect to login page if not authenticated
            print(f"[ADMIN_DEBUG] No user found, redirecting to login")
            return RedirectResponse(url="/admin/login", status_code=302)
        
        # Check if user is admin
        try:
            is_admin = user.get('is_admin', False) if user else False
        except AttributeError:
            print(f"[ADMIN_DEBUG] User admin check error, treating as not admin")
            is_admin = False
            
        if not is_admin:
            # Redirect to access denied page if not admin
            print(f"[ADMIN_DEBUG] User is not admin, redirecting to access-denied")
            return RedirectResponse(url="/access-denied", status_code=302)
        
        # Read the admin HTML file
        with open('static/admin.html', 'r') as f:
            content = f.read()
        
        # Return with relaxed CSP for admin interface
        return HTMLResponse(
            content=content,
            headers={
                "Content-Security-Policy": "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data: https://lh3.googleusercontent.com; font-src 'self';"
            }
        )
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Admin interface not found")
    except Exception as e:
        # Log the actual error for debugging
        print(f"[ADMIN_DEBUG] Exception in admin_interface: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        # If there's any error with authentication, redirect to login
        return RedirectResponse(url="/admin/login", status_code=302)


@router.get("/login")
async def admin_login(request: Request):
    """Serve the admin login page"""
    login_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin Login - Acro Planner</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .login-container {
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.1);
                width: 90%;
                max-width: 400px;
            }
            h1 {
                color: #333;
                margin-bottom: 10px;
                font-size: 28px;
            }
            .subtitle {
                color: #666;
                margin-bottom: 30px;
                font-size: 14px;
            }
            .login-options {
                display: flex;
                flex-direction: column;
                gap: 15px;
            }
            .login-btn {
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 12px 20px;
                border: 1px solid #ddd;
                border-radius: 5px;
                background: white;
                color: #333;
                text-decoration: none;
                font-size: 16px;
                transition: all 0.3s ease;
                cursor: pointer;
            }
            .login-btn:hover {
                background: #f8f9fa;
                border-color: #999;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }
            .google-btn {
                border-color: #4285f4;
                color: #4285f4;
            }
            .google-btn:hover {
                background: #f1f5fe;
            }
            .password-btn {
                border-color: #28a745;
                color: #28a745;
            }
            .password-btn:hover {
                background: #f0f9f2;
            }
            .divider {
                text-align: center;
                color: #999;
                margin: 20px 0;
                position: relative;
            }
            .divider::before,
            .divider::after {
                content: '';
                position: absolute;
                top: 50%;
                width: 45%;
                height: 1px;
                background: #ddd;
            }
            .divider::before {
                left: 0;
            }
            .divider::after {
                right: 0;
            }
            .back-link {
                text-align: center;
                margin-top: 20px;
            }
            .back-link a {
                color: #667eea;
                text-decoration: none;
                font-size: 14px;
            }
            .back-link a:hover {
                text-decoration: underline;
            }
            .error-message {
                background: #f8d7da;
                color: #721c24;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 20px;
                display: none;
            }
            .password-form {
                margin-top: 15px;
                display: flex;
                flex-direction: column;
                gap: 15px;
                padding: 20px;
                border: 1px solid #ddd;
                border-radius: 5px;
                background: #f9f9f9;
            }
            .form-input {
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 16px;
                outline: none;
            }
            .form-input:focus {
                border-color: #28a745;
                box-shadow: 0 0 5px rgba(40, 167, 69, 0.3);
            }
            .submit-btn {
                background: #28a745;
                color: white;
                border-color: #28a745;
            }
            .submit-btn:hover {
                background: #218838;
                border-color: #1e7e34;
            }
            .cancel-btn {
                background: #dc3545;
                color: white;
                border-color: #dc3545;
            }
            .cancel-btn:hover {
                background: #c82333;
                border-color: #bd2130;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <h1>Admin Login</h1>
            <p class="subtitle">Sign in to access the admin dashboard</p>
            
            <div id="error-message" class="error-message"></div>
            
            <div class="login-options">
                <a href="/auth/login?admin=true" class="login-btn google-btn">
                    <svg width="20" height="20" viewBox="0 0 20 20" style="margin-right: 10px;">
                        <path d="M19.6 10.23c0-.82-.1-1.42-.25-2.05H10v3.72h5.5c-.15.96-.74 2.31-2.04 3.22v2.45h3.16c1.89-1.73 2.98-4.3 2.98-7.34z" fill="#4285f4"/>
                        <path d="M13.46 15.13c-.83.59-1.96 1-3.46 1-2.64 0-4.88-1.74-5.68-4.15H1.07v2.52C2.72 17.75 6.09 20 10 20c2.7 0 4.96-.89 6.62-2.42l-3.16-2.45z" fill="#34a853"/>
                        <path d="M3.99 10c0-.69.12-1.35.32-1.97V5.51H1.07A9.973 9.973 0 000 10c0 1.61.39 3.14 1.07 4.49l3.24-2.52c-.2-.62-.32-1.28-.32-1.97z" fill="#fbbc04"/>
                        <path d="M10 3.88c1.48 0 2.79.51 3.83 1.51l2.84-2.84C14.96.99 12.7 0 10 0 6.09 0 2.72 2.25 1.07 5.51l3.24 2.52C5.12 5.62 7.36 3.88 10 3.88z" fill="#ea4335"/>
                    </svg>
                    Sign in with Google
                </a>
                
                <div class="divider">OR</div>
                
                <button onclick="togglePasswordLogin()" class="login-btn password-btn" id="password-login-btn">
                    <svg width="20" height="20" viewBox="0 0 20 20" style="margin-right: 10px;">
                        <path d="M10 2a4 4 0 00-4 4v3H4a1 1 0 00-1 1v7a1 1 0 001 1h12a1 1 0 001-1v-7a1 1 0 00-1-1h-2V6a4 4 0 00-4-4zm2 7V6a2 2 0 10-4 0v3h4z" fill="currentColor"/>
                    </svg>
                    Sign in with Password
                </button>
                
                <div id="password-form" class="password-form" style="display: none;">
                    <input type="email" id="email" placeholder="Email" class="form-input" required>
                    <input type="password" id="password" placeholder="Password" class="form-input" required>
                    <button onclick="submitPasswordLogin()" class="login-btn submit-btn">
                        Sign In
                    </button>
                    <button onclick="togglePasswordLogin()" class="login-btn cancel-btn">
                        Cancel
                    </button>
                </div>
            </div>
            
            <div class="back-link">
                <a href="/app">← Back to App</a>
            </div>
        </div>
        
        <script>
            function togglePasswordLogin() {
                const passwordForm = document.getElementById('password-form');
                const passwordBtn = document.getElementById('password-login-btn');
                
                if (passwordForm.style.display === 'none') {
                    passwordForm.style.display = 'block';
                    passwordBtn.innerHTML = '<svg width="20" height="20" viewBox="0 0 20 20" style="margin-right: 10px;"><path d="M6 10l3 3l6-6" stroke="currentColor" stroke-width="2" fill="none"/></svg>Hide Password Form';
                } else {
                    passwordForm.style.display = 'none';
                    passwordBtn.innerHTML = '<svg width="20" height="20" viewBox="0 0 20 20" style="margin-right: 10px;"><path d="M10 2a4 4 0 00-4 4v3H4a1 1 0 00-1 1v7a1 1 0 001 1h12a1 1 0 001-1v-7a1 1 0 00-1-1h-2V6a4 4 0 00-4-4zm2 7V6a2 2 0 10-4 0v3h4z" fill="currentColor"/></svg>Sign in with Password';
                }
            }
            
            async function submitPasswordLogin() {
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;
                const errorDiv = document.getElementById('error-message');
                
                if (!email || !password) {
                    showError('Please enter both email and password');
                    return;
                }
                
                try {
                    const response = await fetch('/auth/login/password', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        credentials: 'include',
                        body: JSON.stringify({ email, password })
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok && result.success) {
                        // Login successful, redirect to admin
                        window.location.href = '/admin';
                    } else {
                        showError(result.detail || result.message || 'Login failed');
                    }
                } catch (error) {
                    showError('Login failed: ' + error.message);
                }
            }
            
            function showError(message) {
                const errorDiv = document.getElementById('error-message');
                errorDiv.textContent = message;
                errorDiv.style.display = 'block';
            }
            
            // Check for error in URL params
            const urlParams = new URLSearchParams(window.location.search);
            const error = urlParams.get('error');
            if (error) {
                showError(decodeURIComponent(error));
            }
            
            // Allow Enter key to submit form
            document.addEventListener('keypress', function(event) {
                if (event.key === 'Enter' && document.getElementById('password-form').style.display !== 'none') {
                    submitPasswordLogin();
                }
            });
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(
        content=login_html,
        headers={
            "Content-Security-Policy": "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data:;"
        }
    )


@router.get("/debug")
async def admin_debug(request: Request, db: Session = Depends(get_db)):
    """Debug endpoint to check authentication status."""
    debug_info = {
        "cookies": dict(request.cookies),
        "headers": dict(request.headers)
    }
    
    try:
        # Try to get user with detailed error tracking
        user = await get_current_user(request)
        debug_info.update({
            "authenticated": user is not None,
            "user": dict(user) if user else None,  # Convert to dict to avoid serialization issues
            "jwt_validation": "success"
        })
    except Exception as e:
        debug_info.update({
            "error": str(e),
            "error_type": type(e).__name__,
            "authenticated": False,
            "jwt_validation": "failed"
        })
    
    # Additional JWT debugging
    access_token = request.cookies.get("access-token")
    if access_token:
        try:
            import jwt
            
            # Try to decode without verification to see token structure
            unverified = jwt.decode(access_token, options={"verify_signature": False})
            debug_info["jwt_payload_unverified"] = unverified
            
            # Try with verification using current secret
            from auth_manager import JWT_SECRET
            verified = jwt.decode(access_token, JWT_SECRET, algorithms=["HS256"])
            debug_info["jwt_payload_verified"] = verified
            debug_info["jwt_secret_match"] = True
            
        except jwt.ExpiredSignatureError:
            debug_info["jwt_error"] = "Token expired"
        except jwt.InvalidTokenError as e:
            debug_info["jwt_error"] = f"Invalid token: {str(e)}"
        except Exception as e:
            debug_info["jwt_debug_error"] = str(e)
    else:
        debug_info["jwt_cookie_present"] = False
    
    return debug_info

@router.get("/current-frontend-url")
async def get_current_frontend_url(db: Session = Depends(get_db)):
    """Get the current frontend URL from system settings."""
    try:
        frontend_url = get_frontend_url(db)
        return {
            "success": True,
            "frontend_url": frontend_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get frontend URL: {str(e)}")