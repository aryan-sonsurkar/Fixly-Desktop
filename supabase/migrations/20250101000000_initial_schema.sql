-- Migration: 20250101000000_initial_schema
-- Description: Initial schema for Fixly - all tables, triggers, RLS, and policies

-- ============================================
-- UTILITY FUNCTIONS
-- ============================================

-- Trigger function to auto-update updated_at
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

-- ============================================
-- TABLES
-- ============================================

-- 1. profiles
create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    email text not null,
    full_name text,
    avatar_url text,
    xp integer not null default 0,
    streak integer not null default 0,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- 2. settings
create table if not exists public.settings (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.profiles(id) on delete cascade,
    theme text not null default 'dark',
    pomodoro_focus integer not null default 25,
    pomodoro_break integer not null default 5,
    notification_enabled boolean not null default true,
    email_sync_enabled boolean not null default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint unique_user_settings unique (user_id)
);

-- 3. subjects
create table if not exists public.subjects (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.profiles(id) on delete cascade,
    name text not null,
    color text,
    created_at timestamptz not null default now()
);

-- 4. assignments
create table if not exists public.assignments (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.profiles(id) on delete cascade,
    subject_id uuid references public.subjects(id) on delete set null,
    title text not null,
    description text,
    status text not null default 'pending',
    priority text not null default 'medium',
    due_date timestamptz,
    source text not null default 'manual',
    source_email_id text,
    ai_draft text,
    ai_draft_generated boolean not null default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint valid_status check (status in ('pending', 'in_progress', 'completed', 'cancelled')),
    constraint valid_priority check (priority in ('low', 'medium', 'high', 'urgent')),
    constraint valid_source check (source in ('manual', 'email', 'ai'))
);

-- 5. attachments
create table if not exists public.attachments (
    id uuid primary key default gen_random_uuid(),
    assignment_id uuid not null references public.assignments(id) on delete cascade,
    user_id uuid not null references public.profiles(id) on delete cascade,
    file_name text not null,
    file_type text,
    file_size integer,
    storage_path text not null,
    created_at timestamptz not null default now()
);

-- 6. notifications
create table if not exists public.notifications (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.profiles(id) on delete cascade,
    title text not null,
    message text,
    type text not null,
    read boolean not null default false,
    metadata jsonb,
    created_at timestamptz not null default now(),
    constraint valid_notification_type check (type in ('info', 'success', 'warning', 'error', 'reminder'))
);

-- 7. study_sessions
create table if not exists public.study_sessions (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.profiles(id) on delete cascade,
    subject_id uuid references public.subjects(id) on delete set null,
    duration_minutes integer not null,
    started_at timestamptz not null,
    ended_at timestamptz,
    created_at timestamptz not null default now()
);

-- 8. pomodoro_sessions
create table if not exists public.pomodoro_sessions (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.profiles(id) on delete cascade,
    focus_duration integer not null,
    break_duration integer not null,
    cycles_completed integer not null default 0,
    total_focus_minutes integer not null default 0,
    date date not null default current_date,
    created_at timestamptz not null default now()
);

-- 9. ai_history
create table if not exists public.ai_history (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.profiles(id) on delete cascade,
    role text not null,
    content text not null,
    model text,
    tokens_used integer,
    context_type text,
    metadata jsonb,
    created_at timestamptz not null default now(),
    constraint valid_role check (role in ('user', 'assistant', 'system'))
);

-- 10. email_accounts
create table if not exists public.email_accounts (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.profiles(id) on delete cascade,
    email text not null,
    provider text not null default 'gmail',
    access_token text,
    refresh_token text,
    token_expires_at timestamptz,
    sync_enabled boolean not null default true,
    last_synced_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint valid_provider check (provider in ('gmail', 'outlook', 'icloud', 'other'))
);

-- 11. analytics
create table if not exists public.analytics (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.profiles(id) on delete cascade,
    date date not null default current_date,
    total_study_minutes integer not null default 0,
    assignments_completed integer not null default 0,
    pomodoro_cycles integer not null default 0,
    xp_earned integer not null default 0,
    created_at timestamptz not null default now(),
    constraint unique_user_date unique (user_id, date)
);

-- ============================================
-- TRIGGERS (updated_at)
-- ============================================

create trigger set_profiles_updated_at
    before update on public.profiles
    for each row
    execute function public.set_updated_at();

create trigger set_settings_updated_at
    before update on public.settings
    for each row
    execute function public.set_updated_at();

create trigger set_assignments_updated_at
    before update on public.assignments
    for each row
    execute function public.set_updated_at();

create trigger set_email_accounts_updated_at
    before update on public.email_accounts
    for each row
    execute function public.set_updated_at();

-- ============================================
-- AUTO-PROFILE CREATION ON SIGNUP
-- ============================================

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
    insert into public.profiles (id, email, full_name, avatar_url)
    values (
        new.id,
        new.email,
        new.raw_user_meta_data ->> 'full_name',
        new.raw_user_meta_data ->> 'avatar_url'
    );

    insert into public.settings (user_id)
    values (new.id);

    return new;
end;
$$;

create or replace trigger on_auth_user_created
    after insert on auth.users
    for each row
    execute function public.handle_new_user();

-- ============================================
-- INDEXES
-- ============================================

create index if not exists idx_profiles_email on public.profiles(email);
create index if not exists idx_settings_user_id on public.settings(user_id);
create index if not exists idx_subjects_user_id on public.subjects(user_id);
create index if not exists idx_assignments_user_id on public.assignments(user_id);
create index if not exists idx_assignments_subject_id on public.assignments(subject_id);
create index if not exists idx_assignments_status on public.assignments(status);
create index if not exists idx_assignments_due_date on public.assignments(due_date);
create index if not exists idx_attachments_assignment_id on public.attachments(assignment_id);
create index if not exists idx_attachments_user_id on public.attachments(user_id);
create index if not exists idx_notifications_user_id on public.notifications(user_id);
create index if not exists idx_notifications_read on public.notifications(read);
create index if not exists idx_study_sessions_user_id on public.study_sessions(user_id);
create index if not exists idx_study_sessions_subject_id on public.study_sessions(subject_id);
create index if not exists idx_pomodoro_sessions_user_id on public.pomodoro_sessions(user_id);
create index if not exists idx_pomodoro_sessions_date on public.pomodoro_sessions(date);
create index if not exists idx_ai_history_user_id on public.ai_history(user_id);
create index if not exists idx_ai_history_created_at on public.ai_history(created_at);
create index if not exists idx_email_accounts_user_id on public.email_accounts(user_id);
create index if not exists idx_analytics_user_id on public.analytics(user_id);
create index if not exists idx_analytics_date on public.analytics(date);

-- ============================================
-- ROW LEVEL SECURITY
-- ============================================

-- Enable RLS on all tables
alter table public.profiles enable row level security;
alter table public.settings enable row level security;
alter table public.subjects enable row level security;
alter table public.assignments enable row level security;
alter table public.attachments enable row level security;
alter table public.notifications enable row level security;
alter table public.study_sessions enable row level security;
alter table public.pomodoro_sessions enable row level security;
alter table public.ai_history enable row level security;
alter table public.email_accounts enable row level security;
alter table public.analytics enable row level security;

-- ============================================
-- RLS POLICIES
-- ============================================

-- Profiles: users can read/update their own profile
create policy "Users can view own profile"
    on public.profiles for select
    using (auth.uid() = id);

create policy "Users can update own profile"
    on public.profiles for update
    using (auth.uid() = id);

-- Settings: users can CRUD their own settings
create policy "Users can view own settings"
    on public.settings for select
    using (auth.uid() = user_id);

create policy "Users can insert own settings"
    on public.settings for insert
    with check (auth.uid() = user_id);

create policy "Users can update own settings"
    on public.settings for update
    using (auth.uid() = user_id);

create policy "Users can delete own settings"
    on public.settings for delete
    using (auth.uid() = user_id);

-- Subjects: users can CRUD their own subjects
create policy "Users can view own subjects"
    on public.subjects for select
    using (auth.uid() = user_id);

create policy "Users can insert own subjects"
    on public.subjects for insert
    with check (auth.uid() = user_id);

create policy "Users can update own subjects"
    on public.subjects for update
    using (auth.uid() = user_id);

create policy "Users can delete own subjects"
    on public.subjects for delete
    using (auth.uid() = user_id);

-- Assignments: users can CRUD their own assignments
create policy "Users can view own assignments"
    on public.assignments for select
    using (auth.uid() = user_id);

create policy "Users can insert own assignments"
    on public.assignments for insert
    with check (auth.uid() = user_id);

create policy "Users can update own assignments"
    on public.assignments for update
    using (auth.uid() = user_id);

create policy "Users can delete own assignments"
    on public.assignments for delete
    using (auth.uid() = user_id);

-- Attachments: users can CRUD their own attachments
create policy "Users can view own attachments"
    on public.attachments for select
    using (auth.uid() = user_id);

create policy "Users can insert own attachments"
    on public.attachments for insert
    with check (auth.uid() = user_id);

create policy "Users can delete own attachments"
    on public.attachments for delete
    using (auth.uid() = user_id);

-- Notifications: users can CRUD their own notifications
create policy "Users can view own notifications"
    on public.notifications for select
    using (auth.uid() = user_id);

create policy "Users can insert own notifications"
    on public.notifications for insert
    with check (auth.uid() = user_id);

create policy "Users can update own notifications"
    on public.notifications for update
    using (auth.uid() = user_id);

create policy "Users can delete own notifications"
    on public.notifications for delete
    using (auth.uid() = user_id);

-- Study sessions: users can CRUD their own sessions
create policy "Users can view own study sessions"
    on public.study_sessions for select
    using (auth.uid() = user_id);

create policy "Users can insert own study sessions"
    on public.study_sessions for insert
    with check (auth.uid() = user_id);

create policy "Users can update own study sessions"
    on public.study_sessions for update
    using (auth.uid() = user_id);

create policy "Users can delete own study sessions"
    on public.study_sessions for delete
    using (auth.uid() = user_id);

-- Pomodoro sessions: users can CRUD their own sessions
create policy "Users can view own pomodoro sessions"
    on public.pomodoro_sessions for select
    using (auth.uid() = user_id);

create policy "Users can insert own pomodoro sessions"
    on public.pomodoro_sessions for insert
    with check (auth.uid() = user_id);

create policy "Users can update own pomodoro sessions"
    on public.pomodoro_sessions for update
    using (auth.uid() = user_id);

create policy "Users can delete own pomodoro sessions"
    on public.pomodoro_sessions for delete
    using (auth.uid() = user_id);

-- AI history: users can CRUD their own history
create policy "Users can view own ai history"
    on public.ai_history for select
    using (auth.uid() = user_id);

create policy "Users can insert own ai history"
    on public.ai_history for insert
    with check (auth.uid() = user_id);

create policy "Users can delete own ai history"
    on public.ai_history for delete
    using (auth.uid() = user_id);

-- Email accounts: users can CRUD their own accounts
create policy "Users can view own email accounts"
    on public.email_accounts for select
    using (auth.uid() = user_id);

create policy "Users can insert own email accounts"
    on public.email_accounts for insert
    with check (auth.uid() = user_id);

create policy "Users can update own email accounts"
    on public.email_accounts for update
    using (auth.uid() = user_id);

create policy "Users can delete own email accounts"
    on public.email_accounts for delete
    using (auth.uid() = user_id);

-- Analytics: users can CRUD their own analytics
create policy "Users can view own analytics"
    on public.analytics for select
    using (auth.uid() = user_id);

create policy "Users can insert own analytics"
    on public.analytics for insert
    with check (auth.uid() = user_id);

create policy "Users can update own analytics"
    on public.analytics for update
    using (auth.uid() = user_id);

-- ============================================
-- STORAGE BUCKETS
-- ============================================

-- Attachments bucket for user-uploaded files
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
    'attachments',
    'attachments',
    false,
    52428800,
    array['image/png', 'image/jpeg', 'image/gif', 'image/webp', 'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
)
on conflict (id) do nothing;

-- RLS for attachments bucket
create policy "Users can view own attachment files"
    on storage.objects for select
    using (auth.uid()::text = (storage.foldername(name))[1]);

create policy "Users can upload own attachment files"
    on storage.objects for insert
    with check (
        auth.uid()::text = (storage.foldername(name))[1]
        and bucket_id = 'attachments'
    );

create policy "Users can delete own attachment files"
    on storage.objects for delete
    using (auth.uid()::text = (storage.foldername(name))[1]);
