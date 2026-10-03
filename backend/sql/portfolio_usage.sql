-- Add portfolio generation usage tracking for free-tier limits.

ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS portfolio_gen_count INTEGER NOT NULL DEFAULT 0;

CREATE OR REPLACE FUNCTION public.increment_portfolio_count(p_user_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE public.users
    SET portfolio_gen_count = portfolio_gen_count + 1
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

REVOKE EXECUTE ON FUNCTION public.increment_portfolio_count(UUID) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.increment_portfolio_count(UUID) TO service_role;
