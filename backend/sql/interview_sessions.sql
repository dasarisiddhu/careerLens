-- ============================================================
-- CareerLens - interview_sessions table
-- Run this in Supabase SQL editor.
-- ============================================================

create extension if not exists pgcrypto;

create table if not exists public.interview_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  job_role text not null,
  mode text not null default 'text',
  status text not null default 'in_progress',
  questions jsonb not null default '[]'::jsonb,
  answers jsonb not null default '[]'::jsonb,
  transcript jsonb not null default '[]'::jsonb,
  evaluation jsonb,
  score integer,
  communication_score integer,
  technical_score integer,
  overall_score integer,
  created_at timestamptz not null default now()
);

-- Backward-compatible patches for existing tables.
alter table public.interview_sessions add column if not exists mode text default 'text';
alter table public.interview_sessions add column if not exists status text default 'in_progress';
alter table public.interview_sessions add column if not exists questions jsonb default '[]'::jsonb;
alter table public.interview_sessions add column if not exists answers jsonb default '[]'::jsonb;
alter table public.interview_sessions add column if not exists transcript jsonb default '[]'::jsonb;
alter table public.interview_sessions add column if not exists evaluation jsonb;
alter table public.interview_sessions add column if not exists score integer;
alter table public.interview_sessions add column if not exists communication_score integer;
alter table public.interview_sessions add column if not exists technical_score integer;
alter table public.interview_sessions add column if not exists overall_score integer;
alter table public.interview_sessions add column if not exists created_at timestamptz default now();

create index if not exists idx_interview_sessions_user_created
  on public.interview_sessions (user_id, created_at desc);

create index if not exists idx_interview_sessions_role_created
  on public.interview_sessions (job_role, created_at desc);

