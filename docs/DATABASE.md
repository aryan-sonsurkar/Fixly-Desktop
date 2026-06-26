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

### ai_history
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK, DEFAULT gen_random_uuid() |
| user_id | UUID | FK, NOT NULL, references profiles(id) |
| role | TEXT | NOT NULL |
| content | TEXT | NOT NULL |
| model | TEXT | nullable |
| tokens_used | INTEGER | nullable |
| context_type | TEXT | nullable |
| metadata | JSONB | nullable |
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
| last_synced_at | TIMESTAMPTZ | nullable |
| created_at | TIMESTAMPTZ | DEFAULT NOW() |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() |

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
- `ai_history.user_id` → `profiles.id` (1:N)
- `email_accounts.user_id` → `profiles.id` (1:N)
- `analytics.user_id` → `profiles.id` (1:N)

## RLS Policies

Every table has RLS enabled with policies that restrict row access to the owning user.
