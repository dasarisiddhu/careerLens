-- Fixes: "Analysis DB save failed ... Could not find the 'job_description' column of
-- 'resume_analyses' in the schema cache" (PostgREST PGRST204) from POST /api/optimizer/analyse.
-- backend/sql/resume_optimizer_analyses.sql defines these columns but lives outside
-- database/migrations/, so it was never applied. Idempotent: safe to run more than once.

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

-- Make PostgREST see the new columns immediately (otherwise PGRST204 persists until it refreshes).
NOTIFY pgrst, 'reload schema';
