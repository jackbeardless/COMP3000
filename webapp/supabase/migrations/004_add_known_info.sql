alter table public.cases
  add column if not exists known_info jsonb not null default '{}'::jsonb;
