# Coding Standards

## General Rules

- All code must be in English
- No `print()` or `console.log()` in production code — use the structured logging system
- All errors must go through the global error handling system
- No hardcoded secrets, ports, or URLs
- Follow the single responsibility principle
- Write tests for all business logic

## TypeScript / React

### Naming
- **Files**: kebab-case for utilities, PascalCase for components
- **Components**: PascalCase
- **Functions**: camelCase
- **Constants**: UPPER_SNAKE_CASE
- **Types/Interfaces**: PascalCase
- **Hooks**: `use` prefix (camelCase)

### Conventions
- Use TypeScript strict mode
- Prefer interfaces over types for object shapes
- Use `type` for unions, intersections, and mapped types
- Use functional components with hooks (no class components except ErrorBoundary)
- Define props interface for every component
- Use React.memo only when profiling shows benefit
- Import types with `import type { ... }` syntax

### State Management
- Client state → Zustand stores
- Server state → TanStack Query
- Form state → React Hook Form
- Avoid prop drilling beyond 2 levels

### Styling
- Use Tailwind CSS utility classes
- Use `cn()` from shared-utils for conditional classes
- Use shadcn/ui components from packages/ui
- Define custom styles in globals.css using Tailwind directives

## Python

### Naming
- **Files**: snake_case
- **Classes**: PascalCase
- **Functions/Methods**: snake_case
- **Constants**: UPPER_SNAKE_CASE
- **Private methods**: `_` prefix

### Conventions
- Type hints required for all function signatures
- Use Pydantic for all data validation
- Use dependency injection for services
- Services receive repositories via constructor
- No business logic in route handlers
- Use async/await for I/O operations

### Project Structure
- API layer: thin route handlers
- Service layer: business logic
- Repository layer: data access (Supabase queries)
- Models: Pydantic data models
- Schemas: Pydantic request/response validation

## Git

### Branch Naming
- `feat/description` — new features
- `fix/description` — bug fixes
- `chore/description` — maintenance
- `docs/description` — documentation

### Commit Messages
Follow Conventional Commits:
```
feat: add assignment creation endpoint
fix: resolve auth token refresh race condition
chore: update dependencies
docs: add API documentation for email endpoints
```

### Pull Requests
- Title matches Conventional Commits format
- Description explains what and why
- Reference related issues

## Testing

### Frontend (Vitest)
- Test components in isolation
- Use testing-library for user-centric tests
- Mock API calls at the service layer
- Test error states and loading states

### Backend (Pytest)
- Test API endpoints via TestClient
- Test services with mocked repositories
- Test repositories with test Supabase instance
- Use fixtures for common setup
