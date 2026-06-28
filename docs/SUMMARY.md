# Fixly — Project Summary

## What's Done

### Architecture & Infrastructure
- Monorepo: pnpm workspaces + Turborepo
- Backend: Python 3.12 + FastAPI + Uvicorn
- Desktop: React 19 + TypeScript + Vite + Tauri v2
- Shared packages: `config-eslint`, `config-typescript`, `ui`, `types`, `utils`
- CI/CD: GitHub Actions (backend lint/test, desktop build)
- Docker: Python dev container + Supabase local setup
- Sidecar: Tauri launches Python backend in production

### Authentication (v0.2.0)
- Email/password signup, login, logout via Supabase Auth
- Google OAuth (backend endpoint done, frontend not yet wired)
- Protected routes, auth store, token refresh
- Session persistence with auto-restore on app launch
- Settings page: profile editing, preferences, account actions

### Onboarding
- Multi-step wizard: welcome, education info, subjects, preferences
- Anonymous skip mode → education as config, not profile
- Backend validates education type → valid year mapping

### Assignments (v0.3.0/v0.4.0)
- Full CRUD with title, description, due_date, priority, status, subject
- Status transitions: pending → in_progress → completed, overdue auto-mark
- Pagination, filtering (status, priority, subject, search, favorites)
- List + Board (kanban) views
- Assignment detail dialog with editable fields
- Attachment upload/delete (Supabase Storage)
- Bulk actions: complete, archive, delete, pin/unpin, favorite/unfavorite
- Stats endpoint: 9 metrics (total, completed, overdue, avg time, etc.)
- Auto-overdue: marks past-due assignments on list/get/stats access
- Due today and due this week filtering

### Dashboard (v0.4.0)
- Greeting with student name and time-appropriate message
- XP, streak display
- 4 stat cards (pending, overdue, completed, total)
- Completion progress ring
- Subject grid with colors and icons
- Recent assignments list

### AI Platform (v0.5.0)
- Abstraction layer: AIProvider (OllamaProvider, GeminiProvider)
- Auto-routing: Ollama → Gemini → fallback error
- Provider health checks per request
- Conversation management: create, list, get, rename, delete
- Message persistence with provider name and token count
- Prompt Manager with domain-specific builders (system, assignment, coding, study, summary, briefing)
- Auto-context: injects profile + subjects into system prompts
- Auto-titling: first message becomes conversation title
- Chat UI: conversation sidebar, chat window, typing indicator
- Markdown renderer with headings, code blocks, lists, bold, inline code
- AI Settings dialog: provider choice, temperature, max tokens, streaming toggle, system prompt
- Zustand store for AI state + TanStack Query for data management

### Verification (as of last run)
- Backend: 58 source files, 0 mypy errors, 0 typecheck errors
- Backend ruff: 19 E501 line length warnings (pre-existing + new), 0 errors
- Desktop: 0 TypeScript errors, 0 eslint errors (6 pre-existing warnings)
- All Turbo typecheck tasks: 8/8 pass
- Turbo build: packages build, desktop fails (expected — Tauri needs Rust toolchain)

## What's Blocked / Not Started

### Blocked
- Google OAuth callback page (Supabase redirect issue)
- Local Supabase (Docker not available on user's machine)
- Tauri build cache not wired for sidecar bundling

### Not Started
- **Email Intelligence (v0.6.0)**: Gmail OAuth, auto-detection, email parsing
- **Pomodoro Timer (v0.7.0)**: Focus/break cycles, ambient sounds
- **Notifications (v0.7.0)**: Backend has scaffold, no UI
- **Analytics Dashboard (v0.7.0)**: Study time, XP, streaks, productivity trends
- **PDF Intelligence (v0.8.0)**: Summarization, Q&A, OCR
- **File Analysis**: OCR for handwritten notes, image analysis
- **Calendar Integration**: Google Calendar sync
- **Platform Expansion**: Web app, mobile apps
- **Collaboration**: Google Classroom, Moodle, study groups

## Key Decisions
1. **Education type → year mapping via Config object**, not hardcoded in DB
2. **Onboarding as single POST** that creates/updates profile + settings atomically
3. **Overdue as explicit status** (auto-detected, stored in DB, shown in UI)
4. **Stats endpoint is its own route** not inferred from list
5. **File uploads go through backend only** — never direct to Supabase Storage
6. **TanStack Query for assignment data** — caching, pagination, background refetch
7. **No notification UI yet** — backend methods accept event data but only log
8. **AI Provider Abstraction** — frontend never knows which provider generated a response; routing is server-side with Ollama → Gemini → error
9. **Prompt Manager** — all prompts centralized in `app/prompts/`, new features add a new PromptType
10. **No markdown library dependency** — built custom MarkdownRenderer to avoid npm dependency

## Key Architecture Files

### Backend (apps/backend/app/)
```
├── api/v1/
│   ├── auth.py, users.py, subjects.py, settings.py
│   ├── assignments.py, uploads.py, dashboard.py, ai.py
│   └── __init__.py (router aggregation)
├── repositories/
│   ├── user_repository.py, subject_repository.py
│   ├── assignment_repository.py
│   └── ai_repository.py
├── services/
│   ├── user_service.py, subject_service.py
│   ├── assignment_service.py, auth_service.py
│   ├── ai_service.py, token_counter.py
│   └── prompt_builder.py (deprecated — use prompt manager)
├── prompts/
│   ├── __init__.py, base.py, manager.py
│   ├── system.py, assignment.py, coding.py
│   └── study.py, summary.py, briefing.py
├── providers/
│   ├── __init__.py, base.py, ollama.py, gemini.py
├── schemas/
│   ├── auth.py, user.py, profile.py, subject.py, settings.py
│   ├── assignment.py, upload.py, dashboard.py, ai.py
├── models/
│   └── database.py (Supabase client initialization)
├── migrations/
│   ├── 20250101000001_initial.sql
│   ├── 20250101000002_extend_settings.sql
│   └── 20250101000003_ai_platform.sql
└── main.py, config.py, middleware.py
```

### Frontend Desktop (apps/desktop/src/)
```
├── components/
│   ├── app-layout.tsx (sidebar + header + Outlet)
│   ├── auth/ (login, signup, protected routes)
│   ├── assignments/ (list, board, detail, form, filter)
│   ├── settings/ (profile, appearance, subjects, account)
│   ├── dashboard/ (stats, greeting, XP)
│   ├── onboarding/ (wizard steps)
│   ├── ui/ (button, input, dialog, select, etc.)
│   └── ai/
│       ├── chat-window.tsx, message.tsx, code-block.tsx
│       ├── markdown-renderer.tsx, typing-indicator.tsx
│       ├── empty-state.tsx, conversation-sidebar.tsx
│       ├── ai-settings-dialog.tsx, index.ts
├── stores/ (auth-store, settings-store, ai-store)
├── lib/ (api client, dashboard-service, ai-service)
├── pages/ (auth, settings, dashboard, assignments, ai)
└── App.tsx (router with layouts)
```
