-- Add new columns to assignments table
alter table public.assignments
  add column if not exists estimated_study_time integer,
  add column if not exists tags text[],
  add column if not exists notes text,
  add column if not exists completion_date timestamptz,
  add column if not exists is_archived boolean not null default false,
  add column if not exists is_pinned boolean not null default false,
  add column if not exists is_favorite boolean not null default false;

-- Drop old constraint, add new one with 'overdue'
alter table public.assignments drop constraint if exists valid_status;
alter table public.assignments add constraint valid_status check (
  status in ('pending', 'in_progress', 'completed', 'cancelled', 'overdue')
);

-- Create index for common queries
create index if not exists idx_assignments_user_status on public.assignments(user_id, status);
create index if not exists idx_assignments_user_priority on public.assignments(user_id, priority);
create index if not exists idx_assignments_user_due_date on public.assignments(user_id, due_date);
create index if not exists idx_assignments_user_archived on public.assignments(user_id, is_archived);
create index if not exists idx_assignments_user_favorite on public.assignments(user_id, is_favorite);
create index if not exists idx_assignments_tags on public.assignments using gin(tags);
