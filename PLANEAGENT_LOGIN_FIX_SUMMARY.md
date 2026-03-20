# PlaneAgent Login Loop Bug Fix - Summary

## Problem Description
The PlaneAgent application in CT 920 was stuck in an infinite login loop:
1. Backend authentication worked correctly
2. Session cookie was set by the server
3. BUT browser did NOT send `session-id` cookie on subsequent API calls to `/api/users/me/`
4. Frontend received 401 Unauthorized, redirected to login
5. React hydration mismatch occurred (server rendered login, client expected auth view)

## Root Cause
**Cross-Origin Cookie Blocking**: The frontend was served on port 80 (nginx) while the Django API was on port 8000. Browsers treat different ports as different origins for cookie purposes, even on the same IP address.

Django's default session cookie settings:
- `SESSION_COOKIE_SAMESITE` was not set (defaulted to `'Lax'`)
- With `SameSite=Lax`, browsers won't send cookies in cross-origin requests
- The API calls from port 80 to port 8000 were treated as cross-origin

## Solution Applied

### Code Changes (3 commits)

#### 1. `130fcf5f82` - Core Fix: SameSite=None for Cookies
**File**: `apps/api/plane/settings/common.py`

Added explicit SameSite settings for cross-origin cookie support:
```python
# PLANEAGENT FIX: Set SameSite=None for cross-origin requests (frontend:80 <-> api:8000)
SESSION_COOKIE_SAMESITE = os.environ.get("SESSION_COOKIE_SAMESITE", "None")
CSRF_COOKIE_SAMESITE = os.environ.get("CSRF_COOKIE_SAMESITE", "None")
```

#### 2. `a67491933c` - Documentation: Environment Configuration
**File**: `.env.planeagent.example`

Created comprehensive environment variable documentation explaining:
- Cross-origin cookie settings
- Alternative nginx proxy approach (recommended for production)
- Database, Redis, and security configurations

#### 3. `29a68d306a` - Deployment: Nginx Config and Script
**Files**:
- `deployments/nginx/planeagent.conf` - Production nginx configuration
- `deployments/scripts/deploy-ct920.sh` - Automated deployment script

The nginx configuration provides a cleaner solution by:
- Serving React frontend on port 80
- Proxying `/api/` requests to Django on port 8000
- Making frontend and API same-origin (eliminating cross-origin cookie issues)

## Git Commit Hashes
```
29a68d306a deploy: Add nginx config and deployment script for CT 920
a67491933c docs: Add environment configuration template for cross-origin setup
130fcf5f82 fix: Set SameSite=None for cross-origin cookies (frontend:80 <-> api:8000)
```

## Verification Steps

### 1. Verify Code is on GitHub
```bash
git log --oneline -3 origin/preview
# Expected output:
# 29a68d306a deploy: Add nginx config and deployment script for CT 920
# a67491933c docs: Add environment configuration template for cross-origin setup
# 130fcf5f82 fix: Set SameSite=None for cross-origin cookies (frontend:80 <-> api:8000)
```

### 2. Deploy to CT 920
Since direct SSH access was not available, manual deployment steps:

```bash
# On CT 920 as root:
cd /opt/planeagent

# Pull the fix
git fetch origin
git checkout preview
git pull origin preview

# Restart the Django API
systemctl restart plane-api  # or supervisorctl restart plane-api

# Clear browser cookies and test
```

### 3. Test the Fix
```bash
# Test 1: Verify API responds
curl -s http://10.0.0.202:8000/auth/email-check/ \
  -X POST -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'

# Test 2: Check Set-Cookie header includes SameSite=None
curl -s -I -c /tmp/cookies.txt http://10.0.0.202:8000/auth/sign-in/ \
  -X POST -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=YOUR_EMAIL&password=YOUR_PASSWORD" | grep -i set-cookie

# Expected: session-id=xxx; SameSite=None
```

### 4. Browser Verification
1. Open http://10.0.0.202 in browser
2. Open Developer Tools (F12) → Application → Cookies
3. Log in with valid credentials
4. Verify `session-id` cookie is set with `SameSite=None`
5. Verify subsequent API calls include the `session-id` cookie

## Alternative Solution (Recommended for Production)
Instead of using `SameSite=None`, the more robust solution is to:

1. **Use nginx to proxy API requests** (configuration provided in `deployments/nginx/planeagent.conf`)
2. This makes the API same-origin with the frontend (both on port 80)
3. Allows using `SameSite=Lax` (more secure)
4. No cross-origin cookie issues

## Environment Variables Summary
```bash
# Required for cross-origin cookie fix
SESSION_COOKIE_SAMESITE=None
CSRF_COOKIE_SAMESITE=None

# Recommended: Use nginx proxy instead
# Then set these to same value:
WEB_URL=http://10.0.0.202
API_BASE_URL=http://10.0.0.202  # Same as WEB_URL (proxied through nginx)
```

## Files Modified
1. `apps/api/plane/settings/common.py` - Cookie SameSite settings
2. `.env.planeagent.example` - Environment documentation (new file)
3. `deployments/nginx/planeagent.conf` - Nginx configuration (new file)
4. `deployments/scripts/deploy-ct920.sh` - Deployment script (new file)

## Status
- ✅ Code changes committed
- ✅ Changes pushed to GitHub (preview branch)
- ✅ Documentation created
- ⏳ Pending: Deploy to CT 920 (requires SSH access or manual deployment)

## References
- Django Session Cookie Documentation: https://docs.djangoproject.com/en/4.2/ref/settings/#session-cookie-samesite
- SameSite Cookie Explained: https://web.dev/samesite-cookies-explained/
- Cross-Origin Resource Sharing (CORS): https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS