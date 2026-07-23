# Fixly v1.0.0 - Release Notes

## Overview

Fixly is an AI-powered academic operating system that helps students manage study sessions, assignments, and academic workflow with intelligent scheduling, note-taking, and productivity tools.

## What's New in v1.0.0

### Features
- AI-powered study assistant with Gemini and Ollama support
- Intelligent assignment tracking and deadline management
- Pomodoro timer with session tracking
- Document management with smart search
- Email integration for academic correspondence
- Dashboard with performance analytics and insights
- Study session planning and scoring
- Subject management with progress tracking
- Copilot for real-time academic assistance
- Smart notifications and reminders
- Voice/Text interface for hands-free operation
- Risk detection for at-risk assignments

### Technical Improvements
- **Standalone backend.exe** — No Python installation required
  - Backend packaged with PyInstaller into a single executable
  - Auto-launched by the app — no manual setup needed
  - Falls back to `python -m app.main` if exe not found
- **NSIS Installer** — Easy one-click installation for Windows x64
- Improved startup and health-check process

## Installation

1. Run `Fixly_1.0.0_x64-setup.exe`
2. Follow the installer prompts (installer is per-user)
3. Launch Fixly from the Start Menu or desktop shortcut

## System Requirements

- Windows 10 or later (x64)
- 4GB RAM minimum (8GB recommended)
- 500MB free disk space
- Optional: Ollama for local AI inference
- Optional: Google API key for Gemini integration

## Configuration

Create a `.env` file in the app data directory:
- `%APPDATA%/Fixly/.env`

Required keys (if using cloud features):
- `SUPABASE_URL` — Supabase project URL
- `SUPABASE_ANON_KEY` — Supabase anonymous key
- `GEMINI_API_KEY` — Google Gemini API key (optional if using Ollama)

For local AI (Ollama):
- `OLLAMA_HOST` — defaults to `http://localhost:11434`

## Changelog

### v1.0.0 (2026-07-23)
- Initial public release
- Backend standalone executable (no Python dependency)
- NSIS Windows installer
- All core features implemented
