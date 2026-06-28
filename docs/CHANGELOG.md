# Changelog

## [0.5.0] — 2026-06-26

### Added
- AI Platform — complete AI infrastructure for the entire Fixly ecosystem
- Backend AI layer: schemas, repository, service, provider abstraction
- Ollama provider — local LLM support via Ollama API (llama3.2)
- Gemini provider — Google Gemini 2.0 Flash via REST API
- Auto-routing: Ollama → Gemini → graceful error with provider health checks
- Prompt Manager — centralized prompt routing with domain-specific builders:
  - SystemPromptBuilder (academic context, profile, subjects)
  - AssignmentPromptBuilder, CodingPromptBuilder, StudyPromptBuilder
  - SummaryPromptBuilder, BriefingPromptBuilder
- Conversation management: create, list, get, rename, delete conversations
- Message persistence with provider name and token count
- Auto-titling: first message becomes conversation title
- Auto-overdue: marks pending/in_progress assignments as overdue on access
- Frontend AI page with conversation sidebar and chat window
- Real-time chat with send message, regenerate, markdown rendering
- Markdown renderer with headings, lists, inline code, bold, dividers
- Code blocks with language label and copy button
- Typing indicator animation (Framer Motion)
- AI settings dialog: provider selection, temperature, max tokens, streaming, system prompt
- Frontend Zustand store for AI state management
- TanStack Query integration for conversations and messages
- Database migration: 20250101000003_ai_platform.sql (conversations + messages tables)
- Provider availability endpoints for frontend status indicators

### Changed
- Router: AI route now renders AIPage instead of placeholder
- AppLayout sidebar: AI Assistant navigation item points to /ai page
- Instantiated PromptManager replaces PromptBuilder throughout AIService
- Backend typecheck: 58 source files, 0 mypy errors
- Settings table now stores AI configuration (preferred_provider, temperature, max_tokens, streaming, system_prompt)

## [0.4.0] — 2026-06-26

### Added
- Assignment management system with full CRUD
- Dashboard page with daily briefing, stats overview, XP display, recent assignments
- AppLayout with sidebar navigation (collapsible, icons, active state)
- Bulk actions for assignments (complete, archive, delete, pin/unpin, favorite/unfavorite)
- List and board (kanban) views for assignments
- Filter bar with search, status, priority, subject, favorites filters
- Paginated assignment list with sort options
- Assignment detail dialog with attachment upload/delete
- Assignment form dialog (create/edit mode)
- File uploads through backend (/api/v1/upload endpoint)
- Supabase Storage integration for attachments
- Backend stats endpoint with 9 metrics
- Overdue auto-detection on list/get/stats access

### Changed
- Router: dashboard, assignments use real pages with AppLayout Outlet
- ProtectedLayout replaced with AppLayout (sidebar + header + Outlet)
- Project scope increased to 58 backend source files

## [0.3.0] — 2026-06-26

### Added
- Onboarding wizard — multi-step form (Personal, Academic, Institution, Preferences, Subjects) with progress indicator
- Profile page — view and edit academic identity (personal, academic, institution fields)
- Settings page — theme (dark/light/system), daily goal, pomodoro durations, notification toggles
- Subject management page — full CRUD with color picker, icon, credits
- Protected route onboarding check — redirects to /onboarding if profile incomplete
- Academic profile fields: display_name, education_type, education_year, college_name, university_board, branch_stream, division, roll_number, onboarding_completed
- Extended settings: daily_goal_hours, assignment_reminders, daily_briefing, email_monitoring
- Extended subjects: icon, credits
- Backend profile endpoints: GET/PUT /profile/me, GET/PUT /profile/settings, POST /profile/onboarding, GET /profile/onboarding/status
- Backend subject endpoints: GET/POST /subjects, GET/PUT/DELETE /subjects/:id
- ProfileService, ProfileRepository, SubjectService, SubjectRepository
- Profile, Settings, Subject Pydantic schemas with validation
- Frontend API service module for profile and subject calls (profile-service.ts)
- Database migration: 20250101000001_academic_profile.sql

### Changed
- Router: added /onboarding, /settings, /subjects, /profile routes
- ProtectedRoute: checks onboarding status and redirects to /onboarding
- shared-types: Subject extended with icon, credits; added Profile and Settings interfaces
- api/v1/__init__.py: registered profile_router and subjects_router

## [0.2.0] — 2026-06-26

### Added
- Complete authentication system (login, register, forgot password, email verification)
- Login page with email/password and Google OAuth button
- Registration page with name, email, password, confirm password, password strength indicator
- Forgot password page with email input and success confirmation screen
- Email verification page with resend capability
- Premium auth UI with Framer Motion animations, gradient backgrounds, backdrop blur
- AuthLayout component for consistent auth page shell
- Zod schemas with strong password validation (uppercase, lowercase, number, min 8)
- Auth service module for all auth API calls
- Backend endpoints: forgot-password, reset-password, resend-verification, google/url, google/callback
- Google OAuth URL generation and code exchange flow
- Password strength indicator bar in registration form
- Password visibility toggle on all password fields
- Inline form validation with error messages
- Loading spinners and disabled buttons during submission
- Keyboard navigation support (Enter to submit, autofocus)
- Session persistence across application restarts via Tauri secure store
- Automatic token refresh on app launch
- Automatic logout on invalid/expired session
- Protected route guard (unauthenticated → /login)
- Smooth page transitions and error animations
- Dark and light theme support for all auth pages

### Changed
- Router initial entry changed to /login
- Auth endpoints updated to match implementation (signup, signin, signout, refresh, me)
- API documentation updated with all auth endpoints and error responses
- Architecture documentation updated with auth flow diagrams
- Auth repository extended with password reset, verification resend, Google OAuth methods

### Fixed
- ESLint configuration migrated to flat config format (eslint.config.js)
- Turborepo pipeline renamed to tasks (v2 migration)
- Python mypy strict mode warnings resolved
- Ruff lint issues fixed (import sorting, line length)
- Turbo CLI not found — installed as root devDependency
- Multiple Python version handling for virtual environment

## [0.1.0] — 2026-06-26

### Added
- Monorepo structure with pnpm workspaces and Turborepo
- Tauri v2 desktop application with React, TypeScript, Tailwind CSS
- Python FastAPI backend with layered architecture
- Shared packages: UI components, types, utilities, configuration
- Design token system (CSS variables for dark/light themes)
- MemoryRouter-based routing (no browser dependency)
- Axios HTTP client with JWT interceptor
- Zustand stores (auth, UI)
- TanStack Query provider
- Structured logging (frontend and backend)
- Global error handling (Error Boundary, exception handlers)
- Feature flag infrastructure
- Architecture Decision Records (ADRs)
- GitHub Actions CI/CD pipeline
- Husky + lint-staged for pre-commit checks
- ESLint, Prettier, EditorConfig configuration
- Comprehensive documentation (architecture, API, database, etc.)
- Supabase database schema (all tables with RLS)
- Tauri sidecar configuration for Python backend
- Dynamic port management for production
