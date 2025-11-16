# Admin Login Flow - Backend Perspective

## Overview
The admin login flow supports two authentication methods:
1. **OAuth (Google)** - Primary method
2. **Password-based** - Fallback method

Both methods use **JWT tokens** stored in HTTP-only cookies for session management.

---

## Flow Diagram

```
User → /admin → Check Auth → Not Authenticated → /admin/login
                                              ↓
                    ┌────────────────────────┴────────────────────────┐
                    │                                                 │
            OAuth Login                                    Password Login
                    │                                                 │
                    ↓                                                 ↓
        /auth/login?admin=true                    /auth/login/password (POST)
                    │                                                 │
                    ↓                                                 ↓
        Google OAuth Flow                          Verify Password
                    │                                                 │
                    ↓                                                 ↓
        /auth/callback                              Create JWT Token
                    │                                                 │
                    └─────────────────┬───────────────────────────────┘
                                      ↓
                            Set JWT Cookie (access-token)
                                      ↓
                            Redirect to /admin
                                      ↓
                            Check Admin Status
                                      ↓
                            Serve admin.html
```

---

## Detailed Flow

### 1. Initial Access to Admin Interface

**Endpoint:** `GET /admin`

**Code Location:** `api/routes/admin.py:16-46`

**Flow:**
1. User navigates to `/admin`
2. Backend calls `get_current_user(request)` from `auth_manager.py`
3. `get_current_user()` extracts JWT token from cookie (`access-token`)
4. If no token or invalid token:
   - Redirects to `/admin/login` (status 302)
5. If token is valid:
   - Calls `load_user(user_id)` to fetch user from database
   - `load_user()` calls `get_user_with_roles(db, user_id)` to get user with role info
   - Checks `user.get('is_admin', False)`
   - If not admin: Redirects to `/access-denied`
   - If admin: Serves `static/admin.html`

**Key Code:**
```python
@router.get("")
async def admin_interface(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)  # Validates JWT token
    if not user:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    if not user.get('is_admin', False):
        return RedirectResponse(url="/access-denied", status_code=302)
    
    # Serve admin.html
```

---

### 2. OAuth Login Flow

**Entry Point:** `GET /admin/login` → User clicks "Sign in with Google" → `GET /auth/login?admin=true`

**Code Locations:**
- `api/routes/admin.py:49-332` - Login page HTML
- `api/routes/auth_routes.py:24-27` - Login endpoint
- `oauth.py:91-149` - OAuth initiation
- `oauth.py:151-234` - OAuth callback

#### Step 2a: Initiate OAuth

**Endpoint:** `GET /auth/login?admin=true`

**Flow:**
1. `oauth_login()` checks if OAuth is configured
2. Stores return URL in session: `request.session['oauth_return_url'] = f"{BASE_URL}/admin"`
3. Redirects to Google OAuth authorization page
4. User authenticates with Google

**Key Code:**
```python
if admin_flag == 'true':
    request.session['oauth_return_url'] = f"{BASE_URL}/admin"
    
return await oauth.google.authorize_redirect(request, redirect_uri)
```

#### Step 2b: OAuth Callback

**Endpoint:** `GET /auth/callback` (handled by OAuth middleware)

**Flow:**
1. Google redirects back with authorization code
2. `oauth_callback()` exchanges code for access token
3. Fetches user info from Google (email, name)
4. **Database Lookup/Creation:**
   - Queries `Users` table by email
   - If user doesn't exist: Creates new user automatically
   - Gets user ID
5. **JWT Token Creation:**
   - Calls `create_access_token(user_id)` from `auth_manager.py`
   - Creates JWT with 24-hour expiration
   - Token contains: `{"sub": user_id}`
6. **Set Cookie:**
   - Sets HTTP-only cookie: `access-token = <JWT>`
   - Cookie settings:
     - `httponly=True` (JavaScript can't access)
     - `secure=True` (HTTPS only)
     - `samesite="none"` (Cross-site allowed)
     - `max_age=86400` (24 hours)
7. **Redirect:**
   - Redirects to stored return URL: `/admin`

**Key Code:**
```python
# Find or create user
existing_user = db.query(Users).filter(Users.email == user_info['email']).first()
if not existing_user:
    # Auto-create user
    new_user = Users(id=new_user_id, email=..., name=...)
    db.add(new_user)
    db.commit()

# Create JWT token
access_token = create_access_token(user_id)

# Set cookie and redirect
response = RedirectResponse(url=return_url)
response.set_cookie(
    key=manager.cookie_name,  # "access-token"
    value=access_token,
    httponly=True,
    secure=True,
    samesite="none",
    max_age=24 * 60 * 60
)
```

---

### 3. Password Login Flow

**Entry Point:** `GET /admin/login` → User clicks "Sign in with Password" → `POST /auth/login/password`

**Code Location:** `api/routes/auth_routes.py:30-109`

**Flow:**
1. User submits email/password via form
2. **Password Verification:**
   - Queries `Users` table by email
   - Checks if user is OAuth-only (if yes, rejects)
   - Verifies password using `verify_password(password, user.password_hash, user.salt)`
3. **JWT Token Creation:**
   - Calls `create_access_token(user.id)`
   - Creates JWT with 24-hour expiration
4. **Set Cookie:**
   - Same cookie settings as OAuth flow
5. **Response:**
   - Returns JSON: `{"success": True, "redirect": "/admin"}`
   - Frontend JavaScript redirects to `/admin`

**Key Code:**
```python
# Verify password
if not verify_password(login_data.password, user.password_hash, user.salt):
    raise HTTPException(status_code=401, detail="Invalid email or password")

# Create JWT token
access_token = create_access_token(user.id)

# Set cookie
response.set_cookie(
    key=manager.cookie_name,
    value=access_token,
    httponly=True,
    secure=True,
    samesite="none",
    max_age=24 * 60 * 60
)
```

---

### 4. JWT Token Validation

**Code Location:** `auth_manager.py:78-98`

**Flow:**
1. `get_current_user(request)` is called
2. Extracts JWT from cookie: `request.cookies.get("access-token")`
3. **Token Validation:**
   - Uses `fastapi-login` manager to validate token
   - Verifies signature using `JWT_SECRET`
   - Checks expiration
4. **User Loading:**
   - Extracts `user_id` from token payload (`sub` field)
   - Calls `load_user(user_id)` async function
   - `load_user()` queries database and calls `get_user_with_roles(db, user_id)`
   - Returns user dict with roles: `{"id": ..., "email": ..., "is_admin": ..., "is_host": ..., "is_attendee": ...}`
5. Returns user dict or `None` if invalid/expired

**Key Code:**
```python
def get_current_user(request: Request) -> Optional[dict]:
    try:
        # fastapi-login validates token and calls load_user()
        user = manager(request)
        return user
    except Exception as e:
        return None

@manager.user_loader()
async def load_user(user_id: str) -> Optional[dict]:
    db = next(get_db())
    try:
        user_with_roles = get_user_with_roles(db, user_id)
        return user_with_roles  # Includes is_admin, is_host, is_attendee
    finally:
        db.close()
```

---

### 5. Admin Role Check

**Code Location:** `utils/roles.py` (get_user_with_roles function)

**Flow:**
1. `get_user_with_roles()` queries:
   - `Users` table for basic info
   - `Admins` table to check if user is admin
   - `Hosts` table to check if user is host
   - `Attendees` table to check if user is attendee
2. Returns dict with boolean flags:
   ```python
   {
       "id": user.id,
       "email": user.email,
       "name": user.name,
       "is_admin": bool(admin_record),
       "is_host": bool(host_record),
       "is_attendee": bool(attendee_record),
       "roles": ["admin", "host", "attendee"]  # List of roles
   }
   ```
3. Admin check in `/admin` endpoint:
   ```python
   if not user.get('is_admin', False):
       return RedirectResponse(url="/access-denied", status_code=302)
   ```

---

## Security Features

1. **JWT Tokens:**
   - Signed with `SECRET_KEY` from environment
   - 24-hour expiration
   - Stored in HTTP-only cookies (XSS protection)

2. **Cookie Security:**
   - `httponly=True` - JavaScript cannot access
   - `secure=True` - Only sent over HTTPS
   - `samesite="none"` - Allows cross-site (for Flutter app)

3. **Password Security:**
   - Passwords hashed with salt (stored in `password_hash` and `salt` columns)
   - OAuth-only users cannot use password login

4. **Role-Based Access:**
   - Admin status checked on every `/admin` access
   - Database query ensures current role status

---

## Key Components

### Files Involved:
- `api/routes/admin.py` - Admin interface and login page
- `api/routes/auth_routes.py` - Auth endpoints
- `oauth.py` - OAuth flow implementation
- `auth_manager.py` - JWT token management
- `utils/roles.py` - Role checking logic

### Database Tables:
- `users` - User accounts
- `admins` - Admin role assignments
- `hosts` - Host role assignments
- `attendees` - Attendee role assignments

### Environment Variables:
- `GOOGLE_CLIENT_ID` - OAuth client ID
- `GOOGLE_CLIENT_SECRET` - OAuth client secret
- `SECRET_KEY` - JWT signing secret
- `BASE_URL` - Application base URL

---

## Common Issues & Debugging

### Issue: "Redirect loop" or "Not authenticated"
**Cause:** JWT token missing, expired, or invalid
**Debug:** Check `/admin/debug` endpoint to see token status

### Issue: "Access denied" after login
**Cause:** User doesn't have admin role in `admins` table
**Fix:** Add user to `admins` table or use `add_admin_role()` function

### Issue: OAuth callback fails
**Cause:** State mismatch, CSRF token issue, or OAuth not configured
**Debug:** Check logs for OAuth errors, verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set

---

## Summary

The admin login flow uses **JWT-based authentication** with two entry points (OAuth and password). Both methods:
1. Authenticate the user
2. Create a JWT token with user ID
3. Set an HTTP-only cookie
4. Redirect to `/admin`
5. `/admin` endpoint validates JWT and checks admin role
6. Serves admin interface if authorized

The entire flow is stateless (no server-side sessions) except for OAuth state management during the OAuth flow itself.

