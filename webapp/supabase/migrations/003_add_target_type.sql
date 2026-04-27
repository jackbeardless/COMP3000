alter table public.cases
  add column if not exists target_type text not null default 'username';
