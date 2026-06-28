# Database Schema

All tables use Row Level Security (RLS). The `profiles` table references `auth.users` which is managed by Supabase Auth.

## Tables

### profiles
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, references auth.users(id) |
| email | TEXT | NOT NULL |
| full_name | TEXT | nullable |
| display_name | TEXT | nullable |
| avatar_url | TEXT | nullable |
| education_type | TEXT | nullable |
| education_year | TEXT | nullable |
| college_name | TEXT | nullable |
| university_board | TEXT | nullable |
| branch_stream | TEXT | nullable |
| division | TEXT | nullable |
| roll_number | TEXT | nullable |
| onboarding_completed | BOOLEAN | DEFAULT false |
| xp | INTEGER | DEFAULT 0 |
| streak | INTEGER | DEFAULT 0 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() |

### settings
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| user_id | UUID | FK, NOT NULL, references profiles(id) |
| theme | TEXT | DEFAULT 'dark' |
| daily_goal_hours | INTEGER | DEFAULT 0 |
| pomodoro_focus | INTEGER | DEFAULT 25 |
| pomodoro_break | INTEGER | DEFAULT 5 |
| notification_enabled | BOOLEAN | DEFAULT true |
| assignment_reminders | BOOLEAN | DEFAULT true |
| daily_briefing | BOOLEAN | DEFAULT true |
| email_monitoring | BOOLEAN | DEFAULT false |
| email_sync_enabled | BOOLEAN | DEFAULT false |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() |

### subjects
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| user_id | UUID | FK, NOT NULL, references profiles(id) |
| name | TEXT | NOT NULL |
| color | TEXT | nullable |
| icon | TEXT | nullable |
| credits | INTEGER | nullable |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |

### assignments
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| user_id | UUID | FK, NOT NULL, references profiles(id) |
| subject_id | UUID | FK, nullable, references subjects(id) |
| title | TEXT | NOT NULL |
| description | TEXT | nullable |
| status | TEXT | DEFAULT 'pending' |
| priority | TEXT | DEFAULT 'medium' |
| due_date | TIMESTAMPTZ | nullable |
| source | TEXT | DEFAULT 'manual' |
| source_email_id | TEXT | nullable |
| ai_draft | TEXT | nullable |
| ai_draft_generated | BOOLEAN | DEFAULT false |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() |

### attachments
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| assignment_id | UUID | FK, NOT NULL, references assignments(id) ON DELETE CASCADE |
| user_id | UUID | FK, NOT NULL, references profiles(id) |
| file_name | TEXT | NOT NULL |
| file_type | TEXT | nullable |
| file_size | INTEGER | nullable |
| storage_path | TEXT | NOT NULL |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |

### notifications
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| user_id | UUID | FK, NOT NULL, references profiles(id) |
| title | TEXT | NOT NULL |
| message | TEXT | nullable |
| type | TEXT | NOT NULL |
| read | BOOLEAN | DEFAULT false |
| metadata | JSONB | nullable |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |

### study_sessions
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| user_id | UUID | FK, NOT NULL, references profiles(id) |
| subject_id | UUID | FK, nullable, references subjects(id) |
| duration_minutes | INTEGER | NOT NULL |
| started_at | TIMESTAMPTZ | NOT NULL |
| ended_at | TIMESTAMPTZ | nullable |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |

### pomodoro_sessions
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| user_id | UUID | FK, NOT NULL, references profiles(id) |
| focus_duration | INTEGER | NOT NULL |
| break_duration | INTEGER | NOT NULL |
| cycles_completed | INTEGER | DEFAULT 0 |
| total_focus_minutes | INTEGER | DEFAULT 0 |
| date | DATE | DEFAULT CURRENT_DATE |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |

### conversations
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| user_id | UUID | FK, NOT NULL, references profiles(id) ON DELETE CASCADE |
| title | TEXT | DEFAULT 'New conversation' |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() |

### messages
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| conversation_id | UUID | FK, NOT NULL, references conversations(id) ON DELETE CASCADE |
| user_id | UUID | FK, NOT NULL, references profiles(id) |
| role | TEXT | NOT NULL, CHECK (role IN ('user', 'assistant', 'system')) |
| content | TEXT | NOT NULL |
| provider | TEXT | nullable |
| tokens | INTEGER | nullable |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |

### email_accounts
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| user_id | UUID | FK, NOT NULL, references profiles(id) |
| email | TEXT | NOT NULL |
| provider | TEXT | DEFAULT 'gmail' |
| access_token | TEXT | nullable (encrypted) |
| refresh_token | TEXT | nullable (encrypted) |
| token_expires_at | TIMESTAMPTZ | nullable |
| sync_enabled | BOOLEAN | DEFAULT true |
| sync_status | TEXT | DEFAULT 'idle', CHECK (idle, syncing, error, paused) |
| sync_error | TEXT | nullable |
| total_emails | INTEGER | DEFAULT 0 |
| last_message_id | TEXT | nullable |
| last_synced_at | TIMESTAMPTZ | nullable |
| daily_briefing_enabled | BOOLEAN | DEFAULT true |
| briefing_time | TEXT | DEFAULT '08:00' |
| auto_create_assignments | BOOLEAN | DEFAULT false |
| confidence_threshold | REAL | DEFAULT 0.70 |
| attachment_download | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() |

### email_messages
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| user_id | UUID | FK, NOT NULL, references auth.users(id) ON DELETE CASCADE |
| account_id | UUID | FK, NOT NULL, references email_accounts(id) ON DELETE CASCADE |
| message_id | TEXT | NOT NULL |
| thread_id | TEXT | nullable |
| subject | TEXT | DEFAULT '' |
| from_name | TEXT | nullable |
| from_email | TEXT | NOT NULL |
| to_emails | TEXT[] | DEFAULT '{}' |
| cc_emails | TEXT[] | DEFAULT '{}' |
| body_text | TEXT | nullable |
| body_html | TEXT | nullable |
| received_at | TIMESTAMPTZ | NOT NULL |
| is_read | BOOLEAN | DEFAULT false |
| is_starred | BOOLEAN | DEFAULT false |
| has_attachments | BOOLEAN | DEFAULT false |
| labels | TEXT[] | DEFAULT '{}' |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| UNIQUE(user_id, message_id) | | |

### email_classifications
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| email_id | UUID | FK, NOT NULL, references email_messages(id) ON DELETE CASCADE |
| user_id | UUID | FK, NOT NULL, references auth.users(id) |
| category | TEXT | NOT NULL, CHECK (assignment, exam, project, notice, holiday, event, general, spam) |
| confidence | REAL | NOT NULL DEFAULT 0 |
| is_reviewed | BOOLEAN | DEFAULT false |
| user_feedback | TEXT | nullable |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| UNIQUE(email_id) | | |

### email_assignments
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| email_id | UUID | FK, NOT NULL, references email_messages(id) ON DELETE CASCADE |
| user_id | UUID | FK, NOT NULL, references auth.users(id) |
| subject | TEXT | nullable |
| title | TEXT | nullable |
| due_date | TIMESTAMPTZ | nullable |
| priority | TEXT | DEFAULT 'medium', CHECK (low, medium, high, urgent) |
| teacher_name | TEXT | nullable |
| description | TEXT | nullable |
| course | TEXT | nullable |
| confidence | REAL | NOT NULL DEFAULT 0 |
| status | TEXT | DEFAULT 'pending', CHECK (pending, approved, edited, rejected, converted) |
| assignment_id | UUID | nullable |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| UNIQUE(email_id) | | |

### email_attachments
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| email_id | UUID | FK, NOT NULL, references email_messages(id) ON DELETE CASCADE |
| document_id | UUID | FK, nullable, references documents(id) ON DELETE SET NULL |
| user_id | UUID | FK, NOT NULL, references auth.users(id) |
| filename | TEXT | NOT NULL |
| file_type | TEXT | nullable |
| file_size | INTEGER | DEFAULT 0 |
| storage_path | TEXT | nullable |
| processed | BOOLEAN | DEFAULT false |
| created_at | TIMESTAMPTZ | DEFAULT NOW()

### analytics
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| user_id | UUID | FK, NOT NULL, references profiles(id) |
| date | DATE | DEFAULT CURRENT_DATE |
| total_study_minutes | INTEGER | DEFAULT 0 |
| assignments_completed | INTEGER | DEFAULT 0 |
| pomodoro_cycles | INTEGER | DEFAULT 0 |
| xp_earned | INTEGER | DEFAULT 0 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| UNIQUE(user_id, date) | | |

## Relationships

- `profiles.id` → `auth.users.id` (via trigger on signup)
- `settings.user_id` → `profiles.id` (1:1)
- `subjects.user_id` → `profiles.id` (1:N)
- `assignments.user_id` → `profiles.id` (1:N)
- `assignments.subject_id` → `subjects.id` (N:1)
- `attachments.assignment_id` → `assignments.id` (N:1, cascade delete)
- `notifications.user_id` → `profiles.id` (1:N)
- `study_sessions.user_id` → `profiles.id` (1:N)
- `pomodoro_sessions.user_id` → `profiles.id` (1:N)
- `conversations.user_id` → `profiles.id` (1:N)
- `messages.conversation_id` → `conversations.id` (N:1, cascade delete)
- `messages.user_id` → `profiles.id` (1:N)
- `email_accounts.user_id` → `profiles.id` (1:N)
- `email_messages.user_id` → `profiles.id` (1:N)
- `email_messages.account_id` → `email_accounts.id` (N:1, cascade delete)
- `email_classifications.email_id` → `email_messages.id` (1:1, cascade delete)
- `email_assignments.email_id` → `email_messages.id` (1:1, cascade delete)
- `email_attachments.email_id` → `email_messages.id` (N:1, cascade delete)
- `email_attachments.document_id` → `documents.id` (N:1, set null on delete)
- `analytics.user_id` → `profiles.id` (1:N)

## RLS Policies

Every table has RLS enabled with policies that restrict row access to the owning user.
