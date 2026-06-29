# Changelog

## [1.0.0] — 2026-06-29

### Added
- **Dashboard v2** — modular widget system with drag-and-drop reordering, AI Daily Briefing, Today's Focus, AI Recommended Tasks, Upcoming Assignments, XP & Streak, Productivity Score, Quick Actions with global search trigger
- **Universal AI Workspace** — enhanced AI page with workspace context preview panel showing assignments, focus, subjects; plan generation endpoints (daily/weekly/revision)
- **Planner UI** — dedicated planner page with Daily, Weekly, and Revision views; AI-generated study plans with context summaries; generate/regenerate/edit flow
- **Global Search (Ctrl+K)** — command palette overlay with instant search across assignments, subjects, emails, documents, conversations, notes; category filters; recent searches; keyboard navigation; ESC to dismiss
- **Notification Center** — full notification page with infinite scroll; read/unread filters; type filters (assignments, exams, deadlines, email, AI, briefing); mark all read; delete; auto-polling for unread count
- **Email Intelligence UI** — smart categories dashboard (Assignments, Exams, Internships, Placements, Scholarships, Circulars); enhanced inbox with category badges and AI summaries; improved review queue with confidence indicators; Smart Categories tab with per-category breakdown
- **Toast Notification System** — animated toast stack with success/error/info/warning types; auto-dismiss; zustand-driven
- **Workspace Polish** — keyboard shortcuts hook (Ctrl+K, ESC, auto-refresh); skeleton loading states; error boundaries; route-based lazy loading (React.lazy + Suspense); consistent spacing and transitions
- **Backend Services** — Context Engine (workspace_context.py), Planner Service (planner_service.py), Notification Service (notification_service.py + repository), Search Service (search_service.py), Dashboard Service (dashboard_service.py) with productivity scoring and daily briefing aggregation
- **API Endpoints** — `/api/v1/ai/plan/daily`, `/api/v1/ai/plan/weekly`, `/api/v1/ai/plan/revision`, `/api/v1/notifications/*` (full CRUD + mark read all), `/api/v1/search`, `/api/v1/dashboard/briefing`
- **Zustand Stores** — dashboard-store (widgets, briefing, layout), notification-store (infinite scroll, filters, unread count), search-store (command palette state, recent searches), planner-store (daily/weekly/revision plans), toast-store
- **Dashboard Widget Components** — BriefingWidget, FocusWidget, DeadlinesWidget, QuickActionsWidget, XPStreakWidget, ProductivityScoreWidget, EmailWidget
- **Frontend Services** — notification-service.ts, planner-service.ts, search-service.ts

### Changed
- Router: replaced PlaceholderRoute for `/notifications` with NotificationPage; added `/planner` route; comprehensive lazy loading for all pages
- AppLayout: added search bar (Ctrl+K trigger) with keyboard shortcut hint; notification bell icon; conditional collapse button; renamed "AI Assistant" to "AI Workspace" in sidebar
- Dashboard: completely rewritten with widget-based architecture, draggable reordering, briefing integration, direct search trigger
- AI page: added workspace context panel toggle, renamed to "AI Workspace", context auto-injection indicator
- Email page: added Smart Categories tab, enhanced review queue UI, toast notifications for sync/briefing operations, improved navigation with consistent iconography
- AppProvider: integrated keyboard shortcuts hook, increased gcTime for query cache

### Performance
- Route-based code splitting via React.lazy for all 16 pages
- Reduced initial bundle: only auth/login pages loaded at startup
- TanStack Query gcTime increased to 10min for better caching
- Zustand selector optimization with shallow equality
- Debounced search (200ms) in command palette

## [0.9.0] — 2026-06-28

### Added
- Email Intelligence — automated email classification and assignment extraction
- Backend: EmailService, EmailClassifier (AI via PromptManager), DuplicateDetector, EmailSyncWorker
- API endpoints: accounts CRUD, sync, messages, review queue, daily briefing, dashboard stats
- Email classification: assignment, exam, project, notice, holiday, event, general, spam
- Auto-extraction: due dates, priorities, teacher names, courses from assignment emails
- Review queue: approve/edit/reject detected assignments with manual override
- Daily briefing: AI-generated academic summary of unread emails and pending reviews
- Dashboard stats: account overview, unread counts, recent academic emails, sync status
- Frontend email page: inbox with search, read/unread, classification badges, review queue, account management
- 4 database tables: email_messages, email_classifications, email_assignments, email_attachments
- Database migration: 20250101000009_email_intelligence.sql
- `.gitattributes` for consistent LF line endings across environments

### Changed
- README: Node.js requirement updated from >= 20 to >= 22
- CI workflow: removed `version: 11` from pnpm/action-setup (reads from packageManager field)
- CI workflow: added desktop Vite build step (build:ci, no Tauri/Rust dependency)
- CI workflow: added pip caching for Python dependencies
- Desktop lint script: removed deprecated `--ext` flag
- Desktop build script: added `build:ci` for Vite-only builds in CI
- Lint warnings fixed across 4 files (unused imports removed)

### Fixed
- DuplicateDetector: uses lightweight `get_messages_light` query
- `_classify_and_extract`: extracted as separate method with per-message error handling
- `_parse_response`: marked as `@staticmethod` for clarity
- Unused `cast` import removed from email_service.py

## [0.7.0] — 2026-06-27

### Added
- Premium Pomodoro Timer & Focus Workspace
- Backend: PomodoroSession schema, PomodoroRepository, PomodoroService, API endpoints
- Focus workspace with timer states (focus, break, long_break, idle)
- Session logging with focus/break duration, cycles, date tracking
- Frontend: usePomodoroTimer hook, pomodoro-store, pomodoro-service
- Pomodoro page with animated circular timer, cycle counter, daily stats
- Full-screen focus mode with distraction-free interface
- Configurable durations: focus (25/30/45/60), short break (5/10/15), long break (15/20/30)
- Daily progress tracking (completed cycles, total focus minutes)
- PWA-like behavior with document title and favicon updates
- Keyboard shortcuts: Space (toggle), Escape (quit)
- Study scoring integration: pomodoro sessions earn XP
- Database migration: 20250101000007_pomodoro_enhancements.sql

## [0.8.0] — 2026-06-27

### Added
- AI Document Intelligence — OCR, PDF analysis, document classification
- Backend: DocumentService, OCRService, PDFService, DocumentContextService
- API endpoints: document upload, list, get, delete, OCR, PDF analysis, batch
- Document classification with AI (notes, textbook, slides, handout, exam, other)
- OCR text extraction for images and scanned documents
- PDF text extraction with page-by-page analysis
- Context extraction: topics, formulas, code snippets, diagrams
- Reading session logging with XP tracking
- Frontend: Documents page with file upload, document list, analysis display
- Document store with TanStack Query integration
- Database migration: 20250101000008_document_intelligence.sql

## [0.6.0] — 2026-06-27

### Added
- Study system: XP, streaks, scoring engine, calendar heatmap
- Study scoring: per-activity XP (assignments, pomodoro, AI study, reading, OCR, PDF, quiz, flashcard, revision, email, manual)
- Daily goal bonus: 250 XP when daily goal is met
- Streak tracking with consecutive day calculation
- Calendar heatmap component with color intensity based on XP earned
- Study page with activity log, stats, calendar heatmap
- Study scoring unit tests (20 tests)

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
