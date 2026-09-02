# Fixly Release & Update Process

> **Source repository: PRIVATE** — only the compiled installer, signed updater artifacts, and public updater metadata are distributed. Users never receive source, Actions internals, or private keys.

---

## Versioning

Single authoritative source: **Git tags** `v*` (e.g. `v1.0.1`). Tag push triggers `release.yml`.

Version is stored in three places and must stay synchronized. Before tagging, update all three atomically in one commit:

| File | Field | Example |
|------|-------|---------|
| `apps/desktop/package.json` | `version` | `"1.0.0"` |
| `apps/desktop/src-tauri/Cargo.toml` | `version` | `1.0.0` |
| `apps/desktop/src-tauri/tauri.conf.json` | `version` | `"1.0.0"` |

Helper (PowerShell):

```powershell
$V="1.0.1"
# package.json
(Get-Content apps/desktop/package.json) -replace '"version": ".*"', "`"version`": `"$V`"" | Set-Content apps/desktop/package.json
# Cargo.toml
(Get-Content apps/desktop/src-tauri/Cargo.toml) -replace 'version = ".*"', 'version = "$V"' | Set-Content apps/desktop/src-tauri/Cargo.toml
# tauri.conf.json
$j = Get-Content apps/desktop/src-tauri/tauri.conf.json | ConvertFrom-Json
$j.version = $V
$j | ConvertTo-Json -Depth 10 | Set-Content apps/desktop/src-tauri/tauri.conf.json
git add -A; git commit -m "release: v$V"; git tag v$V; git push origin main --tags
```

---

## Required GitHub Secrets

| Secret | Value | Notes |
|--------|-------|-------|
| `TAURI_SIGNING_PRIVATE_KEY` | Content of `fixly-updater.key` (minisign secret key) | Generate via `npx @tauri-apps/cli signer generate -w <path>` — **never commit** |
| `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` | Password if key was generated with `-p` | Empty if key has no password |

Also accepted legacy names (fallback in workflow): `TAURI_PRIVATE_KEY` → `TAURI_SIGNING_PRIVATE_KEY`, `TAURI_KEY_PASSWORD` → password.

The **public key** (`fixly-updater.key.pub`) is already embedded in `tauri.conf.json` under `plugins.updater.pubkey`. It is safe to ship.

To rotate: generate a new keypair, replace `pubkey` in `tauri.conf.json`, rotate the secret, and cut a new release. Old installs will see signature mismatch on the first post-rotation update — users must reinstall the fresh installer.

---

## What GitHub Actions Builds (`release.yml` on `v*`)

1. **Checkout** private repo (via `GITHUB_TOKEN`, no repo access leak to artifacts).
2. **Quality gates** (fail-fast):
   - Frontend: `lint`, `typecheck`, `vitest`, `vite build`
   - Backend: `ruff check app/`, `mypy app/`, `pytest tests/ -v`
   - Rust: `cargo check`
3. **Backend** (`apps/backend`): `pip install pyinstaller && pyinstaller backend.spec --noconfirm` → `apps/backend/dist/backend.exe` (+ `backend/models/*.gguf` already in repo/resources)
4. **Tauri** (`apps/desktop/src-tauri`): `pnpm --filter @fixly/desktop build` → `vite build` + `cargo tauri build` with `TAURI_SIGNING_PRIVATE_KEY` env → generates:
   - `target/release/bundle/nsis/Fixly_*_x64-setup.exe` (current-user, `passive` update mode)
   - `target/release/bundle/nsis/Fixly_*_x64-setup.nsis.zip` + `.sig` (updater artifact)
   - `target/release/bundle/latest.json` (updater metadata, `v1Compatible`)
   - `target/release/bundle/msi/*.msi` (optional, per `tauri.conf` targets)
5. **Security scan**: Python script fails the job if any `.json`/`.sig` contains `TAURI_SIGNING_PRIVATE_KEY`, `PRIVATE KEY`, or `supabase_service_role` literal.
6. **Artifacts uploaded** as `Fixly-Setup-x64`, `Fixly-MSI-x64`, `Fixly-Portable-x64`, `Fixly-Updater`.
7. **Release job** downloads all four, generates notes + checksums, creates a **draft** GitHub Release `vX.Y.Z` with: `*.exe`, `*.msi`, `fixly-desktop.exe`, `latest.json`, `*.sig`, `*.zip`.
8. **No source archive suppression needed** — release assets are only `files:` listed above; source zip/tar are GitHub defaults but not distributed to beta via updater.

---

## Updater Metadata

Tauri v2 updater JSON (`latest.json`, `v1Compatible`):

```json
{
  "version": "1.0.1",
  "notes": "Bug fixes",
  "pub_date": "2026-09-01T15:00:00Z",
  "platforms": {
    "windows-x86_64": {
      "signature": "... Contents of .nsis.zip.sig ...",
      "url": "https://github.com/aryan-sonsurkar/Fixly-Desktop/releases/download/v1.0.1/Fixly_1.0.1_x64-setup.nsis.zip"
    }
  }
}
```

`pub_date` is build time. `signature` is the **actual `.sig` file content**, not a path. Tauri verifies it against the `pubkey` in the installed app before installing.

---

## Signing

* Keypair: `minisign` Ed25519 via `tauri signer generate`. Private key signs the updater `.zip`; public key is baked into the binary at compile time (`tauri.conf.json`).
* The private key is **never** in source, `.env`, frontend bundle, release asset, logs, or installer resources. Only in `TAURI_SIGNING_PRIVATE_KEY` secret.
* Workflow fails if `signing fails` (Tauri will error if `TAURI_SIGNING_PRIVATE_KEY` present but `.sig` not produced).
* Local dev (`cargo tauri build` without `TAURI_SIGNING_PRIVATE_KEY`) still builds NSIS/MSI but produces **unsigned** updater artifacts — local updater checks will return `up_to_date` or soft error; never corrupt the install.

---

## Private Repository Distribution — Why `Fixly-Desktop/releases` Works Only for Collaborators

**GitHub private repo releases are private.** `https://github.com/aryan-sonsurkar/Fixly-Desktop/releases/latest/download/latest.json` requires `Authorization: token with repo scope`. Ordinary beta users without repo access see `404`.

**Chosen architecture for V1 (simplest secure):**

* **Private source repo** `Fixly-Desktop` stays private.
* **Public update distribution** via a second **public** repository `aryan-sonsurkar/Fixly-Updates` (source-free, only holds `latest.json` + signed `.zip` + `.sig` per release) **or** via a public bucket on the Fixly website (`https://fixly.co.in/updates/latest.json` backed by Supabase Storage / Vercel static).
* **Release workflow** adds a final step (manual or Action `gh api` / `aws s3 cp`) that mirrors `latest.json` + artifacts from the private draft release to the public endpoint. Until that mirror is configured, **beta users must be GitHub collaborators** to receive updates via the private endpoint. The updater degrades gracefully: offline / 404 / private 404 are handled as soft `up_to_date` or `error` state with "Will retry next launch" — no crash, no data loss.

**Why this architecture:**

* No source, no Actions logs, no secrets ever in the public repo — only `latest.json`, `.zip`, `.sig` (all public by nature).
* Tauri's official static-JSON updater is used verbatim — no custom protocol.
* Switching distribution mid-stream is a one-line `tauri.conf.json` `endpoints` change + one secret (`FIXLY_UPDATES_PAT` or `R2_*`) — no code change.

**To enable public beta without repo access (owner action, one time):**

1. Create public repo `github.com/aryan-sonsurkar/Fixly-Updates` (empty, no source).
2. Create a fine-grained PAT with `contents:write` on that repo, save as `FIXLY_UPDATES_PAT` in `Fixly-Desktop` Secrets.
3. Add a final job step in `release.yml` that after `softprops/action-gh-release` uploads to the private draft, also `gh release create vX.Y.Z --repo aryan-sonsurkar/Fixly-Updates dist/updater/latest.json dist/updater/*.zip dist/updater/*.sig` (or `supabase storage cp` / `aws s3` to the website bucket).
4. Change `tauri.conf.json` `plugins.updater.endpoints` to `https://github.com/aryan-sonsurkar/Fixly-Updates/releases/latest/download/latest.json` (or `https://fixly.co.in/updates/latest.json`) and ship in the next installer.

Until step 2-4 are done, local development and collaborator installs update correctly via the private endpoint; public beta is documented as "repo access required."

---

## How Beta Users Receive Updates

1. Fixly launches → `StartupGate` waits for backend `ready` → `useUpdater` waits 8s → `check()` from `@tauri-apps/plugin-updater` fetches `endpoints[0]` (`latest.json`) in background.
2. If `update.version > installed version`, a subtle banner appears below the header: **"Fixly 1.0.1 is available — Update now / Later"** (deferred if Pomodoro running, assignment editing, document upload, or AI streaming).
3. **Update now** → `update.downloadAndInstall()` streams progress, verifies Ed25519 `signature` against baked `pubkey`, stages the NSIS `passive` update. Download progress shows `%` and `MB`.
4. Banner becomes **"Update 1.0.1 downloaded — restart Fixly to apply."** User restarts (or banner's Restart button) → Tauri relaunch → version shows `1.0.1` in About/Diagnostics, all user data intact (Supabase-sourced, not on disk).

No restart is forced during active work.

---

## How to Test an Update Locally (no secrets needed)

```powershell
# 1. Build & install 1.0.0
pnpm --filter @fixly/desktop build:ci
pyinstaller backend.spec --noconfirm   # in apps/backend
cargo tauri build                       # in src-tauri → release/Fixly_1.0.0_x64-setup.exe
# Install, create an account, add a subject/assignment, generate a plan

# 2. Bump version everywhere to 1.0.1 (see Versioning section above)
# ... edit package.json, Cargo.toml, tauri.conf.json ...

# 3. Build 1.0.1 similarly — inspect target/release/bundle/latest.json
# Without TAURI_SIGNING_PRIVATE_KEY, latest.json will exist but signature will be empty — updater check will soft-fail; unit test the banner with a mock latest.json via a local http server.

# 4. With TAURI_SIGNING_PRIVATE_KEY set (export TAURI_SIGNING_PRIVATE_KEY=(Get-Content $env:APPDATA\fixly\updater.key)):
#    cargo tauri build  # now produces signed .zip + .sig + latest.json with real signature

# 5. Tests remain green without secrets:
pnpm --filter @fixly/desktop test; npx tsc --noEmit
# backend: pytest, ruff, mypy
cargo check
```

---

## How to Revoke/Rotate Signing Keys

1. `npx @tauri-apps/cli signer generate -w $env:APPDATA\fixly\rotated.key` (with password).
2. Replace `plugins.updater.pubkey` in `tauri.conf.json` with new public key.
3. Rotate secret: delete old `TAURI_SIGNING_PRIVATE_KEY` in GitHub Settings → Secrets, add new private key.
4. Cut a new release — old installs will see `signature invalid` on the first post-rotation check and fall back to `error` banner with "Will retry"; they must reinstall the new installer once. To avoid this, keep the old key active for one transition release if possible.

---

## What Beta Users Receive (and do not receive)

| Public | Private (never shipped) |
|--------|------------------------|
| NSIS/MSI installer | Source code |
| Signed `.nsis.zip` + `.sig` | `TAURI_SIGNING_PRIVATE_KEY` |
| `latest.json` updater metadata | GitHub Actions internals |
| Public `updater.pubkey` (in binary) | Supabase service-role key |
| Release notes, checksums | JWT secret, Gmail credentials |

---

## Checklist for a Release

- [ ] Bump `1.0.0 → 1.0.1` in `package.json`, `Cargo.toml`, `tauri.conf.json` + commit
- [ ] `git tag v1.0.1 && git push origin v1.0.1` (triggers `release.yml`)
- [ ] Watch Actions: quality gates → backend → `cargo tauri build` → secret scan PASS
- [ ] Approve draft release, verify artifacts: `Fixly_*_x64-setup.exe`, `latest.json`, `.nsis.zip` + `.sig`
- [ ] (If public beta) Mirror `latest.json` + signed zip to `Fixly-Updates` public repo / Fixly website bucket
- [ ] Test: install `1.0.0`, add data, trigger update to `1.0.1`, verify download+signature+restart+data persistence
- [ ] Verify `beta_waitlist` untouched (`SELECT count(*) FROM beta_waitlist` unchanged)
