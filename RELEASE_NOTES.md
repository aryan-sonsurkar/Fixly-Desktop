# Fixly v1.0.0-internal.1 — Internal Beta Release

## Overview
Fixly is an AI-powered academic operating system that helps students manage study sessions, assignments, and academic workflow with intelligent scheduling, note-taking, and productivity tools.

## What's New
- **One-click launch** — Backend starts automatically; no manual setup required
- **Professional startup** — Splash screen with progress indicators
- **System diagnostics** — Comprehensive health checks with copy/export
- **Windows installer** — Easy NSIS-based setup

## Prerequisites
- **Python 3.11+** installed and available in PATH
- **Ollama** (optional) for local AI inference
- Supabase project configured via `.env` in the backend directory

## Installation
1. Run `Fixly_1.0.0_x64-setup.exe`
2. Follow the installer prompts
3. Launch Fixly from the Start Menu or desktop shortcut

## First Launch
1. The app will show a splash screen
2. Backend starts automatically (may take 5-15 seconds)
3. Login or create an account
4. Complete onboarding

## Testing Focus
- Backend auto-start reliability
- Startup screen flow and error handling
- Diagnostics page accuracy
- Cross-feature integration (dashboard, AI, assignments, etc.)
- Install/uninstall experience

## Known Issues
See KNOWN_ISSUES.md for the complete list.
