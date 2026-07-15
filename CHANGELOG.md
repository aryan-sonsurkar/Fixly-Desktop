# Changelog

## v1.0.0-internal.1 (2026-07-15)

### Major Changes
- **Backend Auto-Start**: FastAPI backend now launches automatically when Fixly starts, using Tauri sidecar architecture. No more manual `uvicorn` commands.
- **Startup Screen**: Professional startup sequence with splash animation, progress indicators, and error recovery.
- **Diagnostics Page**: Enhanced system diagnostics with Copy/Export functionality.
- **Windows Installer**: NSIS installer produced for easy distribution (2.8 MB).

### Backend
- Auto-detects Ollama status (installed/running/models)
- Enhanced `/api/v1/health` endpoint with comprehensive system status
- Robust Python process lifecycle management

### Desktop
- Splash screen with animated startup stages
- Backend health check before React app loads
- Graceful backend shutdown on app exit
- Dynamic backend port detection and configuration
- Enhanced diagnostics with Copy and Export buttons
- No terminal windows during normal operation (uses `pythonw` or `CREATE_NO_WINDOW`)

### Provider Architecture
- Ollama-first AI routing (auto-detects local Ollama)
- Fallback to Gemini when Ollama unavailable
- Provider status shown in diagnostics

### Infrastructure
- Backend bundled as resource in installer
- Backend port auto-detection via `FIXLY_PORT` stdout protocol
- Process lifecycle managed by Tauri runtime

### Quality
- TypeScript: 0 errors
- ESLint: 0 errors
- Ruff: All checks passed
- Pytest: 58/58 pass
- Vitest: 41/41 pass
