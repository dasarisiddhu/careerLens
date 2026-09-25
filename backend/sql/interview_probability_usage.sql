-- Add interview probability usage tracking for free-tier limits.

ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS interview_probability_count INTEGER NOT NULL DEFAULT 0;

CREATE OR REPLACE FUNCTION public.increment_interview_probability_count(p_user_id UUID)
RETURNS void AS $$
BEGIN
  UPDATE public.users
  SET interview_probability_count = interview_probability_count + 1
  WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
