-- Migration: 20261003_lock_down_users_writes.sql
-- Description:
-- 1. [FINDING-001] Lock down table write permissions from anon and authenticated clients.
--    The frontend only reads or talks to the FastAPI backend, while the backend uses the service_role key.
--    Prevents users from updating their own plan_type, usage counters, or analyses directly via Supabase REST API.
-- 2. [FINDING-002] Secure SECURITY DEFINER functions with search_path and revoke EXECUTE from PUBLIC/anon/authenticated.
--    Only service_role can execute these administrative/counter functions.

-- ============================================================
-- 1. LOCK DOWN TABLE WRITES (RLS & PRIVILEGES)
-- ============================================================

-- Remove user update policy that allowed tampering with plan_type and counters
DROP POLICY IF EXISTS "Users can update their own profile" ON public.users;

-- Revoke write permissions from client-facing roles
REVOKE INSERT, UPDATE, DELETE ON public.users FROM anon, authenticated;
REVOKE INSERT, UPDATE, DELETE ON public.resume_analyses, public.interview_sessions, public.chatbot_messages, public.resume_versions FROM anon, authenticated;

-- Drop insert/update policies for tables that only backend service-role should modify
DROP POLICY IF EXISTS "Users can update their own analyses" ON public.resume_analyses;
DROP POLICY IF EXISTS "Users can update their own interviews" ON public.interview_sessions;
DROP POLICY IF EXISTS "Users can insert their own analyses" ON public.resume_analyses;
DROP POLICY IF EXISTS "Users can insert their own interviews" ON public.interview_sessions;
DROP POLICY IF EXISTS "Users can insert their own messages" ON public.chatbot_messages;
DROP POLICY IF EXISTS "Users insert own resume versions" ON public.resume_versions;

-- Keep SELECT policies intact so users can view their own data via client SDK if needed.


-- ============================================================
-- 2. LOCK DOWN SECURITY DEFINER FUNCTIONS & SEARCH PATH
-- ============================================================

-- Fix search_path on auth trigger function
ALTER FUNCTION public.handle_new_user() SET search_path = public, pg_temp;

-- Lock down upgrade_user_to_premium
ALTER FUNCTION public.upgrade_user_to_premium(UUID) SET search_path = public, pg_temp;
REVOKE EXECUTE ON FUNCTION public.upgrade_user_to_premium(UUID) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.upgrade_user_to_premium(UUID) TO service_role;

-- Lock down increment_resume_count
ALTER FUNCTION public.increment_resume_count(UUID) SET search_path = public, pg_temp;
REVOKE EXECUTE ON FUNCTION public.increment_resume_count(UUID) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.increment_resume_count(UUID) TO service_role;

-- Lock down increment_interview_count
ALTER FUNCTION public.increment_interview_count(UUID) SET search_path = public, pg_temp;
REVOKE EXECUTE ON FUNCTION public.increment_interview_count(UUID) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.increment_interview_count(UUID) TO service_role;

-- Lock down increment_chatbot_count
ALTER FUNCTION public.increment_chatbot_count(UUID) SET search_path = public, pg_temp;
REVOKE EXECUTE ON FUNCTION public.increment_chatbot_count(UUID) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.increment_chatbot_count(UUID) TO service_role;

-- Lock down increment_portfolio_count
ALTER FUNCTION public.increment_portfolio_count(UUID) SET search_path = public, pg_temp;
REVOKE EXECUTE ON FUNCTION public.increment_portfolio_count(UUID) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.increment_portfolio_count(UUID) TO service_role;

-- Lock down increment_interview_probability_count
ALTER FUNCTION public.increment_interview_probability_count(UUID) SET search_path = public, pg_temp;
REVOKE EXECUTE ON FUNCTION public.increment_interview_probability_count(UUID) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.increment_interview_probability_count(UUID) TO service_role;
