-- Migration 002: Add contradiction_flags column to clusters table
-- Run in: Supabase Dashboard → SQL Editor → New Query

alter table public.clusters
  add column if not exists contradiction_flags text[] not null default '{}';
