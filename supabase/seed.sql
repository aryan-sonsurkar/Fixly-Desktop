-- Seed data for local development
-- This file is loaded after migrations during `supabase db reset`

-- Create a test user (password: testpassword123)
-- Note: In production, use the auth.signup flow
-- This is for local development only
insert into auth.users (id, email, encrypted_password, email_confirmed_at, confirmation_sent_at, raw_user_meta_data)
values (
    '00000000-0000-0000-0000-000000000001',
    'test@fixly.dev',
    crypt('testpassword123', gen_salt('bf')),
    now(),
    now(),
    '{"full_name": "Test User"}'
) on conflict (id) do nothing;

-- The auth trigger will automatically create profile and settings
insert into public.profiles (id, email, full_name, xp, streak)
values (
    '00000000-0000-0000-0000-000000000001',
    'test@fixly.dev',
    'Test User',
    150,
    3
) on conflict (id) do nothing;

insert into public.settings (user_id, theme)
values ('00000000-0000-0000-0000-000000000001', 'dark')
on conflict (user_id) do nothing;

-- Sample subjects
insert into public.subjects (id, user_id, name, color)
values
    ('10000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'Mathematics', '#3b82f6'),
    ('10000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', 'Physics', '#ef4444'),
    ('10000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000001', 'Computer Science', '#10b981')
on conflict (id) do nothing;

-- Sample assignments
insert into public.assignments (id, user_id, subject_id, title, description, status, priority, due_date)
values
    ('20000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000001', 'Calculus Problem Set 5', 'Integration by parts and trigonometric substitution', 'pending', 'high', now() + interval '3 days'),
    ('20000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000002', 'Lab Report: Quantum Mechanics', 'Write lab report on the double-slit experiment', 'in_progress', 'medium', now() + interval '7 days'),
    ('20000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000001', '10000000-0000-0000-0000-000000000003', 'Binary Search Tree Implementation', 'Implement BST with insert, delete, and traversal', 'completed', 'medium', now() - interval '2 days')
on conflict (id) do nothing;
