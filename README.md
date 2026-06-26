# Fixly

Fixly is an AI-powered academic operating system designed to become the single workspace every student needs throughout their academic journey.

Instead of switching between Gmail, Notes, WhatsApp, Calendar, AI chatbots, task managers and productivity apps, Fixly brings everything into one intelligent platform.

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Desktop | Tauri v2 |
| Frontend | React, TypeScript, Tailwind CSS, shadcn/ui |
| State | Zustand, TanStack Query |
| Backend | Python, FastAPI, Uvicorn |
| Cloud | Supabase (Auth, PostgreSQL, Storage, Realtime) |
| AI | Ollama (primary), Gemini (fallback) |
| Monorepo | pnpm workspaces, Turborepo |

## Quick Start

### Prerequisites

- Node.js >= 20
- pnpm >= 9
- Python >= 3.12
- Rust (latest stable)
- Supabase account (free tier)

### Setup

```bash
# Install dependencies
pnpm install

# Set up Python virtual environment
cd apps/backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements-dev.txt

# Start development
pnpm dev
```

## Project Structure

```
Fixly/
├── apps/
│   ├── desktop/          # Tauri v2 desktop application
│   └── backend/          # Python FastAPI backend
├── packages/
│   ├── ui/               # Shared UI component library
│   ├── shared-types/     # TypeScript type definitions
│   ├── shared-utils/     # Shared utility functions
│   └── config/           # ESLint, Prettier, TypeScript configs
├── docs/                 # Documentation
└── .github/              # GitHub Actions workflows
```

## Architecture

Fixly follows a strict layered architecture:

```
React Frontend → Axios → FastAPI → Services → Repositories → Supabase
```

The frontend never communicates with Supabase directly. All requests go through the Python backend service layer.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Product Vision](docs/PRODUCT.md)
- [Roadmap](docs/ROADMAP.md)
- [Database Schema](docs/DATABASE.md)
- [API Reference](docs/API.md)
- [Coding Standards](docs/CODING_STANDARDS.md)
- [Contributing Guide](docs/CONTRIBUTING.md)
- [Changelog](docs/CHANGELOG.md)
- [Security](docs/SECURITY.md)
- [Architecture Decisions](docs/DECISIONS.md)

## License

MIT License — see [LICENSE](LICENSE) for details.
