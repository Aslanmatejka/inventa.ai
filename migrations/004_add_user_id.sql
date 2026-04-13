-- Migration 004: Add user_id to projects table for per-user project scoping
-- Run this in Supabase SQL Editor

-- ══════════════════════════════════════════════════════════════
-- Add user_id column (nullable for backward compatibility with existing rows)
-- ══════════════════════════════════════════════════════════════
ALTER TABLE projects ADD COLUMN IF NOT EXISTS user_id UUID;

-- Index for fast user-scoped queries
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects (user_id);

-- ══════════════════════════════════════════════════════════════
-- Update RLS policies — users can only see/edit their own projects
-- Existing "Allow all" policies are replaced with user-scoped ones
-- ══════════════════════════════════════════════════════════════

-- Drop old permissive policies
DROP POLICY IF EXISTS "Allow all for service role" ON projects;
DROP POLICY IF EXISTS "Allow all for service role" ON builds;
DROP POLICY IF EXISTS "Allow all for service role" ON chat_messages;

-- Projects: users see only their own, or projects with no owner (legacy)
CREATE POLICY "Users can view own projects" ON projects
    FOR SELECT USING (
        user_id = auth.uid() OR user_id IS NULL
    );

CREATE POLICY "Users can insert own projects" ON projects
    FOR INSERT WITH CHECK (
        user_id = auth.uid() OR user_id IS NULL
    );

CREATE POLICY "Users can update own projects" ON projects
    FOR UPDATE USING (
        user_id = auth.uid() OR user_id IS NULL
    );

CREATE POLICY "Users can delete own projects" ON projects
    FOR DELETE USING (
        user_id = auth.uid() OR user_id IS NULL
    );

-- Builds: accessible if user owns the parent project
CREATE POLICY "Users can access builds via project" ON builds
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = builds.project_id
            AND (projects.user_id = auth.uid() OR projects.user_id IS NULL)
        )
    );

-- Chat messages: accessible if user owns the parent project
CREATE POLICY "Users can access messages via project" ON chat_messages
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM projects
            WHERE projects.id = chat_messages.project_id
            AND (projects.user_id = auth.uid() OR projects.user_id IS NULL)
        )
    );

-- Version history: keep permissive (no project FK)
DROP POLICY IF EXISTS "Allow all for service role" ON version_history;
CREATE POLICY "Allow all version history" ON version_history
    FOR ALL USING (true);
