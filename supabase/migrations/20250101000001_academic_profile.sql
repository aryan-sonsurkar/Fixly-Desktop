-- Add academic profile fields to profiles table
alter table public.profiles
  add column if not exists display_name text,
  add column if not exists education_type text,
  add column if not exists education_year text,
  add column if not exists college_name text,
  add column if not exists university_board text,
  add column if not exists branch_stream text,
  add column if not exists division text,
  add column if not exists roll_number text,
  add column if not exists onboarding_completed boolean not null default false;

-- Add missing fields to settings table
alter table public.settings
  add column if not exists daily_goal_hours integer not null default 0,
  add column if not exists assignment_reminders boolean not null default true,
  add column if not exists daily_briefing boolean not null default true,
  add column if not exists email_monitoring boolean not null default false;

-- Add icon and credits to subjects table
alter table public.subjects
  add column if not exists icon text,
  add column if not exists credits integer;
