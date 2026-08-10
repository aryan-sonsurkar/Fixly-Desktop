# Fixly v1.0.0 — Internal Test Runbook

Build date: 2026-08-10
Installer: `release/Fixly_1.0.0_x64-setup.exe`
SHA-256: `213eb26b905cb5ebd35dcd342dfcabbfaae8bb0a25f4e79ff619f83b9e112c53`

## About this build (what changed vs. previous installers)

1. **Sign-in network fix** — all API calls from the desktop webview are now routed through Rust via `tauri-plugin-http` (bypasses webview CORS entirely). This is the fix for the old "Network Error"/"Invalid password" at sign-in.
2. **Security hardening (big one)** — the `SUPABASE_SERVICE_ROLE_KEY` and `SUPABASE_JWT_SECRET` have been **removed from the shipped bundle**. Anyone who can read the previous installer could extract the service-role key and gain full database admin access. Now:
   - Password reset uses the user's own recovery token (anon key only)
   - Sign-out uses the user's own JWT
   - All queries are scoped to the signed-in user only
3. **IDOR hardening** — attachments/uploads/overdue-marking can no longer touch another user's data.
4. Backend still auto-runs on `127.0.0.1:8000` (random port on conflict) — no Python needed.
5. **Health check fix** — `/api/v1/health` now probes the real `profiles` table instead of a nonexistent `_health` table, so the app's System Diagnostics shows "Database: Connected" instead of a scary red "unable to fetch db" state.
6. **Stale-backend protection** — the app now always launches its backend on a **random free port** instead of fixed 8000. A leftover `backend.exe` from an old session can no longer hijack the app (old symptom: sign-in "Network Error" / wrong-port health failures after a crash or old install).
7. **Real registration errors (fix for "Registration failed. Please try again.")** — the desktop webview's HTTP adapter used to swallow non-2xx HTTP responses, so sign-up failures surfaced as a misleading generic message. Now HTTP error statuses properly reject through axios with the backend's real error body attached, so the UI shows the actual reason (e.g. "An account with this email already exists."). Wrong-password sign-in also shows the real backend message.
8. **Google login is now available** — the "Continue with Google" button on the Sign-in page is enabled. It opens your default browser at Supabase's Google OAuth page (PKCE, no password anywhere); when you finish, the browser returns to the app via the newly registered `fixly://` protocol and you're signed in automatically. The app registers the `fixly://` scheme on your machine at startup (deep-link plugin + single-instance forwarding). **To make Google login work you must enable it in Supabase once** (see below).

## Enabling Google login in Supabase (one-time, by you)

The app and backend are ready; the remaining step is provider config on the Supabase dashboard (needs Google OAuth credentials):

1. **Google Cloud Console** → APIs & Services → OAuth consent screen → **Create OAuth client** → application type **Desktop app** → copy the **Client ID** and **Client secret**.
2. **Supabase dashboard** → Authentication → Providers → **Google**: toggle Enable, paste Client ID/Secret, Save. Confirm the provider appears as enabled under the Auth logins.
3. Under **Authentication → URL Configuration**, add `fixly://auth/callback` to **Additional Redirect URLs** (and `http://localhost:1420/auth/callback` for dev).
4. Restart the app. "Continue with Google" should now complete sign-in/registration with your Google account.

## Test credentials

| Role | Email | Password |
|------|-------|----------|
| Admin (you) | `boyalone28405@gmail.com` | `Aryan@1234` |
| Tester | (create your own accounts in-app via "Create account") | — |

## Critical test checklist (run in this order)

1. **Install**: run `Fixly_1.0.0_x64-setup.exe`. If a previous Fixly version is installed, **uninstall it first** (Start Menu → Fixly → Uninstall), then install fresh.
2. **Sign in** with `boyalone28405@gmail.com` / `Aryan@1234` → should reach the dashboard within a few seconds.
3. **Wrong password test:** enter a wrong password → should now show the backend's real message like "Email or password is incorrect" (NOT a generic fallback).
4. **Create account:** sign out → Create account with a NEW email → must succeed. Then try re-creating the SAME email → should now show "An account with this email already exists."
5. **Sign out → sign back in:** tokens are invalidated server-side; sign-out button must work in every page footer/menu where it appears.
6. **Data isolation smoke test (optional):** upload a file on one account, then confirm a second account cannot see it (attachment list stays empty).
7. **Passwords:** Settings → Change password → use the NEW password to sign back in.
8. **Google login:** (after enabling the provider — see above) Sign in page → "Continue with Google" → browser opens → pick a Google account → app comes back and lands on the dashboard signed in. Also verify the `fixly://` scheme got registered: `reg query HKCU\Software\Classes\fixly\shell\open\command` shows your install path.

## Where to find logs

- Backend log: `%APPDATA%\com.fixly.desktop\backend.log` (created by the app; check this first if something fails)
- App config: `%APPDATA%\com.fixly.desktop\backend\.env` (created on first run — this is where you'd add `GEMINI_API_KEY` etc.)
- Missing things: if the app can't start, look for a crash window; attach `backend.log` with any bug report.

## Security notes (for the internal team)

- The install ships the Supabase **anon** key only. Do NOT add `SUPABASE_SERVICE_ROLE_KEY`/`SUPABASE_JWT_SECRET` to the shipped `.env` — developer-only admin scripts exist in the repo; ask for them if needed (password recovery for test accounts).
- `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` in `.env` are unused: Google OAuth is handled by Supabase's hosted provider flow (credentials live in the Supabase dashboard, never in the app).
- When this goes public (v1.1+): switch `ENVIRONMENT=production` (this flips email-verification and OAuth redirects to production behavior) and enable Supabase RLS + consider per-user storage buckets.

## Known open items (not blocking this test cycle)

- Ollama/Gemini must be configured via `.env` for AI features; not configured = graceful fallbacks.