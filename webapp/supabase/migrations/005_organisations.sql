-- Migration 005: Organisations, members, and deletion requests
-- Run in: Supabase Dashboard → SQL Editor → New Query

-- ── Organisations ─────────────────────────────────────────────
create table public.organisations (
  id             uuid        primary key default uuid_generate_v4(),
  name           text        not null,
  admin_user_id  uuid        not null references auth.users(id) on delete cascade,
  created_at     timestamptz not null default now()
);

-- ── Organisation Members ───────────────────────────────────────
create table public.organisation_members (
  id            uuid        primary key default uuid_generate_v4(),
  org_id        uuid        not null references public.organisations(id) on delete cascade,
  user_id       uuid        references auth.users(id) on delete set null,
  email         text        not null,
  role          text        not null default 'member' check (role in ('admin', 'member')),
  status        text        not null default 'pending' check (status in ('pending', 'active')),
  invite_token  uuid        not null default uuid_generate_v4(),
  invited_at    timestamptz not null default now(),
  joined_at     timestamptz,
  unique (org_id, email)
);

create index org_members_user_id_idx on public.organisation_members(user_id);
create index org_members_token_idx   on public.organisation_members(invite_token);

-- ── Deletion Requests ─────────────────────────────────────────
create table public.deletion_requests (
  id             uuid        primary key default uuid_generate_v4(),
  org_id         uuid        not null references public.organisations(id) on delete cascade,
  requested_by   uuid        not null references auth.users(id),
  resource_type  text        not null check (resource_type in ('case', 'scan')),
  resource_id    uuid        not null,
  resource_name  text,
  status         text        not null default 'pending' check (status in ('pending', 'approved', 'rejected')),
  created_at     timestamptz not null default now(),
  resolved_at    timestamptz,
  resolved_by    uuid        references auth.users(id)
);

create index deletion_requests_org_idx    on public.deletion_requests(org_id);
create index deletion_requests_status_idx on public.deletion_requests(status);

-- ── Cases: add org_id ─────────────────────────────────────────
alter table public.cases
  add column if not exists org_id uuid references public.organisations(id) on delete cascade;

create index cases_org_id_idx on public.cases(org_id);

-- Recreate case_summaries view to include org_id and known_info
drop view if exists public.case_summaries;
create view public.case_summaries as
select
  ca.id,
  ca.user_id,
  ca.org_id,
  ca.name,
  ca.description,
  ca.target,
  ca.status,
  ca.known_info,
  ca.created_at,
  ca.updated_at,
  count(s.id)                                           as total_scans,
  max(s.created_at)                                     as last_scan_at,
  (select status from public.scans
   where case_id = ca.id
   order by created_at desc limit 1)                    as last_scan_status
from public.cases ca
left join public.scans s on s.case_id = ca.id
group by ca.id;

-- ── RLS — enable after all tables exist ───────────────────────
alter table public.organisations      enable row level security;
alter table public.organisation_members enable row level security;
alter table public.deletion_requests  enable row level security;

-- organisations: members can view their org
create policy "org: members can view"
  on public.organisations for select
  using (
    id in (
      select org_id from public.organisation_members
      where user_id = auth.uid() and status = 'active'
    )
  );

create policy "org: authenticated can create"
  on public.organisations for insert
  with check (admin_user_id = auth.uid());

-- organisation_members: members can view others in same org
create policy "members: org members can view"
  on public.organisation_members for select
  using (
    org_id in (
      select org_id from public.organisation_members m2
      where m2.user_id = auth.uid() and m2.status = 'active'
    )
  );

-- deletion_requests: org members can view
create policy "deletion_requests: org members can view"
  on public.deletion_requests for select
  using (
    org_id in (
      select org_id from public.organisation_members
      where user_id = auth.uid() and status = 'active'
    )
  );

create policy "deletion_requests: org members can create"
  on public.deletion_requests for insert
  with check (
    requested_by = auth.uid()
    and org_id in (
      select org_id from public.organisation_members
      where user_id = auth.uid() and status = 'active'
    )
  );
