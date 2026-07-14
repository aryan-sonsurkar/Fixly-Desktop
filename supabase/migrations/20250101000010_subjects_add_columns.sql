-- Add missing columns to subjects table
alter table public.subjects
  add column if not exists color text,
  add column if not exists icon text,
  add column if not exists credits integer,
  add column if not exists updated_at timestamptz not null default now();

-- Update constraint for credits (pg_constraint check for PG < 16 compatibility)
do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conname = 'valid_credits'
    and conrelid = 'public.subjects'::regclass
  ) then
    alter table public.subjects
      add constraint valid_credits check (credits is null or (credits >= 0 and credits <= 30));
  end if;
end $$;

-- Add updated_at trigger
create trigger set_subjects_updated_at
    before update on public.subjects
    for each row
    execute function public.set_updated_at();

-- Create index for common queries
create index if not exists idx_subjects_user_updated on public.subjects(user_id, updated_at);