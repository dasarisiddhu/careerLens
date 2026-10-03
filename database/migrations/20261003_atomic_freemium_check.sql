-- Migration: Atomic freemium check and increment for resume analysis
-- Timestamp: 20261003_atomic_freemium_check.sql
-- Addresses CWE-367 (TOCTOU) race condition on freemium usage counters

CREATE OR REPLACE FUNCTION public.try_increment_resume_count(p_user_id UUID, p_max INT)
RETURNS BOOLEAN AS $$
DECLARE
    v_updated INT;
BEGIN
    UPDATE public.users
    SET resume_analysis_count = resume_analysis_count + 1
    WHERE user_id = p_user_id
      AND (plan_type != 'freemium' OR resume_analysis_count < p_max);

    GET DIAGNOSTICS v_updated = ROW_COUNT;
    RETURN v_updated > 0;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

REVOKE EXECUTE ON FUNCTION public.try_increment_resume_count(UUID, INT) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.try_increment_resume_count(UUID, INT) TO service_role;

CREATE OR REPLACE FUNCTION public.decrement_resume_count(p_user_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE public.users
    SET resume_analysis_count = GREATEST(0, resume_analysis_count - 1)
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

REVOKE EXECUTE ON FUNCTION public.decrement_resume_count(UUID) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.decrement_resume_count(UUID) TO service_role;
