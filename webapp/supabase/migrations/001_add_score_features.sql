-- Migration 001: Add explainability columns to clusters table
-- Run in: Supabase Dashboard → SQL Editor → New Query

alter table public.clusters
  add column if not exists score_features     jsonb not null default '[]'::jsonb,
  add column if not exists source_reliability text  not null default 'unknown';
