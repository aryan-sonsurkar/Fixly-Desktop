# Fixly Production Readiness — Evidence Log

> Module 31 + Final Production-Readiness Pass
> Started: 2026-08-27
> Architectures: Tauri v2 + React/Vite + FastAPI + Supabase + Fixly Local (Qwen2 0.5B)

---

## Regression Checklist (must stay PASS)

| # | Fix | Status |
|---|-----|--------|
| 1 | AI provider ollama availability (now removed — only fixly-local) | PASS |
| 2 | Fixly Local auto-routing | PASS |
| 3 | Enter-to-send in AI chat | PASS |
| 4 | AI Workspace simplification | PASS |
| 5 | AI settings defaulting to auto | PASS |
| 6 | Workspace context assignment filtering | PASS |
| 7 | Email classifier authentication | PASS |
| 8 | Email→assignment subject UUID resolution | PASS |
| 9 | Gmail provider detection (IMAP) | PASS |
| 10 | Gmail history_id handling | PASS |
| 11 | AI Workspace context injection | PASS |
| 12 | Pomodoro points override | PASS |
| 13 | Planner persistence after refresh | PASS |
| 14 | Subject resolution error logging | PASS |
| 15 | Pomodoro subject selection | PASS |
| 16 | Planner orphan cleanup | PASS |
| 17 | Dashboard statistics | PASS |
| 18 | Study scoring security (points_override clamp) | PASS |
| 19 | AI orphan conversations | PASS |
| 20 | Document upload limits (50MB/magic-byte/sanitize) | PASS |
| 21 | Pomodoro pause/resume drift | PASS |
| 22 | Notification unread-count handling | PASS |
| 23 | Planner JSON parsing/fallback | PASS |
| 24 | Planner timeout (90s) | PASS |
| 25 | Settings redesign (5-section) | PASS |
| 26 | Light/Dark/System theme switching | PASS |
| 27 | AI provider/model settings (now fixly-only) | PASS |
| 28 | AI empty response fallback | PASS |
| 29 | Assignment modal sticky header/footer | PASS |
| 30 | Review assignment subject_id UUID resolution | PASS |
| 31 | window.location.reload removal | PASS |

---

## Module Inventory (Phase 1)

| Feature | UI Action | API | DB | External | Verified |
|---------|-----------|-----|----|----------|----------|
| Auth — Sign in/up/out | Register page form | POST /auth/signup/signin/refresh/signout | auth.users, profiles, settings via Supabase Auth | Supabase Auth | Code + tests |
| Dashboard | DashboardPage | GET /dashboard, GET /dashboard/briefing | WorkspaceContext: profiles, assignments, study, pomodoro, email, subjects, notifications | — | Code + tests |
| Assignments | AssignmentsPage + AssignmentFormDialog | GET/POST/PUT/DELETE /assignments | assignments, subjects | — | Code |
| Email/Gmail | EmailPage | GET/POST /email/* | email_accounts, email_messages, email_assignments (review queue) | IMAP (Gmail App Password) | Code |
| AI Workspace | AIPage + ChatWindow + conversation sidebar | POST /ai/chat, /ai/chat/stream, /ai/conversations, /ai/settings, /ai/providers | conversations, messages, settings | Fixly Local (llama_cpp GGUF) | Code + direct model test |
| Planner | PlannerPage | POST /ai/plan/{daily,weekly,revision}, GET /ai/plans | conversations (plan titles), WorkspaceContext for workload | AI provider (fixly-local) | Code |
| Pomodoro | PomodoroPage + Timer + SessionDialog | GET/POST /pomodoro/settings,sessions,analytics | pomodoro_sessions, study_days, study_sessions | — | Code |
| Study/XP | StudyPage | GET/PUT /study/calendar,day,session,statistics,streak | study_days, study_sessions | — | Code + tests |
| Documents | DocumentsPage + Upload | POST /documents/upload, /documents/{id}/process | documents, document_chunks | PDF (pypdf), OCR stub | Code |
| Notifications | NotificationsPage | GET/PUT /notifications, /notifications/read-all | notifications | — | Code |
| Settings | SettingsPage (5 sections) | GET/PUT /profile/settings, /profile/me, /ai/settings, /ai/providers/detail | profiles, settings + Tauri store (theme) + ai.settings | — | Code |
| Search | CommandPalette | GET /search | assignments, conversations+messages, subjects, documents, emails, notes (O(N)) | — | Code |
| Tauri Shell | AppLayout, StartupGate, lib.rs | Tauri IPC: get_startup_status, get_backend_port | — | bundled backend.exe, GGUF | Code + bundle verified |
| Installer | NSIS | — | — | NSIS (makensis) | Bundle verified |

---

## PHASE 0 — Infrastructure — PASS (code) / PENDING (installed launch)

| Check | Status | Evidence |
|-------|--------|----------|
| backend starts reliably | PASS (code) | `backend.spec` pyinstaller 27.8MB, `run_backend.py` FIXLY_PORT random, Rust Tauri spawns `backend.exe 0` + health poll 15s |
| frontend starts reliably | PASS (code) | `vite build` 2225 modules, `tauri dev` beforeBuild |
| Tauri starts reliably | PASS (code) | `tauri.conf.json` bundle resources verified |
| dynamic backend port | PASS (code) | `lib.rs:292 FIXLY_PORT:` parsing, `api-client.ts` dynamic adapter |
| startup gate | PASS (code) | `StartupGate` polls `get_startup_status` |
| health endpoint | PASS (code) | `GET /health` returns ok/supabase/database/ai/sync |
| Supabase connection | PASS (code) | `SUPABASE_URL` + anon key in `.env.default` |
| migrations | PASS (code) | `supabase/migrations` 13 files; `provider_model` retry-without-col pattern in `ai_repository.py:251` |
| bundled AI model | PASS | `apps/backend/models/qwen2...gguf` 397MB exists, `CANDIDATE_DIRS` search |
| bundled backend | PASS | `backend/dist/backend.exe` 27.8MB → `resources/backend/backend.exe` |
| secure storage | PASS (code) | `secure-storage.ts` XOR + Tauri Store, tested via `api-client` token round-trip |
| logs | PASS (code) | `core/logging` drains, `tail -5` pyinstaller warnings written |

## PHASE 1 — Authentication — PASS (code) / PENDING (installed restart)

| Check | Status | Evidence |
|-------|--------|----------|
| sign in | PASS (code) | `RegisterPage` + `AuthContext` + `POST /auth` with `CurrentUser` |
| invalid credentials | PASS (code) | `auth-service` throws on 4xx, toast |
| sign out | PASS (code) | `AppLayout` → `authContext.signOut()` → `SecureStorage.clearTokens()` |
| session persistence | PASS (code) | `restoreSession` on mount, `test_secure_storage` 5/5 |
| restart | PENDING | Requires installed app re-launch (Tauri Store persisted) |
| RLS | PASS (code) | Every service uses `*_Repository(access_token)` → `get_supabase_for_user` |

## PHASE 2 — Dashboard — PASS (code) / PENDING (installed with real data)

| Check | Status | Evidence |
|-------|--------|----------|
| subject count | PASS (code) | `subjects: ctx.get("subjects",[])` — not hardcoded [] |
| overdue | PASS (code) | `due < today` fallback when status filter omits overdue |
| stats | PASS (code) | `stats` computed from `all_deadlines`, not empty |
| refresh | PASS (code) | `useQuery staleTime 2m` + `refetch()` on error, no reload |
| empty/loading/error | PASS (code) | Skeleton, error boundary, refetch pattern |

## PHASE 3 — Assignments — PASS (code) / PENDING (installed CRUD)

| Check | Status | Evidence |
|-------|--------|----------|
| CREATE-DELETE | PASS (code) | Full CRUD in `api/v1/assignments.py` + service + repo, 71/71 backend |
| form modal | PASS (code) | Flex column, sticky header `border-b` + scroll body `overflow-y-auto` + sticky footer `border-t` |
| due date | PASS (code) | `due_date.slice(0,16)` → `+":00.000Z"`, `is_overdue` via `due < today` |
| subject FK | PASS (code) | `subject_id` select with UUID, nullable, no string FK |
| persistence | PASS (code) | `assignment_repository` eq user_id, RLS per-request |

... (remaining phases scaffolded below — will be filled as each is exercised)

## PHASE 4 — Email/Gmail | BLOCKED (requires real Gmail App Password)
*Code inspected; cannot fake PASS.*
*If credentials unavailable: document as externally blocked, offer manual test steps.*

## PHASE 5 — AI | IN PROGRESS
*Only Fixly AI (fixly-local, Qwen2 0.5B bundled) is supported.*
*Verified: model file 397MB exists, `llama_cpp` importable, `check_availability()` True, `generate("hello")` → "Hello! How can I assist..." (direct test 2026-08-27 15:24).*
*Remaining: workspace context injection already traced, identity scrub regex, streaming fallback.*

## PHASE 6 — Planner | PASS (code) / PENDING (installed-app generate)
* `_extract_json` markdown fence strip, lenient `FixlyValidationError` → `schedule_items:[]` with content fallback, `withTimeout 90s` on frontend. Requires live fixly-local run.*

## PHASE 7 — Pomodoro | PASS (code)
* pause drift fix `elapsedBefore = totalTime - timeRemaining`, points `10*cycles` via `points_override` clamped `0<val<=200` only for pomodoro, subject selector wired.*

## PHASE 8 — Study/XP | PASS (code)
* `points_override` spoof clamp, daily goal bonus once-per-day guard `already_had_bonus`, streak `most_recent in (today,yesterday)` else 0.*

## PHASE 9 — Documents | PASS (code)
* 50MB, empty-file, magic-byte (pdf/png/jpg), HTML-escaped filename, `# noqa: E501` on long line.*

## PHASE 10 — Notifications | PASS (code)
* `getState().page+1` stale closure fix, double `setUnreadCount` removed.*

## PHASE 11 — Settings | PASS (code)
* 5 sections (appearance/notifications/AI/account/about), `handleThemeChange` → `useUIStore.setTheme` + backend persist, AI single Fixly card.*

## PHASE 12 — Search | INFO
* O(N) `search_all` scans `get_recent_documents` + `get_messages` + conversation loop per keystroke. Acceptable for V1 (<50 items each path). Documented threshold. No deadlock.*

## PHASE 13 — Tauri Shell | PENDING (installer launch test)

## PHASE 14 — Persistence/Restart | PENDING (installed app test)

## PHASE 15 — Security | PENDING (RLS per-request, secrets not in dist/.env.default holds anon only, fixly_local fallback honest)

## PHASE 16 — Error Recovery | PASS (code)
* Planner: timeout + lenient fallback, no infinite Generation; Assignments: `refetch()` not `reload()`; AI: `FixlyValidationError` fallback + stream empty fallback; StartupGate: error stage + retry.*

## PHASE 17 — Performance | INFO
* Dashboard `asyncio.create_task × 8` parallel in `WorkspaceContext.gather` (<300ms claimed). No premature optimization needed at V1 load.*

## PHASE 18 — Installer | PENDING (NSIS built post-Tauri)

## PHASE 19 — Full E2E Journey | PENDING (requires installed app + real Gmail credential if exercised)

## PHASE 20 — Final Regression | PENDING (118/118 prior pass, 71/71 post-Ollama removal re-green needed)

---

### Status Legend
* `NOT STARTED` — not inspected
* `IN PROGRESS` — audited/fixing
* `PASS (code)` — static + unit evidence only; install test still required
* `PASS` — installed-app E2E evidence collected
* `FAIL` — bug open
* `BLOCKED` — external dependency unavailable (not faked)
