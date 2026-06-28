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

### AI Platform Architecture

The AI system uses a layered provider architecture:

```
AI API (FastAPI)
    ↓
AIService (routing, conversation management)
    ↓
PromptManager → SystemPromptBuilder, AssignmentPromptBuilder, etc.
    ↓
AIProvider Interface (abstract base)
    ↓
OllamaProvider ─── GeminiProvider ─── Future Providers
```

**Provider Routing Logic:**
1. If `preferred_provider` is `"auto"`: try Ollama first → Gemini fallback → error
2. If a specific provider is set: check availability → use it → error if unavailable
3. Provider availability is checked per-request via health check endpoints

### Prompt Management System

All AI prompts pass through a centralized Prompt Management System.

```
AI Provider (Ollama / Gemini)
    ↓  requests prompt
PromptManager.build(PromptType, user_id, **kwargs)
    ↓
PromptRegistry.get(PromptType)
    ↓  returns PromptTemplate (template string + metadata)
Utils.resolve_variables(template, context, kwargs)
    ↓  substitutes {user_name}, {subjects}, {current_date}, ...
Final rendered prompt string
```

**Architecture:**

```
app/prompts/
├── __init__.py          — Exports: PromptManager, PromptType, PromptTemplate, get_registry
├── manager.py           — PromptManager: loads context, resolves variables, returns prompt
├── registry.py          — PromptType enum, PromptTemplate dataclass, PromptRegistry, auto_discover
├── utils.py             — resolve_variables(), count_placeholders()
└── templates/
    ├── __init__.py       — Empty (auto-discovered)
    ├── system.py         — System prompt with academic context
    ├── assignment.py     — Assignment assistance
    ├── coding.py         — Coding tutor
    ├── study.py          — Study assistant
    ├── summary.py        — Content summarization (PromptType.SUMMARIZE)
    ├── briefing.py       — Daily briefing
    ├── pdf.py            — PDF document analysis
    ├── screenshot.py     — Screenshot/image analysis
    ├── ocr.py            — OCR text extraction
    ├── email.py          — Email drafting/reply
    └── planner.py        — Academic planning
```

**Prompt Lifecycle:**

1. **Registration** — When the system starts, `auto_discover()` scans `app/prompts/templates/` and registers every module that exports `PROMPT` (a `PromptTemplate`) and `PROMPT_TYPE` (a `PromptType`). No manual registration is needed.

2. **Building** — A request arrives at `PromptManager.build(PromptType, user_id, **kwargs)`:
   - The registry looks up the template by `PromptType`
   - If `requires_context=True` and `user_id` is provided, user context (profile, subjects) is loaded from repositories
   - `resolve_variables()` replaces all `{variable}` placeholders with values from context and kwargs
   - Auto-injected variables: `{user_name}`, `{education_type}`, `{branch}`, `{year}`, `{college}`, `{subjects}`, `{current_date}`
   - Explicit kwargs override auto-injected values

3. **Consumption** — The rendered string is passed to the AI provider as the system prompt or feature prompt.

**Prompt Registry:**
- Singleton `PromptRegistry` holds a `dict[PromptType, PromptTemplate]`
- Access via `get_registry()` — lazily triggers auto-discovery on first access
- `register(prompt_type, template)` for programmatic registration
- `get(prompt_type)` raises `KeyError` if type is unknown

**Prompt Versioning:**
Each `PromptTemplate` carries metadata:
- `name` — unique identifier
- `version` — semantic version (e.g. "1.0.0")
- `description` — what this prompt does
- `author` — who created it
- `last_updated` — ISO date of last change

**Variable Injection:**
- Auto-injected from user profile: `{user_name}`, `{education_type}`, `{branch}`, `{year}`, `{college}`
- Auto-injected from subjects: `{subjects}` (comma-separated list)
- Auto-injected date: `{current_date}` (ISO format)
- Feature-specific kwargs: `{assignment_title}`, `{due_date}`, `{subject}`, `{content}`, `{email_context}`, `{assignment_load}`, etc.
- Missing variables are left as-is (e.g. `{unknown_var}` stays `{unknown_var}`)
- Explicit kwargs always override context values

**Extensibility:**
Adding a new AI feature requires zero changes to existing code:
1. Create `app/prompts/templates/my_new_feature.py` with `PROMPT` and `PROMPT_TYPE` exports
2. Call `PromptManager.build(PromptType.MY_FEATURE, user_id, **kwargs)` from your service

Examples of future features that follow this pattern:
- AI Flashcards → `templates/flashcards.py`
- Quiz Generator → `templates/quiz.py`
- Exam Preparation → `templates/exam.py`
- Career Assistant → `templates/career.py`
- Resume Review → `templates/resume.py`
- Interview Coach → `templates/interview.py`

**Testing:**
- 18 unit tests in `tests/test_prompts.py` covering registry, variable resolution, template metadata, and PromptManager.build()
- Tests verify: registration, lookup errors, variable replacement, missing variable handling, kwargs overrides, context injection, and all template metadata

**Provider Interaction:**
Providers (Ollama, Gemini) call `PromptManager.build()` indirectly through `AIService._format_messages()`, which uses `PromptType.SYSTEM` for the system prompt. Feature-specific prompts will be delivered as separate calls when those features are built.

**Conversation System:**
- Conversations and messages stored in PostgreSQL via Supabase
- Messages are ordered by `created_at`
- Auto-titling: first message becomes conversation title
- Provider name and token count stored per message

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
