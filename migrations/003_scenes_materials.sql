-- Migration 003: Add scenes, scene_products, and material_metadata tables
-- Run this in Supabase SQL Editor

-- Scenes table
CREATE TABLE IF NOT EXISTS scenes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
    name TEXT NOT NULL DEFAULT 'Default Scene',
    project_id UUID REFERENCES projects (id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Scene products table
CREATE TABLE IF NOT EXISTS scene_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
    scene_id UUID NOT NULL REFERENCES scenes (id) ON DELETE CASCADE,
    instance_id TEXT NOT NULL UNIQUE,
    build_id TEXT NOT NULL DEFAULT '',
    instance_name TEXT NOT NULL DEFAULT '',
    stl_url TEXT NOT NULL DEFAULT '',
    product_type TEXT NOT NULL DEFAULT '',
    position JSONB NOT NULL DEFAULT '{"x":0,"y":0,"z":0}',
    rotation JSONB NOT NULL DEFAULT '{"x":0,"y":0,"z":0}',
    scale JSONB NOT NULL DEFAULT '{"x":1,"y":1,"z":1}',
    design_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Material metadata table
CREATE TABLE IF NOT EXISTS material_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid (),
    build_id TEXT NOT NULL UNIQUE,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_scene_products_scene_id ON scene_products (scene_id);

CREATE INDEX IF NOT EXISTS idx_scene_products_instance_id ON scene_products (instance_id);

CREATE INDEX IF NOT EXISTS idx_scenes_project_id ON scenes (project_id);

CREATE INDEX IF NOT EXISTS idx_material_metadata_build_id ON material_metadata (build_id);

-- Enable RLS (Row Level Security)
ALTER TABLE scenes ENABLE ROW LEVEL SECURITY;

ALTER TABLE scene_products ENABLE ROW LEVEL SECURITY;

ALTER TABLE material_metadata ENABLE ROW LEVEL SECURITY;

-- Permissive policies (service role key bypasses RLS; adjust for user-level auth)
CREATE POLICY "Allow all for service role" ON scenes FOR ALL USING (true);

CREATE POLICY "Allow all for service role" ON scene_products FOR ALL USING (true);

CREATE POLICY "Allow all for service role" ON material_metadata FOR ALL USING (true);