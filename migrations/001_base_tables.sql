-- Migration 001: Base tables (projects, builds, chat_messages, version_history)
-- Run this in Supabase SQL Editor BEFORE 003_scenes_materials.sql

-- ══════════════════════════════════════════════════════════════
-- Projects table
-- ══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
    name TEXT NOT NULL DEFAULT 'Untitled Project',
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ══════════════════════════════════════════════════════════════
-- Builds table
-- ══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS builds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    build_id TEXT NOT NULL,
    prompt TEXT,
    code TEXT,
    parameters JSONB,
    explanation JSONB,
    stl_path TEXT,
    step_path TEXT,
    script_path TEXT,
    is_modification BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ══════════════════════════════════════════════════════════════
-- Chat messages table
-- ══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
    project_id UUID NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT,
    build_result JSONB,
    status TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ══════════════════════════════════════════════════════════════
-- Version history table
-- ══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS version_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
    build_id TEXT NOT NULL,
    label TEXT DEFAULT 'Snapshot',
    code TEXT,
    parameters JSONB,
    explanation JSONB,
    prompt TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ══════════════════════════════════════════════════════════════
-- Indexes
-- ══════════════════════════════════════════════════════════════
CREATE INDEX IF NOT EXISTS idx_builds_project_id ON builds (project_id);

CREATE INDEX IF NOT EXISTS idx_builds_build_id ON builds (build_id);

CREATE INDEX IF NOT EXISTS idx_chat_messages_project_id ON chat_messages (project_id);

CREATE INDEX IF NOT EXISTS idx_version_history_build_id ON version_history (build_id);

CREATE INDEX IF NOT EXISTS idx_projects_updated_at ON projects (updated_at DESC);

-- ══════════════════════════════════════════════════════════════
-- Enable RLS
-- ══════════════════════════════════════════════════════════════
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

ALTER TABLE builds ENABLE ROW LEVEL SECURITY;

ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

ALTER TABLE version_history ENABLE ROW LEVEL SECURITY;

-- ══════════════════════════════════════════════════════════════
-- Permissive policies (service role key bypasses RLS)
-- Adjust these for proper user-level auth when ready
-- ══════════════════════════════════════════════════════════════
CREATE POLICY "Allow all for service role" ON projects FOR ALL USING (true);

CREATE POLICY "Allow all for service role" ON builds FOR ALL USING (true);

CREATE POLICY "Allow all for service role" ON chat_messages FOR ALL USING (true);

CREATE POLICY "Allow all for service role" ON version_history FOR ALL USING (true);