# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

**BRAHMO Derivability Scoring System** — a full-stack app that pre-computes a derivability score (0.0–1.0) for each knowledge node and classifies it `DERIVABLE` / `PARTIALLY_DERIVABLE` / `NON_DERIVABLE`, **entirely without runtime LLM calls**. The point is to exclude knowledge the AI already knows ("What is a TKR?") from the AI context to save tokens, while never excluding org-specific or safety-critical knowledge. All scoring is heuristic (spaCy NER + regex) + TF-IDF (scikit-learn); the database stores the result so query time is `WHERE derivability_score < threshold` with zero computation.

## Commands

Backend (run from `backend/`, after activating the venv):

```bash
cd backend
python -m venv venv && venv\Scripts\activate          # Windows; venv only needs creating once
pip install -r requirements.txt
python -m spacy download en_core_web_sm               # REQUIRED — scorer raises at import without it
cp .env.example .env                                  # then fill in Supabase creds
uvicorn app.main:app --reload --port 8000             # API + Swagger docs at /docs
```

Tests (from `backend/`):

```bash
python -m pytest tests/ -v                            # all
python -m pytest tests/test_heuristic_scorer.py -v    # one file
python -m pytest tests/test_surprise_nodes.py -v      # the "surprise" ad-hoc-content scoring tests
```

Frontend (from `frontend/`):

```bash
npm install
npm run dev                                           # Vite dev server on :5173, proxies /api → :8000
npm run build
```

Database: run `database/schema.sql` then `database/seed.sql` in the Supabase SQL Editor. Seed loads 30 nodes; verify with `SELECT COUNT(*) FROM knowledge_nodes` → 30.

## Architecture

Request flow: **React (`frontend/src`) → `/api/*` (proxied) → FastAPI router (`backend/app/api/routers/nodes.py`) → `ScoringService` → scorers + `SupabaseService` + `ValidationEngine`.**

- `ScoringService` (`app/services/scoring_service.py`) is the single orchestration layer — every endpoint goes through it. It builds a `HybridScorer` per-org using floors from `organizations.config`.
- `HybridScorer` (`app/scorer/hybrid_scorer.py`) is the core. It fuses `0.7 × heuristic + 0.3 × tfidf`, applies a **type safety ceiling**, classifies, and for partials calls `DeltaExtractor`. The `algorithm` param (`hybrid` | `heuristic` | `tfidf`) selects which raw score is used.
- `HeuristicScorer` (`app/scorer/heuristic_scorer.py`) starts at base 0.50 and adds/subtracts signal weights (def. patterns +0.30, org names −0.40, person names via spaCy PERSON −0.30, incidents −0.30, patient refs −0.30, dates −0.20, etc.). Each signal is a `ScoringSignal` carrying its matched text for explainability.
- `TFIDFScorer` (`app/scorer/embedding_scorer.py`) cosine-compares content to `REFERENCE_CORPUS` (`app/scorer/reference_corpus.py`). High similarity to general medical knowledge → more derivable.
- `ValidationEngine` (`app/validators/validation_engine.py`) compares scored `derivability_class` against the `expected_derivability` ground-truth column from seed data to compute the confusion matrix, precision/recall/F1, and the threshold sweep.

### Key invariants — preserve these when editing

- **Classification thresholds are not symmetric.** A node is `DERIVABLE` if `score >= threshold` (default 0.7), `PARTIALLY_DERIVABLE` if `0.40 <= score < threshold`, else `NON_DERIVABLE`. The `0.40` partial floor is hardcoded in both `HybridScorer._classify` and the metrics/token-savings/threshold code in `ScoringService` and `ValidationEngine` — change all of them together.
- **Type safety floors are a hard ceiling, applied after fusion**: `CONSTRAINT` ≤ 0.50, `ANTI_PATTERN` ≤ 0.60, `DECISION`/`FACT` uncapped. Defaults live in `DEFAULT_TYPE_FLOORS` but are overridden per-org from `OrgConfig`. This is the safety mechanism — safety-critical nodes can never be classified `DERIVABLE` at default threshold.
- **Design bias: false positives (excluding org-specific knowledge) are far worse than false negatives.** `find_optimal_threshold` maximizes F1 subject to precision ≥ 0.85. When in doubt, score lower (keep the node).
- **Token math**: `DERIVABLE` saves `tokens_full`; `PARTIALLY_DERIVABLE` saves `tokens_full - tokens_delta` (delta kept); `NON_DERIVABLE` saves nothing.

### Conventions / gotchas

- spaCy model (`en_core_web_sm`) loads once at module import in `heuristic_scorer.py` and **raises if missing** — the download step is not optional.
- `SupabaseService` reads `SUPABASE_URL` / `SUPABASE_KEY` from `backend/.env` via `load_dotenv()`; a missing key raises at client creation. DB-backed endpoints and `test_api.py` need a live Supabase; the pure scorer tests do not.
- The scoring service is a lazily-initialized singleton (`get_service()` in the router).
- Two identical `requirements.txt` exist (repo root and `backend/`); the README installs from `backend/`. Keep them in sync.
- All scorer/service modules use `from __future__ import annotations` and PEP 604 (`X | None`, `list[...]`) type hints. Pydantic v2 schemas live in `app/models/schemas.py` and back both DB rows (`KnowledgeNode`) and API request/response shapes.
- Frontend talks to the backend only through `frontend/src/api/client.js`; component data flows from `App.jsx`.
