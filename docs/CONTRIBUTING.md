# Contributing

## Development Setup

### Prerequisites
- Node.js >= 20
- pnpm >= 9
- Python >= 3.12
- Rust (latest stable)
- Supabase account (free tier)

### Clone and Install

```bash
git clone https://github.com/aryan-sonsurkar/Fixly-Desktop.git
cd Fixly-Desktop

# Install Node.js dependencies
pnpm install

# Set up Python virtual environment
cd apps/backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements-dev.txt
```

### Environment Variables

Copy `.env.example` to `.env` and fill in the required values.

### Start Development

```bash
# Start both backend and desktop
pnpm dev

# Or start individually:
pnpm dev:backend   # Python server on port 8000
pnpm dev:desktop   # Tauri + Vite on port 1420
```

## Project Structure

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full project structure.

## Making Changes

1. Create a feature branch: `git checkout -b feat/your-feature`
2. Make your changes following the coding standards
3. Write tests for new functionality
4. Run linting and type checking
5. Create a pull request

## Pull Request Process

1. Ensure all linting and tests pass
2. Update documentation if needed
3. Update CHANGELOG.md with your changes
4. Request review from the team
5. Squash commits before merging

## Code Review Guidelines

- Check for adherence to coding standards
- Verify error handling is centralized
- Ensure no direct Supabase calls from frontend
- Confirm feature flags are used for experimental features
- Verify all new code has tests
