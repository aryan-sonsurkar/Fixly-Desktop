# Changelog

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
