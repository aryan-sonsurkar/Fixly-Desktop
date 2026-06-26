# Architecture

## System Overview

Fixly uses a layered architecture that separates concerns into distinct tiers.

```
┌─────────────────────────────────────┐
│         Tauri Desktop Shell         │
│  (Window management, native APIs,   │
│   auto-updater, sidecar launcher)   │
├─────────────────────────────────────┤
│         React Frontend              │
│  (Components, hooks, stores,        │
│   routing, animations)              │
├─────────────────────────────────────┤
│         Axios HTTP Client           │
│  (JWT interceptor, error handling,  │
│   dynamic base URL)                 │
├─────────────────────────────────────┤
│         FastAPI (Python)            │
│  (API endpoints, middleware,        │
│   request validation, auth)         │
├─────────────────────────────────────┤
│         Service Layer               │
│  (Business logic, AI routing,       │
│   email processing, orchestration)  │
├─────────────────────────────────────┤
│         Repository Layer            │
│  (Supabase queries, data access,    │
│   database operations)             │
├─────────────────────────────────────┤
│         Supabase Cloud              │
│  (Auth, PostgreSQL, Storage,        │
│   Realtime subscriptions)           │
└─────────────────────────────────────┘
```

## Key Principles

### Frontend Never Touches Supabase
The React frontend has zero direct Supabase SDK access. All communication flows through the Python backend via HTTP. This ensures:
- A single source of truth for authentication
- Consistent error handling
- Backend-enforced business logic
- No duplicated auth logic

### Repository Pattern
All database operations are encapsulated in repository modules. Services never import the Supabase SDK directly. This makes the data layer testable and swappable.

### AI Provider Abstraction
The AI service routes requests through a provider chain: Ollama (primary) → Gemini (fallback) → Future providers. The frontend never knows which provider generated a response.

### Sidecar Architecture
In production, Tauri launches the Python backend as a managed sidecar process. The backend binds to a dynamic port and communicates the port number to the frontend via Tauri IPC. No ports are hardcoded.

## Data Flow

```
User Action → React Component → Custom Hook
  → TanStack Query → Service Module → Axios
  → FastAPI Router → Service → Repository
  → Supabase → Response chain reverses
```

## Development vs Production

### Development
- Backend runs independently via Uvicorn on port 8000
- Frontend uses Vite dev server on port 1420
- Tauri dev mode connects to both
- `VITE_API_URL=http://localhost:8000`

### Production
- Tauri bundles Python backend as a sidecar binary
- Backend starts on a dynamically assigned port
- Backend prints `FIXLY_PORT:{port}` to stdout
- Tauri Rust code reads the port and exposes it via IPC
- Frontend reads the port through `window.__TAURI__` invoke

## Design Tokens

All colors are defined as HSL CSS custom properties. No hardcoded hex values.

See `apps/desktop/src/styles/globals.css` for the full token set.

## Authentication Flow

### Session Lifecycle

```
App Launch → restoreSession() (secure storage)
  ├─ Tokens found → POST /auth/refresh → valid?
  │   ├─ Yes → store new tokens → /dashboard
  │   └─ No → GET /auth/me with old token → valid?
  │       ├─ Yes → restore session → /dashboard
  │       └─ No → clear tokens → /login
  └─ No tokens → /login
```

### Sign In Flow

```
Login Page → React Hook Form + Zod validation
  → POST /api/v1/auth/signin (via Axios)
  → FastAPI → AuthService → AuthRepository → Supabase Auth
  → Response: { access_token, refresh_token, user }
  → setTokens() in Tauri secure store
  → setAuth() in Zustand store
  → Navigate to /dashboard
```

### Sign Up Flow

```
Register Page → Form validation (name, email, password, confirm)
  → POST /api/v1/auth/signup
  → FastAPI → AuthService → AuthRepository → Supabase Auth
  → Response: { access_token, refresh_token, user }
  Set verification_required? → /verify-email
  Session created? → /dashboard
```

### Token Refresh Flow (Automatic)

```
Axios interceptor detects 401
  → clearTokens() from secure storage
  → Navigate to /login
  (Automatic refresh happens on app launch via POST /auth/refresh)
```

### Google OAuth Flow

```
Login Page → Click "Google" button
  → GET /api/v1/auth/google/url
  → Open system browser to OAuth URL
  → User authenticates with Google
  → Supabase redirects to callback URL with auth code
  → POST /api/v1/auth/google/callback
  → Exchange code for session
  → Store tokens → Navigate to /dashboard
```

### Secure Storage

- JWT access and refresh tokens are stored using `@tauri-apps/plugin-store`
- Tokens are persisted to disk in an encrypted Tauri store (`auth.json`)
- On app launch, tokens are restored from secure storage
- On sign out or invalid session, tokens are cleared from storage
- Fallback to in-memory storage when Tauri APIs are unavailable (e.g., during dev in browser)
