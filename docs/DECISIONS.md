# Architecture Decision Records

## ADR-001: Use Tauri instead of Electron

**Status:** Accepted
**Date:** 2026-06-26

### Context
Fixly is a desktop application targeting Windows, macOS, and Linux. The framework must be lightweight, secure, and support native OS features for a premium student experience.

### Decision
Use Tauri v2 as the desktop framework.

### Alternatives Considered
- **Electron**: Larger bundle (150MB+), higher memory usage, slower startup. Overkill for a focused academic tool.
- **Neutralino**: Less mature ecosystem, limited plugin support for native features.
- **NW.js**: Smaller community, less actively maintained.

### Consequences
- **Positive**: ~10MB installer vs 150MB+ with Electron. Rust enables high-performance native plugins.
- **Positive**: Tauri v2 supports mobile targets, enabling future platform expansion without rewriting.
- **Positive**: Lower memory footprint suited for student laptops with limited RAM.
- **Negative**: Requires Rust knowledge for native plugin development.
- **Negative**: Smaller ecosystem — some libraries need manual integration.

---

## ADR-002: Use FastAPI instead of Flask

**Status:** Accepted
**Date:** 2026-06-26

### Context
The Python backend needs to handle AI inference requests, file processing, and real-time communication. It must be performant, well-documented, and easy to maintain.

### Decision
Use FastAPI as the Python web framework.

### Alternatives Considered
- **Flask**: Synchronous by default, requires additional libraries for async, validation, and documentation.
- **Django**: Too opinionated and heavy for a focused API backend.
- **Starlette**: Lower-level; FastAPI builds on it with built-in validation and docs.

### Consequences
- **Positive**: Async-native — ideal for AI request handling and I/O-bound operations.
- **Positive**: Automatic OpenAPI documentation (useful for frontend-backend contract).
- **Positive**: Pydantic integration means validation is built into the framework.
- **Negative**: Slightly steeper learning curve than Flask for new contributors.

---

## ADR-003: Cloud-first architecture using Supabase

**Status:** Accepted
**Date:** 2026-06-26

### Context
Fixly needs user authentication, a relational database, file storage, and real-time capabilities. Managing these independently would increase complexity.

### Decision
Use Supabase as the primary cloud platform.

### Alternatives Considered
- **Firebase**: Proprietary, weak relational support, vendor lock-in.
- **Self-hosted PostgreSQL + S3 + Redis**: More control but significant operational overhead.
- **AWS Amplify**: Complex configuration, less suited for Python backend.

### Consequences
- **Positive**: One platform for auth, database, storage, and real-time.
- **Positive**: Open-source with self-hosting option for future needs.
- **Positive**: PostgreSQL gives us proper relational data modeling.
- **Negative**: Real-time features depend on Supabase Realtime availability.

---

## ADR-004: Repository Pattern

**Status:** Accepted
**Date:** 2026-06-26

### Context
Services currently depend directly on Supabase SDK. This makes testing difficult and couples business logic to the database implementation.

### Decision
Introduce a repository layer between services and Supabase.

### Architecture
```
Service → Repository → Supabase
```

### Consequences
- **Positive**: Data access is abstracted — Supabase can be replaced without changing services.
- **Positive**: Repositories can be mocked for unit testing services.
- **Positive**: Database queries are centralized and reusable.
- **Negative**: Additional layer means more code for simple CRUD operations.

---

## ADR-005: Service Layer Architecture

**Status:** Accepted
**Date:** 2026-06-26

### Context
Route handlers were becoming complex with business logic mixed into request/response handling. This made testing difficult and violated single responsibility.

### Decision
Separate business logic into service modules.

### Architecture
```
Route Handler → Service → Repository
```

### Consequences
- **Positive**: Route handlers are thin and focused on HTTP concerns.
- **Positive**: Business logic is reusable across different entry points (API, workers, CLI).
- **Positive**: Services can be tested independently of HTTP.
- **Positive**: Clear separation of concerns improves maintainability.

---

## ADR-006: AI Provider Abstraction (Ollama → Gemini → Future)

**Status:** Accepted
**Date:** 2026-06-26

### Context
Fixly uses AI for multiple features (chat, code generation, analysis). Relying on a single provider creates a dependency risk and limits flexibility.

### Decision
Create an abstract AI service that routes requests through a provider chain with fallback.

### Provider Chain
1. Ollama (primary, local)
2. Gemini (secondary, cloud)
3. Future providers (OpenRouter, Groq, Claude, BYOK)

### Consequences
- **Positive**: No single point of failure — fallback if primary provider is unavailable.
- **Positive**: Frontend never knows which provider generated the response.
- **Positive**: Students can use local Ollama for free or cloud providers for more power.
- **Negative**: Abstracting provider differences adds implementation complexity.

---

## ADR-007: Tauri Sidecar Architecture

**Status:** Accepted
**Date:** 2026-06-26

### Context
The Python backend needs to run alongside the desktop application. In development, they run separately. In production, they need to be bundled together.

### Decision
Use Tauri's sidecar mechanism to bundle and launch the Python backend in production.

### Architecture
- **Development**: Backend runs independently via Uvicorn. Frontend connects via VITE_API_URL.
- **Production**: Tauri bundles the Python binary (compiled with PyInstaller) as a sidecar.
- **Port management**: Backend binds to port 0 (random available), prints port to stdout. Tauri reads and exposes via IPC.

### Consequences
- **Positive**: No hardcoded ports in production — fully dynamic.
- **Positive**: Users don't need Python installed — the backend is bundled.
- **Positive**: Same backend code runs in development and production.
- **Negative**: Sidecar adds complexity to the build pipeline.
- **Negative**: Python bundling with PyInstaller increases installer size (~30-50MB).

---

## ADR-008: Monorepo using pnpm Workspaces + Turborepo

**Status:** Accepted
**Date:** 2026-06-26

### Context
Fixly has multiple applications (Desktop, Web, Mobile future) and shared packages (UI, types, utils). Managing them independently creates versioning and duplication issues.

### Decision
Use a pnpm workspaces monorepo with Turborepo for build orchestration.

### Structure
```
apps/       — Desktop, Backend (future: Web, Mobile)
packages/   — UI components, shared types, utilities, configs
```

### Alternatives Considered
- **Nx**: More powerful but heavier configuration for our needs.
- **Lerna**: Legacy tool, less efficient caching than Turborepo.
- **Separate repos**: Version drift, duplicate code, harder cross-repo changes.

### Consequences
- **Positive**: Shared packages are versioned together with consumers.
- **Positive**: Turborepo caches builds — zero-repeat work for unchanged packages.
- **Positive**: Single `pnpm install` for all dependencies.
- **Positive**: Consistent tooling (TypeScript, ESLint, Prettier) across the project.
- **Negative**: Root-level dependency conflicts need careful management.
- **Negative**: CI needs to handle both Node.js and Python toolchains.
