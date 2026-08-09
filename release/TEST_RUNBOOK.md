# Fixly v1.0.0 — Internal Test Runbook

Build date: 2026-08-09
Installer: `release/Fixly_1.0.0_x64-setup.exe`
SHA-256: `686b1be23a2682f2c5bf8ff0ef5f1d86bfca3dbc0e930918869d990bfc7c445e`

## About this build (what changed vs. previous installers)

1. **Sign-in network fix** — all API calls from the desktop webview are now routed through Rust via `tauri-plugin-http` (bypasses webview CORS entirely). This is the fix for the old "Network Error"/"Invalid password" at sign-in.
2. **Security hardening (big one)** — the `SUPABASE_SERVICE_ROLE_KEY` and `SUPABASE_JWT_SECRET` have been **removed from the shipped bundle**. Anyone who can read the previous installer could extract the service-role key and gain full database admin access. Now:
   - Password reset uses the user's own recovery token (anon key only)
   - Sign-out uses the user's own JWT
   - All queries are scoped to the signed-in user only
3. **IDOR hardening** — attachments/uploads/overdue-marking can no longer touch another user's data.
4. Backend still auto-runs on `127.0.0.1:8000` (random port on conflict) — no Python needed.

## Test credentials

| Role | Email | Password |
|------|-------|----------|
| Admin (you) | `boyalone28405@gmail.com` | `Aryan@1234` |
| Tester | (create your own accounts in-app via "Create account") | — |

## Critical test checklist (run in this order)

1. **Install**: run `Fixly_1.0.0_x64-setup.exe`. If a previous Fixly version is installed, **uninstall it first** (Start Menu → Fixly → Uninstall), then install fresh.
2. **Sign in** with `boyalone28405@gmail.com` / `Aryan@1234` → should reach the dashboard within a few seconds.
3. **Wrong password test:** enter a wrong password → should show "Invalid credentials" error, app must NOT crash or white-screen.
4. **Create account:** sign out → Create account with a new email → sign in with it.
5. **Sign out → sign back in:** tokens are invalidated server-side; sign-out button must work in every page footer/menu where it appears.
6. **Data isolation smoke test (optional):** upload a file on one account, then confirm a second account cannot see it (attachment list stays empty).
7. **Passwords:** Settings → Change password → use the NEW password to sign back in.

## Where to find logs

- Backend log: `%APPDATA%\com.fixly.desktop\backend.log` (created by the app; check this first if something fails)
- App config: `%APPDATA%\com.fixly.desktop\backend\.env` (created on first run — this is where you'd add `GEMINI_API_KEY` etc.)
- Missing things: if the app can't start, look for a crash window; attach `backend.log` with any bug report.

## Security notes (for the internal team)

- The install ships the Supabase **anon** key only. Do NOT add `SUPABASE_SERVICE_ROLE_KEY`/`SUPABASE_JWT_SECRET` to the shipped `.env` — developer-only admin scripts exist in the repo; ask for them if needed (password recovery for test accounts).
- When this goes public (v1.1+): switch `ENVIRONMENT=production` (this flips email-verification and OAuth redirects to production behavior), wire Google OAuth, and enable Supabase RLS + consider per-user storage buckets.

## Known open items (not blocking this test cycle)

- `/api/v1/health` reports `supabase: disconnected` until the health-check table is created — cosmetic only; core features still work.
- Attachments upload requires an assignment to exist first (ownership-verified now).
- Ollama/Gemini must be configured via `.env` for AI features; not configured = graceful fallbacks.