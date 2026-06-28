# API Reference

Base URL: `http://127.0.0.1:{port}/api/v1`

All endpoints except authentication require a Bearer JWT token in the Authorization header.

## Authentication

### POST /api/v1/auth/signup
Create a new account.

Request: `{ "email": string, "password": string, "full_name"?: string }`
Response: `{ "access_token": string, "refresh_token": string, "user": object }`
Errors: `UNAUTHORIZED` — duplicate email, weak password

### POST /api/v1/auth/signin
Sign in with email and password.

Request: `{ "email": string, "password": string }`
Response: `{ "access_token": string, "refresh_token": string, "user": object }`
Errors: `UNAUTHORIZED` — invalid credentials, email not confirmed

### POST /api/v1/auth/signout
Sign out the current session.

Headers: Authorization: Bearer {token}
Response: `{ "message": string }`

### POST /api/v1/auth/refresh
Refresh an expired access token using a refresh token.

Request: `{ "refresh_token": string }`
Response: `{ "access_token": string, "refresh_token": string, "user": object }`
Errors: `UNAUTHORIZED` — invalid or expired refresh token

### GET /api/v1/auth/me
Get the currently authenticated user profile.

Headers: Authorization: Bearer {token}
Response: `{ "id": string, "email": string, "profile": object | null, "user_metadata": object | null }`

### POST /api/v1/auth/forgot-password
Send a password reset email.

Request: `{ "email": string }`
Response: `{ "message": string }`

### POST /api/v1/auth/reset-password
Reset password using an access token from the reset email.

Request: `{ "access_token": string, "new_password": string }`
Response: `{ "message": string }`
Validation: Password must be at least 8 chars, contain uppercase, lowercase, and a number.

### POST /api/v1/auth/resend-verification
Resend the email verification email.

Request: `{ "email": string }`
Response: `{ "message": string }`

### GET /api/v1/auth/google/url
Get the Google OAuth authorization URL.

Response: `{ "url": string }`

### POST /api/v1/auth/google/callback
Exchange a Google OAuth code for a session.

Request: `{ "code": string, "redirect_uri": string }`
Response: `{ "access_token": string, "refresh_token": string, "user": object }`

## Profile

### GET /api/v1/profile/me
Get the current user's full profile including academic fields.

Headers: Authorization: Bearer {token}
Response: `ProfileResponse`

### PUT /api/v1/profile/me
Update the current user's profile.

Request: `ProfileUpdate` (partial)
Response: `ProfileResponse`

### GET /api/v1/profile/settings
Get the current user's settings.

Headers: Authorization: Bearer {token}
Response: `SettingsResponse`

### PUT /api/v1/profile/settings
Update settings.

Request: `SettingsUpdate` (partial)
Response: `SettingsResponse`

### POST /api/v1/profile/onboarding
Complete the onboarding flow. Saves profile, settings, and initial subjects in one request.

Request: `OnboardingRequest` (profile, settings, subjects[])
Response: `{ "profile": ProfileResponse, "settings": SettingsResponse }`

### GET /api/v1/profile/onboarding/status
Check if the current user has completed onboarding.

Response: `{ "onboarding_completed": boolean }`

## Subjects

### GET /api/v1/subjects
List all subjects for the current user.

Headers: Authorization: Bearer {token}
Response: `Subject[]`

### POST /api/v1/subjects
Create a new subject.

Request: `{ "name": string, "color"?: string, "icon"?: string, "credits"?: number }`
Response: `Subject`

### GET /api/v1/subjects/:id
Get a single subject.

Response: `Subject`

### PUT /api/v1/subjects/:id
Update a subject.

Request: `SubjectUpdate` (partial)
Response: `Subject`

### DELETE /api/v1/subjects/:id
Delete a subject.

Response: `{ "message": string }`

## Dashboard

### GET /api/v1/dashboard
Response: `{ "briefing": string, "upcoming": Assignment[], "schedule": object, "summary": object, "xp": number, "activity": object[] }`

## Assignments

### GET /api/v1/assignments
Query: `?status=pending&subject={id}&priority=high&page=1`
Response: `{ "data": Assignment[], "total": number, "page": number, "page_size": number }`

### POST /api/v1/assignments
Request: `{ "title": string, "description"?: string, "subject_id"?: string, "priority"?: string, "due_date"?: string }`
Response: `{ "assignment": Assignment }`

### GET /api/v1/assignments/:id
Response: `{ "assignment": Assignment, "attachments": Attachment[] }`

### PUT /api/v1/assignments/:id
Request: Partial<Assignment>
Response: `{ "assignment": Assignment }`

### DELETE /api/v1/assignments/:id
Response: `{ "message": string }`

### POST /api/v1/assignments/:id/generate-draft
Response: `{ "ai_draft": string }`

## Subjects

### GET /api/v1/subjects
Response: `{ "subjects": Subject[] }`

### POST /api/v1/subjects
Request: `{ "name": string, "color"?: string }`
Response: `{ "subject": Subject }`

## AI

### POST /api/v1/ai/chat
Send a message and get an AI response. Creates or continues a conversation.

Request: `{ "message": string, "conversation_id"?: string, "stream"?: boolean }`
Response: `{ "message": Message, "conversation": Conversation }`
Status: 503 `AI_UNAVAILABLE` if no provider is reachable

### POST /api/v1/ai/regenerate
Regenerate the last assistant message in a conversation.

Request: `{ "conversation_id": string, "message_id": string }`
Response: `{ "message": Message, "conversation": Conversation }`

### GET /api/v1/ai/conversations
List all conversations for the current user, ordered by most recent.

Response: `Conversation[]`

### POST /api/v1/ai/conversations
Create a new empty conversation.

Request: `{ "title"?: string }`
Response: `Conversation`

### GET /api/v1/ai/conversations/:id
Get a conversation with all its messages.

Response: `{ ...Conversation, messages: Message[] }`

### PUT /api/v1/ai/conversations/:id
Rename a conversation.

Request: `{ "title": string }`
Response: `Conversation`

### DELETE /api/v1/ai/conversations/:id
Delete a conversation and all its messages.

Response: `{ "message": string }`

### GET /api/v1/ai/settings
Get AI settings for the current user.

Response: `{ "preferred_provider": "auto"|"ollama"|"gemini", "temperature": float, "max_tokens": int, "streaming": bool, "system_prompt": string|null, "ollama_available": bool, "gemini_available": bool }`

### PUT /api/v1/ai/settings
Update AI settings.

Request: `AISettingsUpdate` (partial)
Response: `AISettingsResponse`

### GET /api/v1/ai/providers
Check availability of all AI providers.

Response: `{ "ollama": bool, "gemini": bool }`

## Email

### POST /api/v1/email/connect
Response: `{ "auth_url": string }`

### GET /api/v1/email/status
Response: `{ "connected": boolean, "email"?: string, "last_synced"?: string }`

### POST /api/v1/email/sync
Response: `{ "assignments_detected": number, "new_assignments": Assignment[] }`

### DELETE /api/v1/email/disconnect
Response: `{ "message": string }`

## Uploads

### POST /api/v1/upload
Request: Multipart file
Response: `{ "attachment": Attachment }`

### DELETE /api/v1/upload/:id
Response: `{ "message": string }`

## Notifications

### GET /api/v1/notifications
Query: `?read=false&type=assignment_reminder`
Response: `{ "notifications": Notification[] }`

### PUT /api/v1/notifications/:id/read
Response: `{ "notification": Notification }`

### PUT /api/v1/notifications/read-all
Response: `{ "message": string }`

## Study Sessions

### GET /api/v1/study-sessions
Query: `?date=2026-06-26`
Response: `{ "sessions": StudySession[] }`

### POST /api/v1/study-sessions
Request: `{ "subject_id"?: string, "duration_minutes": number }`
Response: `{ "session": StudySession }`

## Pomodoro

### POST /api/v1/pomodoro/complete
Request: `{ "focus_duration": number, "break_duration": number, "cycles_completed": number }`
Response: `{ "session": PomodoroSession }`

### GET /api/v1/pomodoro/history
Query: `?days=7`
Response: `{ "sessions": PomodoroSession[] }`

## Analytics

### GET /api/v1/analytics
Query: `?days=30`
Response: `{ "daily_stats": object[], "total_study": number, "streak": number, "xp": number }`

## Settings

### GET /api/v1/settings
Response: `{ "settings": Settings }`

### PUT /api/v1/settings
Request: Partial<Settings>
Response: `{ "settings": Settings }`

## Error Responses

All errors follow the format:

```json
{
  "error": "Human-readable error message",
  "code": "ERROR_CODE",
  "status": 400
}
```

Common codes:
- `UNAUTHORIZED` — 401
- `NOT_FOUND` — 404
- `VALIDATION_ERROR` — 422
- `AI_UNAVAILABLE` — 503
- `INTERNAL_ERROR` — 500
