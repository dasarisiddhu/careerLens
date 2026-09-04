-- Supports POST /api/optimizer/analyse and keeps the existing resume/GitHub
-- analysis flow compatible with the shared resume_analyses table.
-- Run once in Supabase SQL Editor.

CREATE TABLE IF NOT EXISTS public.resume_analyses (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL,
    resume_file     TEXT,
    github_url      TEXT NOT NULL DEFAULT '',
    linkedin_url    TEXT NOT NULL DEFAULT '',
    job_role        TEXT NOT NULL DEFAULT '',
    job_title       TEXT NOT NULL DEFAULT '',
    job_description TEXT NOT NULL DEFAULT '',
    score           INTEGER CHECK (score >= 0 AND score <= 100),
    results_json    JSONB,
    result_json     JSONB NOT NULL DEFAULT '{}',
    status          TEXT DEFAULT 'pending',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.resume_analyses
    ADD COLUMN IF NOT EXISTS resume_file TEXT,
    ADD COLUMN IF NOT EXISTS github_url TEXT NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS linkedin_url TEXT NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS job_role TEXT NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS job_title TEXT NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS job_description TEXT NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS score INTEGER CHECK (score >= 0 AND score <= 100),
    ADD COLUMN IF NOT EXISTS results_json JSONB,
    ADD COLUMN IF NOT EXISTS result_json JSONB NOT NULL DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending',
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

ALTER TABLE public.resume_analyses
    ALTER COLUMN github_url SET DEFAULT '',
    ALTER COLUMN linkedin_url SET DEFAULT '',
    ALTER COLUMN job_role SET DEFAULT '';

CREATE INDEX IF NOT EXISTS idx_resume_analyses_user_id
    ON public.resume_analyses(user_id);

ALTER TABLE public.resume_analyses ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users see own optimizer analyses"
    ON public.resume_analyses;

CREATE POLICY "Users see own optimizer analyses"
    ON public.resume_analyses FOR ALL
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());
