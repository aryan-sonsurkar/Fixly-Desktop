# Fixly v1.0.0 — Release Candidate

## Release metadata

| Field | Value |
|---|---|
| Version | 1.0.0 (Release Candidate) |
| Commit | `68e5257` (`fix(backend): honor --env-file before config load`) |
| Installer | `release/Fixly_1.0.0_x64-setup.exe` |
| SHA-256 | `e97af6bca5240f24f23373a3ffe060ef01ca71fb8e99cb29124d82b648a2783e` |
| Build date | 2026-08-19 |
| Platform | Windows 10+ (x64) |
| Launch date | Product Hunt, 22 August 2026 |

## Overview

Fixly is an AI-powered academic operating system that helps students manage study sessions, assignments, and academic workflow with intelligent scheduling, note-taking, and productivity tools.

## Features

- AI-powered study assistant (Copilot, planner, insights, risk detection)
- Assignment tracking and deadline management
- Pomodoro timer with session tracking and analytics
- Document management with real PDF text extraction and AI chat
- Email integration for academic correspondence
- Dashboard with performance analytics and insights
- Study session planning, scoring, and streaks
- Subject management with progress tracking
- Smart notifications and reminders
- Global search across notes and conversations
- Google sign-in via Supabase OAuth (`fixly://` deep link)

## Installation

1. Download `Fixly_1.0.0_x64-setup.exe` (SHA-256 above; verify before running).
2. Run the installer and follow the prompts (per-user install, no admin required).
3. Launch Fixly from the Start Menu or desktop shortcut.
4. Create an account with name + email (no password required). On first launch the app auto-starts its bundled backend.

Uninstall: Start Menu → Fixly → Uninstall.

## System requirements

- Windows 10 or later (x64)
- 4GB RAM minimum (8GB recommended)
- 500MB free disk space

## Ollama requirements

Ollama is optional and used for local AI inference when no Gemini key is configured:

- Install Ollama from https://ollama.com
- `OLLAMA_HOST` defaults to `http://localhost:11434` (set in the app's `.env` to override)
- The backend detects installed Ollama models at runtime; AI features gracefully fall back when no provider is available.

## AI provider configuration

AI features are configured via the app's environment file, created on first run at:

- `%APPDATA%\com.fixly.desktop\backend\.env`

Supported keys:

| Key | Purpose | Required? |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API key (cloud inference) | Only if not using Ollama |
| `OLLAMA_HOST` | Local Ollama endpoint (default `http://localhost:11434`) | Optional |
| `SUPABASE_URL` | Supabase project URL (shipped by default) | No |
| `SUPABASE_ANON_KEY` | Supabase anonymous key (shipped by default) | No |

Provider priority: Gemini (if a valid key is present) → Ollama (if a model is available). If neither is available, AI features return a clean error instead of failing silently.

In-app AI Settings can also select a provider and model.

## Security notes

- The installer ships the Supabase **anon** key and project URL only — these are client-safe (all access is scoped per-user by RLS).
- **Never** add `SUPABASE_SERVICE_ROLE_KEY` or `SUPABASE_JWT_SECRET` to the shipped `.env` (admin-only, developer machines).
- The bundled backend and desktop executables were scanned before release: no private credentials present.
- Environment is `production` in the shipped bundle (email verification off, OAuth + verify-email redirect to the `fixly://` deep link).

## Known P2/P3 issues (tracked, not launch-blocking)

1. **Synchronous Supabase client on the event loop** — most services call Supabase synchronously from async handlers (only `ai_repository` offloads via `run_in_thread`). A blocked network call can briefly stall the event loop. (P2, planned: async client migration)
2. **Sequential email AI classification** — multiple email messages are AI-classified one at a time; large mailboxes are slower than a batched approach. (P3)
3. **Unsigned installer** — no code-signing certificate; Windows SmartScreen will show an "unknown publisher" warning on first run. (P3, "More info → Run anyway")
4. **`ENVIRONMENT` semantics** — production mode returns a session immediately at signup (email confirmation disabled in this Supabase project). If email confirmation is ever enabled, `ENVIRONMENT` behavior should be revisited. (P3)

## Known limitations

- Windows x64 only (no macOS/Linux builds in this release).
- Google login requires the provider to be enabled in the Supabase dashboard (App Auth → Google) with `fixly://auth/callback` added as a redirect URL.
- AI features require Gemini or Ollama configuration; without either, AI interactions return a clean "provider unavailable" message.
- Voice/text interface requires a working provider configuration.

## Changelog

### v1.0.0 (RC)
- Standalone `backend.exe` (PyInstaller, no Python dependency) auto-launched by the app on a random free port
- NSIS per-user installer
- Real PDF text extraction (pypdf) with honest OCR fallback messaging
- "Fixly AI" persona enforcement; AI fail-fast when no provider is configured
- Hardened invalid-input handling (no 500s on malformed UUIDs/dates)
- Shipped environment set to `production`; secret-free bundle verified by scan
- Search N+1 eliminated (bulk message fetch)
- Full mypy/ruff/test quality gates green (58/58 tests)