-- ============================================================
-- CareerLens – Supabase PostgreSQL Schema
-- Run this in your Supabase SQL Editor
-- ============================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- ENUMS
-- ============================================================

CREATE TYPE plan_type AS ENUM ('freemium', 'premium');
CREATE TYPE interview_mode AS ENUM ('text', 'voice');
CREATE TYPE interview_status AS ENUM ('in_progress', 'completed', 'abandoned');

-- ============================================================
-- TABLE: users
-- Extends Supabase auth.users with app-specific profile data
-- ============================================================

CREATE TABLE public.users (
    user_id         UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email           TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL DEFAULT '',
    avatar_url      TEXT,
    plan_type       plan_type NOT NULL DEFAULT 'freemium',
    resume_analysis_count   INTEGER NOT NULL DEFAULT 0,
    mock_interview_count    INTEGER NOT NULL DEFAULT 0,
    chatbot_message_count   INTEGER NOT NULL DEFAULT 0,
    portfolio_gen_count     INTEGER NOT NULL DEFAULT 0,
    interview_probability_count INTEGER NOT NULL DEFAULT 0,
    github_url      TEXT,
    linkedin_url    TEXT,
    desired_role    TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Auto-update updated_at on row change
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- TABLE: resume_analyses
-- Stores each resume analysis run per user
-- ============================================================

CREATE TABLE public.resume_analyses (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
    resume_file     TEXT,                    -- Supabase Storage path
    github_url      TEXT NOT NULL DEFAULT '',
    linkedin_url    TEXT NOT NULL DEFAULT '',
    job_role        TEXT NOT NULL DEFAULT '',
    job_title       TEXT NOT NULL DEFAULT '',
    job_description TEXT NOT NULL DEFAULT '',
    score           INTEGER CHECK (score >= 0 AND score <= 100),
    results_json    JSONB,                   -- Full Gemini response
    result_json     JSONB NOT NULL DEFAULT '{}',
    status          TEXT DEFAULT 'pending',  -- pending | processing | done | failed
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER resume_analyses_updated_at
    BEFORE UPDATE ON public.resume_analyses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Index for fast user history lookups
CREATE INDEX idx_resume_analyses_user_id ON public.resume_analyses(user_id);
CREATE INDEX idx_resume_analyses_created_at ON public.resume_analyses(created_at DESC);

-- ============================================================
-- TABLE: interview_sessions
-- Stores mock interview sessions (text or voice)
-- ============================================================

CREATE TABLE public.interview_sessions (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
    job_role            TEXT NOT NULL,
    mode                interview_mode NOT NULL DEFAULT 'text',
    status              interview_status NOT NULL DEFAULT 'in_progress',
    questions           JSONB DEFAULT '[]',      -- Array of questions asked
    transcript          JSONB DEFAULT '[]',      -- Q&A pairs
    evaluation          JSONB,                   -- Gemini evaluation result
    communication_score INTEGER CHECK (communication_score >= 0 AND communication_score <= 100),
    technical_score     INTEGER CHECK (technical_score >= 0 AND technical_score <= 100),
    overall_score       INTEGER CHECK (overall_score >= 0 AND overall_score <= 100),
    duration_seconds    INTEGER DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER interview_sessions_updated_at
    BEFORE UPDATE ON public.interview_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE INDEX idx_interview_sessions_user_id ON public.interview_sessions(user_id);
CREATE INDEX idx_interview_sessions_created_at ON public.interview_sessions(created_at DESC);

-- ============================================================
-- TABLE: chatbot_messages
-- Stores conversation history per user
-- ============================================================

CREATE TABLE public.chatbot_messages (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
    role        TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content     TEXT NOT NULL,
    session_id  UUID,                    -- Groups messages into conversations
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chatbot_messages_user_id ON public.chatbot_messages(user_id);
CREATE INDEX idx_chatbot_messages_session_id ON public.chatbot_messages(session_id);

-- ============================================================
-- TABLE: payment_records
-- Placeholder for Stripe / Razorpay integration
-- ============================================================

CREATE TABLE public.payment_records (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
    provider            TEXT NOT NULL CHECK (provider IN ('stripe', 'razorpay')),
    provider_payment_id TEXT,           -- External payment ID
    provider_customer_id TEXT,          -- External customer ID
    amount              INTEGER NOT NULL, -- In paise/cents
    currency            TEXT NOT NULL DEFAULT 'USD',
    status              TEXT NOT NULL CHECK (status IN ('pending', 'success', 'failed', 'refunded')),
    plan_type           plan_type NOT NULL DEFAULT 'premium',
    valid_until         TIMESTAMPTZ,
    metadata            JSONB DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_payment_records_user_id ON public.payment_records(user_id);

-- ============================================================
-- TABLE: github_cache
-- Caches GitHub API responses to reduce rate limit hits
-- ============================================================

CREATE TABLE public.github_cache (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    github_username TEXT NOT NULL UNIQUE,
    profile_data    JSONB NOT NULL,
    repos_data      JSONB NOT NULL DEFAULT '[]',
    languages_data  JSONB NOT NULL DEFAULT '{}',
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '6 hours')
);

CREATE INDEX idx_github_cache_username ON public.github_cache(github_username);
CREATE INDEX idx_github_cache_expires ON public.github_cache(expires_at);

-- ============================================================
-- ROW LEVEL SECURITY (RLS)
-- Ensures users can only access their own data
-- ============================================================

-- Enable RLS on all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.resume_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interview_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chatbot_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.payment_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.github_cache ENABLE ROW LEVEL SECURITY;

-- ---------- users ----------
CREATE POLICY "Users can view their own profile"
    ON public.users FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can update their own profile"
    ON public.users FOR UPDATE
    USING (auth.uid() = user_id);

-- ---------- resume_analyses ----------
CREATE POLICY "Users can view their own analyses"
    ON public.resume_analyses FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own analyses"
    ON public.resume_analyses FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own analyses"
    ON public.resume_analyses FOR UPDATE
    USING (auth.uid() = user_id);

-- ---------- interview_sessions ----------
CREATE POLICY "Users can view their own interviews"
    ON public.interview_sessions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own interviews"
    ON public.interview_sessions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own interviews"
    ON public.interview_sessions FOR UPDATE
    USING (auth.uid() = user_id);

-- ---------- chatbot_messages ----------
CREATE POLICY "Users can view their own messages"
    ON public.chatbot_messages FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own messages"
    ON public.chatbot_messages FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- ---------- payment_records ----------
CREATE POLICY "Users can view their own payments"
    ON public.payment_records FOR SELECT
    USING (auth.uid() = user_id);

-- ---------- github_cache ----------
-- Allow all authenticated users to read cache (shared).
-- The service-role client bypasses RLS entirely at the connection level;
-- no policy is needed or useful for it. Writing is therefore already
-- restricted to the backend's service-role client without a policy.
CREATE POLICY "Authenticated users can read github cache"
    ON public.github_cache FOR SELECT
    USING (auth.role() = 'authenticated');

-- ============================================================
-- FUNCTION: Auto-create user profile on signup
-- Triggered by Supabase Auth when a new user registers
-- ============================================================

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (user_id, email, name, avatar_url)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1)),
        NEW.raw_user_meta_data->>'avatar_url'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Attach trigger to Supabase auth.users
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================================
-- FUNCTION: Increment usage counters
-- Called by backend after successful analysis/interview
-- ============================================================

CREATE OR REPLACE FUNCTION public.increment_resume_count(p_user_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE public.users
    SET resume_analysis_count = resume_analysis_count + 1
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION public.increment_interview_count(p_user_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE public.users
    SET mock_interview_count = mock_interview_count + 1
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION public.increment_chatbot_count(p_user_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE public.users
    SET chatbot_message_count = chatbot_message_count + 1
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION public.increment_portfolio_count(p_user_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE public.users
    SET portfolio_gen_count = portfolio_gen_count + 1
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION public.increment_interview_probability_count(p_user_id UUID)
RETURNS void AS $$
BEGIN
  UPDATE public.users
  SET interview_probability_count = interview_probability_count + 1
  WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================
-- FUNCTION: Upgrade user to premium after payment
-- ============================================================

CREATE OR REPLACE FUNCTION public.upgrade_user_to_premium(p_user_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE public.users
    SET plan_type = 'premium'
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================
-- STORAGE BUCKETS
-- Run these via Supabase Dashboard > Storage, or via API
-- ============================================================

-- Create bucket for resume PDF uploads (run via Supabase JS client or Dashboard)
-- INSERT INTO storage.buckets (id, name, public) VALUES ('resumes', 'resumes', false);

-- Storage policy: Users can upload to their own folder only
-- CREATE POLICY "Users upload own resumes"
--   ON storage.objects FOR INSERT
--   WITH CHECK (bucket_id = 'resumes' AND auth.uid()::text = (storage.foldername(name))[1]);

-- CREATE POLICY "Users read own resumes"
--   ON storage.objects FOR SELECT
--   USING (bucket_id = 'resumes' AND auth.uid()::text = (storage.foldername(name))[1]);

-- ============================================================
-- VIEWS
-- ============================================================

-- Dashboard summary view per user
CREATE OR REPLACE VIEW public.user_dashboard_summary AS
SELECT
    u.user_id,
    u.name,
    u.email,
    u.plan_type,
    u.resume_analysis_count,
    u.mock_interview_count,
    u.chatbot_message_count,
    u.portfolio_gen_count,
    u.created_at,
    (
        SELECT COUNT(*) FROM public.resume_analyses ra
        WHERE ra.user_id = u.user_id
    ) AS total_analyses,
    (
        SELECT AVG(score) FROM public.resume_analyses ra
        WHERE ra.user_id = u.user_id AND ra.score IS NOT NULL
    ) AS avg_resume_score,
    (
        SELECT COUNT(*) FROM public.interview_sessions i
        WHERE i.user_id = u.user_id AND i.status = 'completed'
    ) AS completed_interviews
FROM public.users u;

-- ============================================================
-- INDEXES for performance
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_users_plan_type ON public.users(plan_type);
CREATE INDEX IF NOT EXISTS idx_resume_analyses_status ON public.resume_analyses(status);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_status ON public.interview_sessions(status);
CREATE INDEX IF NOT EXISTS idx_chatbot_messages_created ON public.chatbot_messages(created_at DESC);

-- Partial unique index: one CareerLens account per github_url.
-- NULL is allowed (user has no GitHub linked yet); only non-null values must be unique.
-- Run this AFTER checking for duplicate non-null github_url rows:
--   SELECT github_url, COUNT(*) FROM public.users WHERE github_url IS NOT NULL
--   GROUP BY github_url HAVING COUNT(*) > 1;
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_github_url_unique
    ON public.users(github_url)
    WHERE github_url IS NOT NULL;

-- ============================================================
-- TABLE: github_identities
-- Enforces durable GitHub ownership at the database level.
-- UNIQUE(careerlens_user_id) → one GitHub account per CareerLens user (Invariant B)
-- UNIQUE(github_user_id)     → one CareerLens user per GitHub account (Invariant A)
-- github_user_id is the numeric GitHub account ID stored as TEXT
-- to avoid JavaScript integer-precision issues with large IDs.
-- The mutable github_login (username) is stored only for display;
-- it is NEVER used as an identity key.
-- ============================================================

CREATE TABLE IF NOT EXISTS public.github_identities (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    careerlens_user_id  UUID NOT NULL UNIQUE REFERENCES public.users(user_id) ON DELETE CASCADE,
    github_user_id      TEXT NOT NULL UNIQUE,   -- GitHub numeric ID (immutable, as TEXT)
    github_login        TEXT NOT NULL,           -- mutable username (display only)
    avatar_url          TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER github_identities_updated_at
    BEFORE UPDATE ON public.github_identities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

ALTER TABLE public.github_identities ENABLE ROW LEVEL SECURITY;

-- Users may only read their own identity record.
-- The service-role backend client bypasses RLS to write.
CREATE POLICY "Users view own github identity"
    ON public.github_identities FOR SELECT
    USING (auth.uid() = careerlens_user_id);

CREATE INDEX IF NOT EXISTS idx_github_identities_user_id
    ON public.github_identities(careerlens_user_id);
CREATE INDEX IF NOT EXISTS idx_github_identities_github_user_id
    ON public.github_identities(github_user_id);

-- ============================================================
-- TABLE: resume_versions
-- Tracks score history per user for the progress chart.
-- ============================================================

CREATE TABLE IF NOT EXISTS public.resume_versions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
    version_number  INTEGER NOT NULL DEFAULT 1,
    resume_score    INTEGER CHECK (resume_score >= 0 AND resume_score <= 100),
    ats_score       INTEGER CHECK (ats_score >= 0 AND ats_score <= 100),
    job_role        TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.resume_versions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users view own resume versions"
    ON public.resume_versions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users insert own resume versions"
    ON public.resume_versions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_resume_versions_user_id
    ON public.resume_versions(user_id);

-- ============================================================
-- TABLE: community_posts, post_likes, post_comments
-- ============================================================

CREATE TABLE IF NOT EXISTS public.community_posts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
    author_name     TEXT NOT NULL DEFAULT '',
    -- author_email is intentionally NOT stored; use users table with RLS if needed.
    post_type       TEXT NOT NULL DEFAULT 'blog',  -- project|job|funding|blog|hiring
    title           TEXT NOT NULL,
    content         TEXT NOT NULL,
    demo_url        TEXT NOT NULL DEFAULT '',
    github_url      TEXT NOT NULL DEFAULT '',
    tags            TEXT[] NOT NULL DEFAULT '{}',
    likes_count     INTEGER NOT NULL DEFAULT 0 CHECK (likes_count >= 0),
    comments_count  INTEGER NOT NULL DEFAULT 0 CHECK (comments_count >= 0),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER community_posts_updated_at
    BEFORE UPDATE ON public.community_posts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

ALTER TABLE public.community_posts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read posts"
    ON public.community_posts FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Users can create own posts"
    ON public.community_posts FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own posts"
    ON public.community_posts FOR DELETE
    USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_community_posts_user_id
    ON public.community_posts(user_id);
CREATE INDEX IF NOT EXISTS idx_community_posts_created_at
    ON public.community_posts(created_at DESC);

-- post_likes: UNIQUE(post_id, user_id) prevents race-condition duplicate likes.
CREATE TABLE IF NOT EXISTS public.post_likes (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id     UUID NOT NULL REFERENCES public.community_posts(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(post_id, user_id)  -- DB-level duplicate-like prevention
);

ALTER TABLE public.post_likes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users view own likes"
    ON public.post_likes FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users manage own likes"
    ON public.post_likes FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE TABLE IF NOT EXISTS public.post_comments (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id     UUID NOT NULL REFERENCES public.community_posts(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
    author_name TEXT NOT NULL DEFAULT '',
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.post_comments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read comments"
    ON public.post_comments FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Users can insert own comments"
    ON public.post_comments FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own comments"
    ON public.post_comments FOR DELETE
    USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_post_comments_post_id
    ON public.post_comments(post_id);

