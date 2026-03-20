# PlaneAgent Login Fix Solutions

## Problem

Cross-origin cookie blocking between ports 80 and 8000.

When the frontend runs on port 80 (nginx) and the backend API runs on port 8000 (Django), browsers treat these as different origins. This causes issues with:

- Session cookies not being sent with API requests
- CSRF token validation failures
- Authentication state not persisting between requests

## Solution 1: Nginx Same-Origin Proxy (DEPLOYED - Preferred)

This solution uses nginx to proxy API and auth requests to the backend, making everything appear to come from the same origin (port 80).

### How it works:

- Frontend served from `/opt/planeagent/apps/web/build` via nginx
- `/api/*` requests proxied to `http://localhost:8000/api/`
- `/auth/*` requests proxied to `http://localhost:8000/auth/`
- Frontend uses relative URLs (empty `VITE_API_BASE_URL`)

### Nginx Configuration:

```nginx
server {
    listen 80;
    server_name _;

    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /auth/ {
        proxy_pass http://localhost:8000/auth/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        root /opt/planeagent/apps/web/build;
        try_files $uri $uri/ /index.html;
    }
}
```

### Files Modified:

- `/opt/planeagent/apps/web/.env` - Set `VITE_API_BASE_URL=` (empty for relative URLs)
- `/etc/nginx/sites-available/planeagent` - New nginx config
- `/etc/nginx/sites-enabled/planeagent` - Symlink to enable

### To Rebuild After Changes:

```bash
cd /opt/planeagent/apps/web
pnpm build
```

## Solution 2: SameSite=None Cookies (Fallback)

If same-origin proxying isn't possible, configure Django to use `SameSite=None` cookies.

### Backend Changes:

In `apps/api/plane/settings/common.py` or local_settings.py:

```python
SESSION_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_SECURE = True  # Required for SameSite=None
CSRF_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SECURE = True
```

### Frontend Changes:

Keep using `http://10.0.0.202:8000` as the API URL but ensure all requests include:

```javascript
credentials: "include";
```

### Trade-offs:

- Requires HTTPS in production (cookies marked Secure)
- Less secure than same-origin approach
- Some browsers block third-party cookies entirely

## How to Switch Between Solutions

### To Use Solution 1 (Nginx Proxy):

```bash
# Update env to use relative URLs
echo 'VITE_API_BASE_URL=' > /opt/planeagent/apps/web/.env

# Enable nginx proxy config
sudo ln -sf /etc/nginx/sites-available/planeagent /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# Rebuild frontend
cd /opt/planeagent/apps/web && pnpm build
```

### To Use Solution 2 (SameSite=None):

```bash
# Update env to use direct backend URL
cat > /opt/planeagent/apps/web/.env << 'EOF'
VITE_API_BASE_URL=http://10.0.0.202:8000
VITE_WEB_BASE_URL=http://10.0.0.202
EOF

# Update Django settings to use SameSite=None cookies
# (edit apps/api/plane/settings/common.py)

# Rebuild frontend
cd /opt/planeagent/apps/web && pnpm build
```

## Current Deployment Status

**Currently Deployed:** Solution 1 (Nginx Same-Origin Proxy)

**Location:** CT 920
**Frontend:** http://10.0.0.202 (nginx port 80)
**Backend API:** http://10.0.0.202:8000 (proxied via nginx)
**Nginx Config:** `/etc/nginx/sites-available/planeagent`
