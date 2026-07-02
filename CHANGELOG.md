# Changelog

## [1.0.0] — 2026-07-02

### Added
- Production desktop configuration: NSIS/MSI targets, installer icons, license, metadata
- GitHub Actions release workflow for automated Windows installer builds
- Release process documentation and naming conventions
- Production-quality application icons (32x32, 128x128, 256x256, 512x512 PNG + ICO)
- Skip-to-content link and ARIA labels for accessibility
- Keyboard shortcuts (g-navigation, Escape, Ctrl+K)
- 404 route for undefined paths
- Error boundary with retry button and expandable error details
- Code splitting (vendor, motion, query, forms, UI chunks)
- `longDescription` and proper `license` fields in bundle config

### Changed
- Version bumped from 0.1.0 to 1.0.0 across all config files
- Tauri CSP from `null` to strict allowlist (`default-src 'self'`)
- Publisher from "Fixly" to "Aryan Sonsurkar"
- Copyright to standard format with year and holder
- Cargo.toml: added homepage, repository, license fields

### Fixed
- Backend type errors (mypy): 21 → 0 errors across 4 service files
- Backend lint warnings (ruff): 8 → 0 E501 line-length warnings
- TypeScript errors: 2 → 0 (Theme type, risk-alerts-widget string indexing)
- `workspace_context.py`: replaced nonexistent `get_sessions(days=)` with `get_sessions_range()`
- `workspace_context.py` + `search_service.py` + `dashboard_service.py`: replaced `list_documents(limit=)` with `get_recent_documents()`
- Supabase type ignore annotations for `.single()` and `.select(count=)`
- `register.tsx`: replaced `document.getElementById` with `watch("password")`
- `dashboard.tsx`: replaced silent catch with production logging

### Security
- Removed unrestricted `shell:allow-execute` capability
- Set Content Security Policy (was null before v1.2.0 polishing)

## [0.1.0] — 2026-06-26

### Added
- Initial pre-release version
- Tauri v2 desktop shell with React frontend
- FastAPI backend with 77 API routes
- Supabase integration (auth, database, storage)
- AI copilot features (chat, study assistant, risk detection)
- Academic workflow management (assignments, subjects, study sessions)
- Pomodoro timer, email monitoring, document management
