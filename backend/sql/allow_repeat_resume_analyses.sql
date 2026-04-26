-- Allow users to run resume analysis multiple times with the same GitHub profile.
-- Run once in Supabase SQL Editor for existing projects.

ALTER TABLE public.resume_analyses
DROP CONSTRAINT IF EXISTS unique_github_linkedin_per_user;
