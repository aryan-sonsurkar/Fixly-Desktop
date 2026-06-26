# Security

## Architecture

Fixly follows a zero-trust security model:

- **No direct Supabase access from frontend** — all requests go through the Python backend
- **JWT-based authentication** — all API requests require valid tokens
- **Row Level Security** — every database table enforces user-level access control
- **Environment variables** — all secrets are configured via environment, never hardcoded

## Authentication

- Passwords are never stored by Fixly — Supabase Auth handles all credential management
- JWT tokens are never persisted to localStorage (stored in memory only)
- Refresh tokens are stored in Tauri's secure store
- Token expiry is handled automatically with refresh interceptor

## Data Protection

- All API communication uses HTTPS in production
- Database access is restricted to the Python backend service role
- File uploads are stored in Supabase Storage with RLS policies
- Email OAuth tokens are encrypted at rest

## Best Practices

- Never commit `.env` files containing real secrets
- Regularly rotate API keys and tokens
- Use feature flags to gate experimental features
- Run security audits before major releases
- Keep dependencies updated

## Reporting Vulnerabilities

If you discover a security vulnerability, please report it by creating a GitHub issue with the "security" label.

Do not disclose security vulnerabilities in public issues until a fix has been released.
