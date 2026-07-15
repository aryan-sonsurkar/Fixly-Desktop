# Fixly v1.0.0-internal.1 — Internal Testing Guide

## Setup
1. Install Python 3.11+ from https://python.org
2. Install Ollama from https://ollama.ai (optional, for local AI)
3. Run the Fixly installer
4. Copy `.env` file with Supabase credentials to the backend directory
5. Launch Fixly

## Test Checklist

### Core Flow
- [ ] App launches without errors
- [ ] Startup screen appears with progress indicators
- [ ] Backend starts automatically (check for `FIXLY_PORT:XXXXX` in logs)
- [ ] Login or register successfully
- [ ] Dashboard loads with correct data
- [ ] Navigate between all pages via sidebar

### Backend Auto-Start
- [ ] Backend starts within 30 seconds of launch
- [ ] Port is dynamically assigned and detected
- [ ] Frontend waits for backend health check before loading
- [ ] Closing app kills backend process (check Task Manager)
- [ ] No Python terminal window visible during operation

### Diagnostics
- [ ] Diagnostics page shows all system status
- [ ] Backend status shows "healthy" with correct port
- [ ] Supabase status shows connectivity
- [ ] Ollama status (if installed)
- [ ] "Copy Diagnostics" copies formatted text to clipboard
- [ ] "Export Diagnostics" downloads a `.txt` file

### Features
- [ ] Assignments: Create, edit, delete
- [ ] Subjects: Manage subjects
- [ ] AI Workspace: Chat with AI (Ollama preferred, Gemini fallback)
- [ ] Pomodoro Timer: Start, pause, complete session
- [ ] Documents: Upload and view
- [ ] Email: Connect and view
- [ ] Planner: Create and manage tasks
- [ ] Study: Track study sessions
- [ ] Notifications: View notification center
- [ ] Search: Use Ctrl+K command palette

### Error Scenarios
- [ ] Kill backend process manually → App detects and shows error
- [ ] Start app without Python → Shows "Python not found" error with retry
- [ ] Start app without backend files → Shows appropriate error
- [ ] Network disconnected → Proper error messages

### Install/Uninstall
- [ ] Installer creates Start Menu shortcut
- [ ] Installer creates desktop shortcut (optional)
- [ ] Uninstall removes all app files
- [ ] Uninstall does NOT remove backend `.env` or user data

### Performance
- [ ] App launches within 30 seconds (cold start)
- [ ] UI is responsive after load
- [ ] Memory usage stays below 500 MB
- [ ] CPU usage idles below 5%

## Reporting Issues
Report bugs with:
1. Copy Diagnostics output
2. Steps to reproduce
3. Expected vs actual behavior
4. Screenshots if applicable
