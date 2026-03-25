-- =============================================================
-- OSINT Dissertation — Supabase Schema
-- Run this entire file in: Supabase Dashboard → SQL Editor → New Query
-- =============================================================

-- UUID extension (already enabled in Supabase by default, but safe to repeat)
create extension if not exists "uuid-ossp";


-- =============================================================
-- PROFILES
-- One row per user. Auto-created on first login via a trigger.
-- =============================================================
create table public.profiles (
  id          uuid        primary key references auth.users(id) on delete cascade,
  username    text        unique not null,
  created_at  timestamptz not null default now()
);

-- Auto-create a profile row whenever a new user signs up
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer as $$
begin
  insert into public.profiles (id, username)
  values (
    new.id,
    coalesce(new.raw_user_meta_data->>'username', split_part(new.email, '@', 1))
  );
  return new;
end;
$$;

create or replace trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();


-- =============================================================
-- CASES
-- An investigation. A user creates a case, then runs scans within it.
-- =============================================================
create table public.cases (
  id          uuid        primary key default uuid_generate_v4(),
  user_id     uuid        not null references auth.users(id) on delete cascade,
  name        text        not null,
  description text,
  target      text        not null,   -- the OSINT target username
  status      text        not null default 'active'
                          check (status in ('active', 'archived')),
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

create index cases_user_id_idx on public.cases(user_id);
create index cases_status_idx  on public.cases(status);

-- Auto-update updated_at on any row change
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger cases_updated_at
  before update on public.cases
  for each row execute procedure public.set_updated_at();


-- =============================================================
-- SCANS
-- A single pipeline run within a case.
-- =============================================================
create table public.scans (
  id              uuid        primary key default uuid_generate_v4(),
  case_id         uuid        not null references public.cases(id) on delete cascade,
  user_id         uuid        not null references auth.users(id) on delete cascade,
  target          text        not null,
  status          text        not null default 'queued'
                              check (status in ('queued', 'running', 'complete', 'failed')),
  -- Pipeline configuration snapshot (what settings were used for this scan)
  config          jsonb       not null default '{}'::jsonb,
  -- Timing
  started_at      timestamptz,
  completed_at    timestamptz,
  -- Error detail if status = 'failed'
  error           text,
  created_at      timestamptz not null default now()
);

create index scans_case_id_idx  on public.scans(case_id);
create index scans_user_id_idx  on public.scans(user_id);
create index scans_status_idx   on public.scans(status);


-- =============================================================
-- CLUSTERS
-- Individual result clusters from a scan, stored flat for easy
-- querying, filtering, and analyst annotation.
-- =============================================================
create table public.clusters (
  id                  uuid        primary key default uuid_generate_v4(),
  scan_id             uuid        not null references public.scans(id) on delete cascade,
  -- Identity
  cluster_key         text        not null,   -- e.g. "github:yogscast"
  platform            text,
  handle              text,
  urls                text[]      not null default '{}',
  -- Scores
  heuristic_score     float       not null default 0,
  final_confidence    float,
  verdict             text        check (verdict in ('likely', 'maybe', 'low')),
  -- LLM metadata
  llm_status          text,       -- candidate_profile / search_or_tooling / invite_or_redirect / unknown_pattern
  rationale           text,       -- LLM explanation
  flags               text[]      not null default '{}',
  signals             text[]      not null default '{}',  -- SpiderFoot modules that found this
  -- Explainability: per-feature score contributions (list of {feature, delta, label})
  score_features      jsonb       not null default '[]'::jsonb,
  -- Source reliability tier for the platform: high / medium / low / unknown
  source_reliability  text        not null default 'unknown',
  -- Contradiction flags: cross-cluster and within-cluster inconsistencies detected
  contradiction_flags text[]      not null default '{}',
  -- Full raw cluster data for drilldown / evidence chain view
  raw_data            jsonb       not null default '{}'::jsonb,
  -- Analyst annotation (manual override)
  analyst_verdict     text        check (analyst_verdict in ('confirmed', 'disputed', 'needs_review')),
  analyst_note        text,
  analyst_updated_at  timestamptz,
  created_at          timestamptz not null default now(),
  -- Each cluster_key is unique within a scan
  unique (scan_id, cluster_key)
);

create index clusters_scan_id_idx       on public.clusters(scan_id);
create index clusters_verdict_idx       on public.clusters(verdict);
create index clusters_platform_idx      on public.clusters(platform);
create index clusters_final_conf_idx    on public.clusters(final_confidence desc);


-- =============================================================
-- ROW LEVEL SECURITY (RLS)
-- Every user can only see and modify their own data.
-- =============================================================
alter table public.profiles  enable row level security;
alter table public.cases     enable row level security;
alter table public.scans     enable row level security;
alter table public.clusters  enable row level security;


-- profiles: users can read and update their own profile only
create policy "profiles: own row"
  on public.profiles for all
  using (id = auth.uid());

-- cases: full access to own cases only
create policy "cases: own rows"
  on public.cases for all
  using (user_id = auth.uid());

-- scans: full access to own scans only
create policy "scans: own rows"
  on public.scans for all
  using (user_id = auth.uid());

-- clusters: accessible if the parent scan belongs to the current user
create policy "clusters: via own scan"
  on public.clusters for all
  using (
    scan_id in (
      select id from public.scans where user_id = auth.uid()
    )
  );


-- =============================================================
-- USEFUL VIEWS
-- =============================================================

-- Summary view: one row per scan with cluster stats pre-aggregated
create or replace view public.scan_summaries as
select
  s.id                                                  as scan_id,
  s.case_id,
  s.user_id,
  s.target,
  s.status,
  s.config,
  s.started_at,
  s.completed_at,
  s.error,
  s.created_at,
  count(c.id)                                           as total_clusters,
  count(c.id) filter (where c.verdict = 'likely')       as likely_count,
  count(c.id) filter (where c.verdict = 'maybe')        as maybe_count,
  count(c.id) filter (where c.verdict = 'low')          as low_count,
  round(avg(c.final_confidence)::numeric, 3)            as avg_confidence,
  round(max(c.final_confidence)::numeric, 3)            as max_confidence
from public.scans s
left join public.clusters c on c.scan_id = s.id
group by s.id;

-- Case summary view: case with latest scan status and total scans
create or replace view public.case_summaries as
select
  ca.id,
  ca.user_id,
  ca.name,
  ca.description,
  ca.target,
  ca.status,
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
