-- ============================================================
-- MIGRATION — Enables the "Delete Recent Upload" feature
-- ============================================================
-- Run this ONCE in the Supabase SQL Editor on your existing
-- database. It adds a column that tags each uploaded batch so
-- the dashboard can delete only the most recently uploaded file's
-- nodes, while leaving the original seed nodes untouched.
--
-- Existing rows (your original 30 seed nodes) get upload_batch = NULL,
-- which means they are NEVER affected by "Delete Recent Upload".
--
-- ⚠️ File uploads will fail until this column exists, because the
--    upload endpoint writes an upload_batch value on every insert.
-- ============================================================

ALTER TABLE knowledge_nodes ADD COLUMN IF NOT EXISTS upload_batch TEXT;

CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_upload_batch
    ON knowledge_nodes(upload_batch);
