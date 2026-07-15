# Known Issues — v1.0.0-internal.1

## Blocker (P0)
1. **MSI Installer unavailable** — WiX Toolset v3 not installed; only NSIS installer is built.

## High (P1)
2. **Python prerequisite** — Users must install Python 3.11+ manually. The installer does not bundle Python.
3. **Backend `.env` not bundled** — Users must create `.env` in the backend directory with Supabase credentials.
4. **No auto-update mechanism** — Users must manually download and install new versions.

## Medium (P2)
5. **Deep link disabled** — `tauri-plugin-deep-link` is not configured; OAuth callback flow uses polling fallback.
6. **Backend development mode** — Backend runs without `--reload`; code changes require app restart.
7. **No tray/minimize-to-system-tray** — App closes entirely when window is closed.
8. **No auto-launch at system startup** — App must be launched manually.

## Low (P3)
9. **Ollama not auto-installed** — Users must install Ollama separately for local AI.
10. **Startup screen not skippable** — No "Skip" button during backend startup (intentional for reliability).
11. **Diagnostics page read-only** — No "Fix" actions available; diagnostics are informational only.
12. **Console window may flash on some systems** — `pythonw` fallback may briefly show a console window.
