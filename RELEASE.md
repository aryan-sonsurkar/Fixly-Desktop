# Fixly Release Process

## Versioning Strategy

| Component | Source of Truth | Frequency |
|-----------|----------------|-----------|
| Desktop app | `apps/desktop/src-tauri/tauri.conf.json` | Per release |
| Backend | `apps/backend/pyproject.toml` | Per release |
| Frontend | `apps/desktop/package.json` | Per release |
| Monorepo | `package.json` | Per release |
| Rust crate | `apps/desktop/src-tauri/Cargo.toml` | Per release |

**Scheme**: `MAJOR.MINOR.PATCH` (semver)
- `1.0.0` — First public beta
- Bump PATCH for bugfixes
- Bump MINOR for features
- Bump MAJOR for breaking changes

## Release Process

1. **Freeze**: No feature commits to `main` without release branch
2. **Version bump**: Update all 5 version sources to match
3. **CHANGELOG**: Write entries under `Unreleased` heading
4. **QA**:
   - `ruff check app/` — zero warnings
   - `mypy app/` — zero errors
   - `pnpm exec eslint src/` — zero errors
   - `pnpm exec tsc --noEmit` — zero errors
   - `pnpm --filter @fixly/desktop build:ci` — passes
   - `pytest tests/ -v` — all pass
   - `pnpm exec vitest run` — all pass
5. **Commit**: `chore(release): v{version}`
6. **Tag**: `git tag v{version}`
7. **Push**: `git push origin main --tags`
8. **GitHub Release**: Triggered by tag → `release.yml` workflow
   - Builds NSIS (.exe), MSI (.msi), portable (.exe)
   - Uploads artifacts
   - Creates draft release

## Changelog Generation

File: `CHANGELOG.md`

Format:
```
# Changelog

## [1.0.0] — 2026-07-02

### Added
- New features

### Changed
- Updates

### Fixed
- Bug fixes

### Security
- Security patches
```

Use `git log --oneline --no-decorate v{prev}..HEAD` to collect changes between tags.

## Installer Naming Convention

| Type | Format | Example |
|------|--------|---------|
| NSIS | `Fixly_{version}_{arch}_Setup.exe` | `Fixly_1.0.0_x64_Setup.exe` |
| MSI | `Fixly_{version}_{arch}.msi` | `Fixly_1.0.0_x64.msi` |
| Portable | `Fixly_{version}_{arch}.exe` | `Fixly_1.0.0_x64.exe` |

## GitHub Releases

- **Draft** created by `release.yml` on tag push
- Title: `Fixly {version}`
- Contents: changelog entry + checksums + download links
- Manual publish after smoke-testing the installer
