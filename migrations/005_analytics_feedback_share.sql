-- Migration 005: Analytics, feedback, share links, tighter RLS
-- Run this in Supabase SQL Editor AFTER 004_add_user_id.sql.

-- ══════════════════════════════════════════════════════════════
-- build_analytics — per-build telemetry for growth + debugging
-- ══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS build_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    build_id TEXT NOT NULL,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    user_id UUID,
    prompt TEXT,
    model TEXT,
    complexity TEXT,
    duration_ms INTEGER,
    self_heal_attempts INTEGER NOT NULL DEFAULT 0,
    cache_hit BOOLEAN NOT NULL DEFAULT false,
    success BOOLEAN NOT NULL DEFAULT false,
    error_category TEXT,
    error_message TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    request_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_build_analytics_user_id ON build_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_build_analytics_created_at ON build_analytics(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_build_analytics_success ON build_analytics(success);
CREATE INDEX IF NOT EXISTS idx_build_analytics_build_id ON build_analytics(build_id);

ALTER TABLE build_analytics ENABLE ROW LEVEL SECURITY;

-- Only the owner (or service role) can read their own analytics
CREATE POLICY "Users read own analytics" ON build_analytics
    FOR SELECT USING (user_id = auth.uid());

-- Inserts are done via service role from the backend — no direct client write
CREATE POLICY "No direct inserts" ON build_analytics
    FOR INSERT WITH CHECK (false);

-- ══════════════════════════════════════════════════════════════
-- build_feedback — thumbs up/down + optional note
-- ══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS build_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    build_id TEXT NOT NULL,
    user_id UUID,
    rating SMALLINT NOT NULL CHECK (rating IN (-1, 0, 1)),
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_build_feedback_unique
    ON build_feedback(build_id, COALESCE(user_id::text, 'anonymous'));

ALTER TABLE build_feedback ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage own feedback" ON build_feedback
    FOR ALL USING (user_id = auth.uid() OR user_id IS NULL);

-- ══════════════════════════════════════════════════════════════
-- share_links — public read-only viewer tokens
-- ══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS share_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token TEXT NOT NULL UNIQUE,
    build_id TEXT NOT NULL,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    owner_id UUID,
    expires_at TIMESTAMPTZ,
    view_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_share_links_token ON share_links(token);
CREATE INDEX IF NOT EXISTS idx_share_links_build_id ON share_links(build_id);

ALTER TABLE share_links ENABLE ROW LEVEL SECURITY;

-- Public can read non-expired share links by token lookup (done through API)
CREATE POLICY "Owners manage share links" ON share_links
    FOR ALL USING (owner_id = auth.uid());

-- ══════════════════════════════════════════════════════════════
-- Tighter RLS: drop the "OR user_id IS NULL" legacy escape hatches
-- Legacy anonymous projects are deprecated — backend backfills user_id
-- on writes, so orphan rows shouldn't exist in new installations.
-- ══════════════════════════════════════════════════════════════
DROP POLICY IF EXISTS "Users can view own projects" ON projects;
DROP POLICY IF EXISTS "Users can insert own projects" ON projects;
DROP POLICY IF EXISTS "Users can update own projects" ON projects;
DROP POLICY IF EXISTS "Users can delete own projects" ON projects;

CREATE POLICY "Users view own projects" ON projects
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users insert own projects" ON projects
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users update own projects" ON projects
    FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY "Users delete own projects" ON projects
    FOR DELETE USING (user_id = auth.uid());
