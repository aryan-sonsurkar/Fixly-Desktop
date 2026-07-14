# Fixly Desktop Authentication Architecture

## 1. Development Authentication Flow

### Overview
During development, email verification is **disabled** to allow rapid iteration. The flow is:

```
Register → Backend auto-signs-in → Dashboard
```

### Implementation
- **Backend** (`apps/backend/app/services/auth_service.py`): In `sign_up()`, if `settings.environment == "development"` and no session is returned (email not confirmed), immediately call `sign_in()` to create a session.
- **Frontend**: Register page redirects directly to `/dashboard` on success (no `/verify-email` intermediate page).
- **Verify Email page**: Checks `isAuthenticated` and redirects to `/dashboard` immediately if already logged in.

### Supabase Local Config (`supabase/config.toml`)
```toml
[auth.email]
enable_confirmations = false  # Disabled for local development
```

### Environment Variable
```bash
ENVIRONMENT=development  # Enables auto-sign-in behavior
```

---

## 2. Production Authentication Flow

### Architecture
```
Desktop App
    ↓ Register
Supabase Auth
    ↓ Verification Email
https://fixly.app/auth/verify (web landing page)
    ↓ User clicks link
fixly://auth/verified?token=<token> (deep link)
    ↓ Desktop app receives URI
Tauri → Frontend event → API /auth/verify-email
    ↓ Tokens validated
Desktop app resumes authenticated session
```

### Required Production Setup

#### 1. Supabase Dashboard Configuration
- **Site URL**: `https://fixly.app`
- **Redirect URLs**: 
  - `https://fixly.app/auth/verify` (web)
  - `fixly://auth/verified` (desktop deep link)
- **Email Templates**: Update verification email to use production site URL
- **Google OAuth**: Configure in Supabase Auth providers

#### 2. Backend Environment
```bash
ENVIRONMENT=production
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
SUPABASE_JWT_SECRET=...
```

#### 3. Frontend Environment
```bash
VITE_API_URL=https://api.fixly.app
```

#### 4. Tauri Config (`tauri.conf.json`)
```json
{
  "bundle": {
    "deepLink": {
      "schemes": ["fixly"]
    }
  }
}
```

---

## 3. Deep Link Implementation Plan

### Current State (Prepared)
- ✅ Tauri config: `deepLink.schemes = ["fixly"]`
- ✅ Rust: `set_uri_scheme_protocol_handler("fixly", ...)` in `lib.rs`
- ✅ Frontend: Event listener for `deep-link` event in `auth-context.tsx`
- ✅ Backend: `/auth/verify-email` and `/auth/google/callback` endpoints return `RedirectResponse` to `fixly://...`
- ✅ Frontend: `/auth/callback` page handles tokens from hash fragment

### Remaining Production Tasks

| Task | Location | Status |
|------|----------|--------|
| Register `fixly://` URL scheme in Windows installer | `tauri.conf.json` + NSIS/WiX | ⚠️ TODO |
| Configure Supabase email template with production URL | Supabase Dashboard | ⚠️ TODO |
| Add production redirect URLs in Supabase Auth | Supabase Dashboard | ⚠️ TODO |
| Configure Google OAuth in Supabase | Supabase Dashboard | ⚠️ TODO |
| Test deep link on clean Windows install | Manual QA | ⚠️ TODO |
| Handle token storage securely (OS keychain) | `lib.rs` + frontend | ⚠️ TODO |

### Deep Link Routes
| Deep Link | Purpose | Handler |
|-----------|---------|---------|
| `fixly://auth/callback` | Google OAuth | Frontend extracts tokens from hash |
| `fixly://auth/verified?token=...` | Email verification | Frontend calls `/auth/verify-email` |
| `fixly://auth/login` | Fallback login | Redirect to login page |

---

## 4. Google OAuth Status

### Current State
- **Supabase Config**: Provider added but `enabled = false` (see `supabase/config.toml`)
- **Frontend**: Button shows "Coming soon" and is disabled
- **Backend**: `/auth/google/url` and `/auth/google/callback` endpoints exist with TODOs

### Production Requirements
1. Create Google Cloud project and OAuth credentials
2. Add to Supabase Dashboard → Auth → Providers → Google
3. Set redirect URIs:
   - Web: `https://fixly.app/auth/google/callback`
   - Desktop: `fixly://auth/callback`
4. Enable provider in `supabase/config.toml` and set `SUPABASE_AUTH_EXTERNAL_GOOGLE_SECRET`

---

## 5. Verification Checklist

### Development Mode ✓
- [x] Register → Dashboard (no email verification)
- [x] Login → Dashboard
- [x] Logout → Login page
- [x] Password reset email sent (no-op in dev)
- [x] Session persists across reloads (Tauri secure store)
- [x] Protected routes redirect to login
- [x] Token refresh works automatically

### Production Readiness
| Flow | Dev | Prod |
|------|-----|------|
| Email/Password Register | ✅ Auto-login | 🔄 Needs deep link |
| Email/Password Login | ✅ | ✅ |
| Email Verification | ❌ Disabled | 🔄 Needs deep link |
| Password Reset | ✅ | ✅ |
| Google OAuth | ❌ Disabled | 🔄 Needs config |
| Session Persistence | ✅ | ✅ |
| Token Refresh | ✅ | ✅ |
| Protected Routes | ✅ | ✅ |

---

## 6. Files Modified

### Backend
- `apps/backend/app/services/auth_service.py` - Auto sign-in in dev mode
- `apps/backend/app/api/v1/auth.py` - Production callback endpoints with TODOs

### Frontend
- `apps/desktop/src/pages/register.tsx` - Direct to dashboard after register
- `apps/desktop/src/pages/verify-email.tsx` - Auto-redirect if authenticated
- `apps/desktop/src/pages/auth-callback.tsx` - New: Handles deep link tokens
- `apps/desktop/src/contexts/auth-context.tsx` - Deep link event listener
- `apps/desktop/src/router/index.tsx` - Added `/auth/callback` route
- `apps/desktop/src/stores/auth-store.ts` - Export `useAuthStore` properly

### Tauri / Config
- `apps/desktop/src-tauri/tauri.conf.json` - Added `deepLink.schemes = ["fixly"]`
- `apps/desktop/src-tauri/src/lib.rs` - Deep link protocol handler
- `supabase/config.toml` - Added Google OAuth provider template

---

## 7. Required Changes Before Public Release

1. **Supabase Project**: Update to production settings (Site URL, Redirect URLs, Email Templates)
2. **Google OAuth**: Configure in Supabase Dashboard and Google Cloud Console
3. **Tauri Deep Links**: Test `fixly://` registration on clean Windows install
4. **Token Storage**: Use OS keychain (Windows Credential Manager) via Tauri plugin
5. **HTTPS**: Configure production domain with SSL certificates
6. **Rate Limiting**: Enable Supabase auth rate limits in production
7. **Monitoring**: Add logging for auth events and errors

---

## 8. Testing Commands

```bash
# Backend
cd apps/backend
.\.venv\Scripts\python.exe -m pytest tests/ -v
.\.venv\Scripts\python.exe -m ruff check app/
.\.venv\Scripts\python.exe -m mypy app/

# Frontend
cd apps/desktop
pnpm typecheck
pnpm lint
pnpm test
```

---

*Document generated: $(date)*