-- ============================================================
-- BRAHMO — Template for ADDING MORE NODES (datasets)
-- ============================================================
-- HOW TO USE:
--   1. Copy a block below, edit the values, paste as many as you want.
--   2. Run this file in the Supabase SQL Editor.
--   3. In the dashboard, click "Rescore All" (or POST /api/score-all).
--      The new nodes are scored and appear alongside the existing ones
--      automatically — no code change, no new column needed.
--
-- You do NOT need to set derivability_score / derivability_class /
-- scoring_reason — those are filled in by the scorer when you rescore.
-- ============================================================


-- ------------------------------------------------------------
-- REQUIRED columns (minimum to insert a scoreable node)
-- ------------------------------------------------------------
--   id          TEXT  — must be UNIQUE (e.g. 'NEW-01'); reusing an id is ignored
--   org_id      TEXT  — must already exist in `organizations` (use 'supra')
--   type        TEXT  — one of: CONSTRAINT | DECISION | ANTI_PATTERN | FACT
--   title       TEXT
--   content     TEXT  — the text that actually gets scored
--   importance  NUMERIC(3,2) — 0.00 to 1.00 (business importance, not derivability)

-- Minimal example — enough to be scored and shown in the table:
INSERT INTO knowledge_nodes (id, org_id, type, title, content, importance) VALUES
('NEW-01', 'supra', 'FACT', 'What is Hypertension',
 'Hypertension, also known as high blood pressure, is a chronic condition in which blood pressure in the arteries is persistently elevated. Normal is below 120/80 mmHg.',
 0.30)
ON CONFLICT (id) DO NOTHING;


-- ------------------------------------------------------------
-- OPTIONAL columns (unlock extra dashboard features)
-- ------------------------------------------------------------
--   tokens_full           INTEGER — needed for the Token Savings panel to count this node
--   tokens_delta          INTEGER — tokens kept for a PARTIALLY_DERIVABLE node (0 if none)
--   expected_derivability TEXT    — DERIVABLE | PARTIALLY_DERIVABLE | NON_DERIVABLE
--                                   set this ONLY if you know the "right answer" — it is
--                                   used by the Validation Matrix (precision/recall/F1)
--   expected_score_range  TEXT    — e.g. '0.85-0.95' (display only)
--   department            TEXT    — e.g. 'ortho' (display only)

-- Full example — counts toward token savings AND validation accuracy:
INSERT INTO knowledge_nodes
  (id, org_id, type, title, content, importance,
   expected_derivability, expected_score_range, department, tokens_full, tokens_delta)
VALUES
('NEW-02', 'supra', 'DECISION', 'Supra Cardiology BP Protocol',
 'Supra Cardiology targets BP < 130/80 for diabetic patients. First-line: Telmisartan 40mg. Decision by Dr. Anand, March 2026.',
 0.85, 'NON_DERIVABLE', '0.02-0.10', 'cardiology', 60, NULL)
ON CONFLICT (id) DO NOTHING;


-- ------------------------------------------------------------
-- VERIFY after running:
--   SELECT COUNT(*) FROM knowledge_nodes;           -- new total
--   SELECT id, type, title FROM knowledge_nodes ORDER BY created_at DESC LIMIT 10;
-- ------------------------------------------------------------
