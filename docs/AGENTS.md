# Project Guide for AI Agents

## Tech Stack
- **Monorepo**: pnpm workspaces + Turborepo (v2)
- **Backend**: Python 3.12, FastAPI, Uvicorn, Supabase SDK, Pydantic
- **Desktop**: React 19, TypeScript, Vite, Tauri v2, Tailwind CSS v4, Framer Motion
- **Shared**: `packages/ui`, `packages/types`, `packages/utils`, `packages/config-*`
- **Auth**: Supabase Auth (email/password, Google OAuth)
- **Database**: Supabase PostgreSQL
- **Storage**: Supabase Storage (for attachments)

## Architecture Pattern
```
Route Handler → Service → Repository → Supabase
```
- Route handlers are thin (HTTP concerns only)
- Services contain business logic
- Repositories abstract data access (can be mocked for tests)
- Projects: `apps/backend/` (Python), `apps/desktop/` (React/Tauri)

## Backend Structure (Python)
```
apps/backend/app/
├── api/v1/          — FastAPI route handlers
├── repositories/    — Database access layer
├── services/        — Business logic
├── schemas/         — Pydantic models for API
├── models/          — DB client initialization
├── prompts/         — Centralized Prompt Management System
│   ├── __init__.py     - Exports PromptManager, PromptType, PromptTemplate
│   ├── manager.py      - PromptManager (loads context, resolves variables)
│   ├── registry.py     - PromptType enum, PromptTemplate, PromptRegistry, auto_discover
│   ├── utils.py        - resolve_variables(), count_placeholders()
│   └── templates/      - 11 prompt templates (auto-discovered)
├── providers/       — AI provider implementations (Ollama, Gemini)
├── migrations/      — SQL migration files
├── main.py          — App factory, middleware, CORS
└── config.py        — Pydantic Settings
```

## Frontend Structure (React)
```
apps/desktop/src/
├── components/      — React components (grouped by domain)
├── stores/          — Zustand stores
├── lib/             — API clients, service wrappers
├── pages/           — Page-level components
└── App.tsx          — Router configuration
```

## State Management
- **Zustand** for global state (auth, settings, AI)
- **TanStack Query** for server state (assignments, conversations)
- Auth state persisted to localStorage with auto-restore

## AI Architecture
- **Provider chain**: Ollama (local) → Gemini (cloud) → error
- **Prompt System**: Centralized. All prompts in `app/prompts/templates/`. Auto-discovered by registry. Every AI request passes through `PromptManager.build()`.
- **Prompt Registry**: Singleton `PromptRegistry` maps `PromptType` → `PromptTemplate` (template string + versioning metadata). Populated lazily via `auto_discover()` on first access.
- **Variable Injection**: `Utils.resolve_variables()` replaces `{user_name}`, `{education_type}`, `{branch}`, `{year}`, `{college}`, `{subjects}`, `{current_date}` from context + any kwargs.
- **Prompt Versioning**: Every `PromptTemplate` has name, version, description, author, last_updated.
- **Providers**: Each implements `AIProvider` abstract with `generate()` / `generate_stream()`
- **Conversations**: Stored in PostgreSQL via Supabase, auto-titled by first message
- **Settings**: Per-user AI preferences stored in `settings` table JSON

## Adding a New AI Feature
1. Create `app/prompts/templates/my_feature.py` with `PROMPT` (PromptTemplate) and `PROMPT_TYPE` (PromptType) exports
2. Done — auto-discovered at runtime. No existing code modified.

## Key Conventions
- No comments in code unless absolutely necessary
- Backend models use `create_model("Name", ...)` dynamic Pydantic models
- Frontend uses Tailwind CSS v4 utility classes (no CSS modules)
- API routes versioned: `/api/v1/...`
- Migrations numbered: `YYYYMMDDHHMMSS_description.sql`
- Type annotations required everywhere (mypy strict)
- Avoid adding npm dependencies — prefer custom lightweight implementations

## Verification Commands
```bash
# Backend
cd apps/backend && uv run mypy app --strict
cd apps/backend && uv run ruff check app

# Desktop
cd apps/desktop && pnpm typecheck
cd apps/desktop && pnpm lint

# Full monorepo
pnpm typecheck  (runs all 8 typecheck tasks)
pnpm build      (packages only — desktop needs Rust)
```

## Current State (Milestone 6 complete — AI Platform)
- Backend: 58 source files, 0 mypy errors
- Desktop: 0 errors, 6 pre-existing lint warnings
- Blocked: Google OAuth callback, Docker for local Supabase, Tauri Rust toolchain
- Next: Email intelligence (v0.6.0), Pomodoro (v0.7.0), Notifications (v0.7.0)
