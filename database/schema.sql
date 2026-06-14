-- ============================================================
-- BRAHMO Derivability Scoring System — Database Schema
-- Run this in Supabase SQL Editor FIRST, then run seed.sql
-- ============================================================

-- Organizations table
CREATE TABLE IF NOT EXISTS organizations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    config JSONB DEFAULT '{}'
);

-- Knowledge nodes table
CREATE TABLE IF NOT EXISTS knowledge_nodes (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL REFERENCES organizations(id),
    type TEXT NOT NULL CHECK (type IN ('CONSTRAINT', 'DECISION', 'ANTI_PATTERN', 'FACT')),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    importance DECIMAL(3,2) NOT NULL,
    derivability_score DECIMAL(3,2) DEFAULT 0.5,
    derivability_class TEXT DEFAULT 'UNKNOWN' CHECK (derivability_class IN (
        'DERIVABLE', 'PARTIALLY_DERIVABLE', 'NON_DERIVABLE', 'UNKNOWN'
    )),
    non_derivable_portion TEXT,
    expected_derivability TEXT,
    expected_score_range TEXT,
    department TEXT,
    tokens_full INTEGER,
    tokens_delta INTEGER,
    scoring_reason TEXT,
    type_floor_applied BOOLEAN DEFAULT FALSE,
    upload_batch TEXT,                              -- tags nodes added via file upload (NULL = seed/manual; never deleted by "Delete Recent Upload")
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_org_id ON knowledge_nodes(org_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_type ON knowledge_nodes(type);
CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_derivability_score ON knowledge_nodes(derivability_score);
CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_derivability_class ON knowledge_nodes(derivability_class);
CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_upload_batch ON knowledge_nodes(upload_batch);
