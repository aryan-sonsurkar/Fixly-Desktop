-- AI Platform: conversations and messages tables

create table if not exists public.conversations (
  id uuid not null default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null default 'New conversation',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint conversations_pkey primary key (id)
);

create table if not exists public.messages (
  id uuid not null default gen_random_uuid(),
  conversation_id uuid not null references public.conversations(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('user', 'assistant', 'system')),
  content text not null,
  provider text,
  tokens int,
  created_at timestamptz not null default now(),
  constraint messages_pkey primary key (id)
);

create index if not exists idx_conversations_user_id on public.conversations(user_id);
create index if not exists idx_messages_conversation_id on public.messages(conversation_id);
create index if not exists idx_messages_user_id on public.messages(user_id);
create index if not exists idx_messages_created_at on public.messages(conversation_id, created_at);
