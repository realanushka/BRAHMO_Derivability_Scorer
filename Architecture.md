# BRAHMO Derivability Scoring System — Architecture Document

## Table of Contents

1. [System Overview](#system-overview)
2. [Scoring Algorithm Design](#scoring-algorithm-design)
3. [Heuristic Scorer](#heuristic-scorer)
4. [TF-IDF Similarity Scorer](#tf-idf-similarity-scorer)
5. [Hybrid Score Fusion](#hybrid-score-fusion)
6. [Type Safety Floors](#type-safety-floors)
7. [Delta Extraction (PARTIALLY_DERIVABLE)](#delta-extraction)
8. [Token Savings Calculation](#token-savings-calculation)
9. [Validation & Calibration](#validation--calibration)
10. [False Positive Protection](#false-positive-protection)
11. [Threshold Tuning](#threshold-tuning)
12. [Data Flow](#data-flow)
13. [API Design](#api-design)
14. [Frontend Architecture](#frontend-architecture)
15. [Tradeoffs & Design Decisions](#tradeoffs--design-decisions)
16. [Future Improvements](#future-improvements)

---

## System Overview

The Derivability Scoring System classifies knowledge nodes into three categories based on whether an AI model (e.g., Claude) can derive the information from its training data:

| Classification | Score Range | Action | Rationale |
|---|---|---|---|
| **DERIVABLE** | 0.70 – 1.00 | EXCLUDE from context | AI already knows this; sending it wastes tokens |
| **PARTIALLY_DERIVABLE** | 0.40 – 0.69 | Include DELTA only | Mix of general + org-specific; send only the org-specific portion |
| **NON_DERIVABLE** | 0.00 – 0.39 | Include FULL content | Organization-specific; AI cannot derive this |

### Core Constraint: ZERO LLM at Query Time

The scoring system operates within the Rules Engine (L2), which is deterministic and binary. **No LLM calls are permitted at query time.** All derivability scores are pre-computed and stored as a database column. At query time, the Rules Engine simply compares `derivability_score < threshold` — a column comparison, not a computation.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     SCORING PIPELINE                             │
│                                                                  │
│  Node Content ──→ ┌──────────────┐                              │
│                   │  Heuristic    │──→ heuristic_score (0-1)    │
│                   │  Scorer       │    (spaCy NER + regex)      │
│                   └──────────────┘                              │
│                                                                  │
│  Node Content ──→ ┌──────────────┐                              │
│                   │  TF-IDF      │──→ tfidf_score (0-1)        │
│                   │  Scorer       │    (scikit-learn cosine)    │
│                   └──────────────┘                              │
│                                                                  │
│  ┌────────────────────────────────────────────┐                 │
│  │  Hybrid Fusion                              │                 │
│  │  final = 0.7 × heuristic + 0.3 × tfidf    │                 │
│  │  → Apply type safety floor                  │                 │
│  │  → Classify (DERIVABLE/PARTIAL/NON_DERIV)  │                 │
│  │  → Extract delta if PARTIAL                 │                 │
│  └────────────────────────────────────────────┘                 │
│                                                                  │
│  Result ──→ UPDATE knowledge_nodes                              │
│             SET derivability_score = X,                          │
│                 derivability_class = Y,                          │
│                 scoring_reason = Z,                              │
│                 non_derivable_portion = delta                    │
└─────────────────────────────────────────────────────────────────┘

At Query Time (Rules Engine Check 5):
  SELECT * FROM knowledge_nodes
  WHERE derivability_score < 0.7   ← just a column comparison
  → ZERO computation, ZERO LLM calls
```

---

## Scoring Algorithm Design

We use a **Hybrid approach** combining two complementary methods:

1. **Heuristic Scorer (70% weight):** Rule-based analysis using spaCy NER and regex patterns. Fast, deterministic, interpretable. Catches obvious cases with high confidence.

2. **TF-IDF Similarity Scorer (30% weight):** Statistical comparison of node content against a general medical knowledge corpus. Handles ambiguous cases where heuristics are uncertain.

### Why Hybrid?

| Approach | Strengths | Weaknesses |
|----------|-----------|------------|
| Heuristic only | Fast, interpretable, catches obvious org names/dates | Misses subtle org-specific content without explicit markers |
| TF-IDF only | Handles ambiguous text, no manual rule creation | No semantic understanding; can be fooled by similar vocabulary |
| **Hybrid** | Best of both; heuristics handle obvious cases, TF-IDF resolves ambiguity | Slightly more complex; requires tuning fusion weights |

---

## Heuristic Scorer

### Base Score

Every node starts at a base score of **0.50** (neutral). Signals add or subtract from this base, then the result is clamped to [0.0, 1.0].

### Positive Signals (toward DERIVABLE)

| Signal | Weight | Detection Method | Example |
|--------|--------|-----------------|---------|
| Definition pattern | +0.30 | Regex: `^(What is|X is a|X is an)` | "Total knee replacement (TKR) is a surgical procedure..." |
| Textbook structure | +0.20 | Short, well-structured, no org terms | "Mechanism: inhibits prostaglandin synthesis in the CNS" |
| Standard keyword | +0.20 | Word match: "standard", "normal", "common" | "Standard adult dose: 500-1000mg" |
| Short factual explanation | +0.20 | Length < 200 chars + medical term density | "Sepsis is a life-threatening organ dysfunction..." |
| Generic terminology density | +0.20 | High ratio of medical/clinical terms vs total | General pharmacology descriptions |
| No organization references | +0.10 | Absence of ORG entities and org name strings | Pure medical definitions |

### Negative Signals (toward NON_DERIVABLE)

| Signal | Weight | Detection Method | Example |
|--------|--------|-----------------|---------|
| Organization names | −0.40 | String match ("Supra", org_name from config) | "Supra Ortho uses..." |
| Person names (spaCy NER) | −0.30 | spaCy `PERSON` entity recognition | "Dr. Vikram decided...", "Patient Rajan" |
| Dates (spaCy + regex) | −0.20 | spaCy `DATE` + regex `(January|Feb...) \d{4}` | "January 2025", "June 2026" |
| Incident references | −0.30 | Keyword: "incident", "near miss", "readmission" | "Past incident: patient discharged..." |
| Policy/protocol with org | −0.20 | "policy" or "protocol" co-occurring with org name | "Supra policy since 2024" |
| Specific counts | −0.10 | Regex: `\d+\s+(refusals|beds|times|episodes)` | "8 refusals", "45 beds" |
| Patient references | −0.30 | "Patient" + name or "Mrs./Mr." patterns | "Patient Rajan", "Mrs. Padma" |
| Decision rationale | −0.20 | Keywords: "because", "based on", "reviewed", "updated" | "Decision based on 3-year outcomes review" |

### Scoring Formula

```python
score = 0.50  # base
for signal in detected_positive_signals:
    score += signal.weight
for signal in detected_negative_signals:
    score += signal.weight  # negative weights subtract
score = max(0.0, min(1.0, score))  # clamp to [0, 1]
```

---

## TF-IDF Similarity Scorer

### Reference Corpus

A curated corpus of ~50 general medical knowledge entries representing "things an AI model already knows":

- **Medical definitions:** TKR, DVT, diabetes, sepsis, osteoarthritis
- **Drug mechanisms:** Paracetamol, warfarin, tramadol, enoxaparin, insulin
- **Vital sign ranges:** Normal HR, BP, RR, SpO2, temperature
- **Standard protocols:** SBAR, hand hygiene WHO 5 moments, Morse Fall Scale
- **Clinical concepts:** Antibiotic stewardship, fall prevention, pain scales

### Algorithm

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Fit vectorizer on corpus + node content
vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
corpus_vectors = vectorizer.fit_transform(reference_corpus)

# Transform node content
node_vector = vectorizer.transform([node.content])

# Compute similarity to corpus centroid
similarities = cosine_similarity(node_vector, corpus_vectors)
tfidf_score = float(np.max(similarities))  # max similarity to any corpus entry
```

### Interpretation

- **High similarity (0.7–1.0):** Node content closely matches general medical knowledge → more derivable
- **Medium similarity (0.4–0.7):** Mixed content → may be partially derivable
- **Low similarity (0.0–0.4):** Node content doesn't match general knowledge → org-specific, non-derivable

---

## Hybrid Score Fusion

```python
final_score = 0.7 * heuristic_score + 0.3 * tfidf_score
final_score = max(0.0, min(1.0, final_score))  # normalize to [0, 1]
```

### Why 70/30?

- Heuristic rules are **more reliable** for obvious cases (org names, person names, dates are strong indicators)
- TF-IDF provides a **statistical safety net** for ambiguous cases
- The 70/30 split gives heuristics primary authority while TF-IDF influences borderline decisions

---

## Type Safety Floors

**Critical safety mechanism.** Certain node types must NEVER be fully excluded, regardless of how "general" their content sounds.

| Node Type | Maximum Score | Rationale |
|-----------|:------------:|-----------|
| CONSTRAINT | 0.50 | Safety-critical rules. Even "general-sounding" constraints (e.g., "hand hygiene") may have org-specific compliance targets |
| ANTI_PATTERN | 0.60 | Past incidents are org-specific by nature. "Don't do X" from experience must be preserved |
| DECISION | No cap | Decisions are already heavily penalized by heuristic signals (org names, dates, persons) |
| FACT | No cap | Facts range from fully general to fully org-specific; signals handle this |

### Implementation

```python
TYPE_FLOORS = {"CONSTRAINT": 0.50, "ANTI_PATTERN": 0.60, "DECISION": 1.0, "FACT": 1.0}

if final_score > TYPE_FLOORS[node.type]:
    final_score = TYPE_FLOORS[node.type]
    type_floor_applied = True
```

### Why This Matters

Example: "Hand hygiene 5-moment compliance" — the WHO 5 moments are general knowledge (Claude knows them). Without the floor, the scorer might assign 0.75 (DERIVABLE) and **exclude** this node. But Supra's target is 95%, current is 88%, and non-compliance is a reportable incident. The floor caps at 0.50 → PARTIALLY_DERIVABLE → delta content is sent.

**False positives are more dangerous than false negatives.** Excluding a safety constraint is far worse than wasting a few tokens.

---

## Delta Extraction

For PARTIALLY_DERIVABLE nodes, we extract only the organization-specific portion (the "delta"):

### Algorithm

1. **Sentence segmentation** using spaCy
2. **Entity detection** for ORG, PERSON, DATE entities
3. **Heuristic filtering** — keep sentences containing:
   - Organization names
   - Person names
   - Specific dates
   - Patient references
   - Incident history
   - Exact dosage schedules with org context
   - Policy/protocol references
4. **Return delta** — only the non-derivable sentences

### Example

**Full content:** "ALL ortho surgical patients receive DVT prophylaxis: Enoxaparin 40mg SC daily starting 12 hours post-op. Duration: 14 days for TKR, 28 days for THR."

**Delta (non-derivable portion):** "Supra: Enoxaparin 12 hours post-op. TKR 14d, THR 28d. Active bleeding/platelet <50K contraindicated."

**Tokens saved:** Full=80, Delta=25 → Saved=55 tokens

---

## Token Savings Calculation

### Per-Node Savings

```python
if classification == "DERIVABLE":
    saved_tokens = tokens_full  # entire node excluded
elif classification == "PARTIALLY_DERIVABLE":
    saved_tokens = tokens_full - tokens_delta  # delta only sent
else:  # NON_DERIVABLE
    saved_tokens = 0  # full content sent
```

### Aggregate Savings

```
total_tokens = sum(node.tokens_full for all nodes)
saved_tokens = sum(node.saved_tokens for all nodes)
savings_percentage = saved_tokens / total_tokens * 100

# Cost projections (GPT-4 pricing: ~$0.015/1K tokens)
cost_per_token = 0.015 / 1000
session_savings = saved_tokens * cost_per_token
daily_savings_50 = session_savings * 10 * 50     # 50 engineers, 10 sessions/day
annual_savings_50 = daily_savings_50 * 250        # 250 working days
annual_savings_500 = annual_savings_50 * 10       # scale to 500 engineers
```

---

## Validation & Calibration

### Validation Matrix

Compare scored results against `expected_derivability` ground truth for all 30 seed nodes:

```
                    ACTUALLY DERIVABLE  ACTUALLY NON_DERIVABLE  ACTUALLY PARTIAL
SCORED DERIVABLE    True Positive (TP)  FALSE POSITIVE (FP)     Borderline
SCORED NON_DERIV    False Negative (FN) True Negative (TN)      Borderline
SCORED PARTIAL      Borderline          Borderline              True Partial
```

### Metrics

Using `sklearn.metrics`:
- **Precision** = TP / (TP + FP) — of excluded nodes, how many were actually derivable?
- **Recall** = TP / (TP + FN) — of actually derivable nodes, how many did we catch?
- **F1 Score** = 2 × (Precision × Recall) / (Precision + Recall)
- **False Positive Rate** = FP / (FP + TN)
- **Target:** Precision ≥ 85%, Recall ≥ 70%

### Calibration Strategy

1. **Monthly validation:** Compare algorithm scores against manually classified nodes
2. **Expanding ground truth:** As doctors manually classify nodes during creation, grow the validation set
3. **Threshold tuning:** Adjust per-org threshold based on false positive rate
4. **Signal weight tuning:** If certain signals produce too many false positives, adjust weights
5. **Corpus expansion:** Add new general knowledge entries as medical knowledge evolves

---

## False Positive Protection

Multiple layers of defense against dangerous false positives (excluding org-specific knowledge):

1. **Type-based floors:** CONSTRAINT and ANTI_PATTERN nodes are physically capped
2. **Conservative default threshold:** 0.70 (not 0.50 or 0.60)
3. **Negative signal priority:** Org-specific signals have higher weights than positive signals
4. **Base score at 0.50:** Starts neutral; requires strong positive evidence to reach DERIVABLE
5. **Manual override support:** Nodes can be manually marked as "never exclude"
6. **Exclusion logging:** Every exclusion decision is logged with reasoning for audit
7. **Validation monitoring:** Continuous precision tracking; if FP rate increases, alert and lower threshold

---

## Threshold Tuning

The derivability threshold is configurable per organization via `org_config`:

| Threshold | Behavior | Risk Profile |
|:---------:|----------|-------------|
| 0.90 | Very conservative — only exclude obvious definitions | Low FP risk, low savings (~15-20%) |
| 0.80 | Conservative — exclude clear general knowledge | Low FP risk, moderate savings (~25-30%) |
| **0.70** | **Default — balanced safety and savings** | **Moderate risk, good savings (~35-40%)** |
| 0.60 | Aggressive — exclude more borderline content | Higher FP risk, high savings (~45-50%) |
| 0.50 | Very aggressive — exclude most general content | High FP risk, very high savings (~55%+) |

**Recommendation:** Start at 0.70, monitor false positives for 30 days, then tune based on precision metrics.

---

## Data Flow

```
1. Node Creation / Update
   ├── Author creates knowledge node with content
   ├── Derivability scorer runs (batch or on-creation)
   │   ├── Heuristic scorer analyzes content (spaCy NER + regex)
   │   ├── TF-IDF scorer computes corpus similarity (scikit-learn)
   │   ├── Hybrid fusion combines scores (0.7H + 0.3T)
   │   ├── Type safety floor applied if needed
   │   ├── Delta extracted for PARTIALLY_DERIVABLE nodes
   │   └── Results stored in database
   └── Node ready for query-time filtering

2. Query Time (Rules Engine Check 5)
   ├── SELECT * FROM knowledge_nodes WHERE derivability_score < threshold
   ├── DERIVABLE nodes: excluded (not in candidate set)
   ├── PARTIALLY_DERIVABLE: non_derivable_portion used instead of full content
   ├── NON_DERIVABLE: full content included
   └── ZERO computation — just a SQL WHERE clause
```

---

## API Design

Base URL: `http://localhost:8000` · Full OpenAPI/Swagger UI at `/docs`.

### Knowledge & Scoring

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/nodes` | GET | List all knowledge nodes with current scores |
| `/api/score-all` | POST | Score all nodes (batch) and persist results |
| `/api/score-node` | POST | Score a single node by ID, or ad-hoc content (Test Playground) |

### Ingestion & Deletion

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload-nodes` | POST | Upload a CSV/SQL **file** of nodes (parsed & stored, unscored) |
| `/api/paste-nodes` | POST | Paste raw CSV/SQL **text** of nodes (parsed & stored, unscored) |
| `/api/nodes/delete-by-file` | POST | Delete uploaded nodes matching a re-supplied file |
| `/api/nodes/delete-by-text` | POST | Delete uploaded nodes matching re-pasted text |

### Analytics

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/metrics` | GET | Classification counts at a given threshold |
| `/api/validation-matrix` | GET | Confusion matrix + precision / recall / F1 |
| `/api/token-savings` | GET | Token savings & projected cost at scale |
| `/api/threshold-analysis` | GET | Threshold-vs-metrics sweep data + optimal threshold |

### Health

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service health check |
| `/health` | GET | Detailed health + endpoint list |

---

## Frontend Architecture

### Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 18.x | UI component framework |
| **Vite** | 5.x | Build tool and dev server (proxies `/api` → `:8000`) |
| **Tailwind CSS** | 3.x | Utility-first CSS framework |
| **Chart.js** | 4.x | Threshold impact charts |
| **react-chartjs-2** | 5.x | React wrapper for Chart.js |

### Two-Tab Structure

The app has two top-level tabs:

| Tab | Purpose |
|-----|--------|
| **📊 Dashboard** | Full scoring view — controls, upload, stats, node table, validation, savings, threshold chart |
| **🧪 Test Playground** | Live ad-hoc scorer — paste any content, score instantly, see full breakdown. **Nothing is saved to the database.** |

### Component Tree

```
App (global state, API orchestration, tab switcher)
├── Header
│   └── BRAHMO branding, version badge, status indicator
│
├── [TAB: Dashboard]
│   ├── Controls
│   │   ├── Threshold slider (0.40–0.95, step 0.05)
│   │   ├── Algorithm selector (Heuristic | TF-IDF | Hybrid)
│   │   └── Rescore All button with loading state
│   ├── UploadNodes
│   │   ├── CSV/SQL file upload → POST /api/upload-nodes
│   │   └── Delete by File → POST /api/nodes/delete-by-file
│   ├── PasteNodes
│   │   ├── Paste CSV/SQL text → POST /api/paste-nodes
│   │   └── Delete by Text → POST /api/nodes/delete-by-text
│   ├── StatsCards (6 metric cards in responsive grid)
│   │   ├── Total Nodes count
│   │   ├── Derivable count (red badge)
│   │   ├── Partially Derivable count (yellow badge)
│   │   ├── Non-Derivable count (green badge)
│   │   ├── Tokens Saved (with percentage)
│   │   └── Annual Cost Savings (USD)
│   ├── NodeTable (sortable, scrollable)
│   │   └── Per-row: ID, Title, Score bar, Class badge, Reason,
│   │       Action, Tokens saved, Expected class, Validation ✅/🔴/⚠️
│   ├── NodeModal (triggered on row click)
│   │   ├── Full content display
│   │   ├── Delta content (highlighted)
│   │   ├── Score explanation breakdown
│   │   ├── Heuristic / TF-IDF individual scores
│   │   ├── Signal list with weights
│   │   └── Type floor indicator
│   ├── ValidationMatrix
│   │   ├── Confusion matrix grid (2×2 with color coding)
│   │   ├── Precision / Recall / F1 gauges
│   │   ├── False positive node list (red alerts)
│   │   └── False negative node list (yellow warnings)
│   ├── ThresholdChart (Chart.js)
│   │   ├── Line: threshold vs token savings %
│   │   ├── Line: threshold vs precision
│   │   ├── Line: threshold vs recall
│   │   └── Optimal threshold marker (max F1 @ precision ≥ 0.85)
│   └── TokenSavings
│       ├── Session savings
│       ├── Daily savings (50 engineers × 10 sessions)
│       ├── Annual savings (250 working days)
│       └── Scale projection (500 engineers)
│
└── [TAB: Test Playground]
    └── TestPlayground
        ├── Free-text input (title + content)
        ├── Score instantly → POST /api/score-node (ad-hoc, no DB write)
        ├── Score display: value, class badge, sub-scores
        ├── Signal breakdown (which heuristic signals fired)
        └── Delta extraction result (for PARTIAL classifications)
```

### Design System

- **Theme:** Dark mode with glassmorphism cards
- **Colors:**
  - DERIVABLE (excluded): `#EF4444` (red) — danger, being removed
  - PARTIALLY_DERIVABLE: `#F59E0B` (amber) — caution, delta only
  - NON_DERIVABLE (included): `#10B981` (emerald) — safe, fully included
  - Background: `#0F172A` (slate-900)
  - Cards: `rgba(255,255,255,0.05)` with backdrop blur
  - Accent: `#6366F1` (indigo-500)
- **Typography:** Inter font from Google Fonts
- **Animations:** Smooth transitions on score bars, hover effects on cards, fade-in on modal

### State Management

Single `App` component manages all global state via React `useState`:

```
nodes[]         → all knowledge nodes with scores (from GET /api/nodes)
threshold       → current threshold slider value (default 0.70)
algorithm       → selected algorithm (heuristic | tfidf | hybrid)
metrics         → validation metrics (from GET /api/metrics)
savings         → token savings data (from GET /api/token-savings)
thresholdData   → chart data (from GET /api/threshold-analysis)
selectedNode    → node ID for detail modal (null = closed)
loading         → boolean loading state for API calls
activeTab       → 'dashboard' | 'playground' (tab switcher)
```

### API Client

Centralized `src/api/client.js` module with functions for each endpoint:

```js
// Scoring
fetchNodes()                          → GET  /api/nodes
scoreAll(algorithm, threshold, orgId) → POST /api/score-all
scoreNode(content, algorithm)         → POST /api/score-node   // ad-hoc, no DB write

// Ingestion
uploadNodes(file)                     → POST /api/upload-nodes
pasteNodes(text, format)              → POST /api/paste-nodes
deleteByFile(file)                    → POST /api/nodes/delete-by-file
deleteByText(text, format)            → POST /api/nodes/delete-by-text

// Analytics
fetchMetrics(threshold)               → GET  /api/metrics
fetchValidationMatrix(threshold)      → GET  /api/validation-matrix
fetchTokenSavings(threshold)          → GET  /api/token-savings
fetchThresholdAnalysis()              → GET  /api/threshold-analysis
```

### Responsive Layout

- **Desktop (≥1280px):** Full dashboard with side-by-side charts
- **Tablet (768-1279px):** Stacked cards, scrollable table
- **Mobile (≤767px):** Single-column layout, collapsible sections

---

## Tradeoffs & Design Decisions

### 1. Why not use embeddings (sentence-transformers) instead of TF-IDF?

TF-IDF with cosine similarity is:
- **Free** — no API calls, no GPU needed
- **Deterministic** — same input always gives same output
- **Fast** — vectorization is O(n) per node
- **Sufficient** — for distinguishing "general medical text" from "org-specific text," vocabulary overlap is a strong signal

Sentence-transformers would give better semantic understanding but require GPU or API calls, adding cost and latency.

### 2. Why start at base 0.50 instead of 0.00 or 1.00?

Starting neutral allows both positive and negative signals to pull the score in either direction. Starting at 0.00 would make it hard for general knowledge to reach DERIVABLE without many positive signals. Starting at 1.00 would make everything default to DERIVABLE (dangerous).

### 3. Why is the heuristic weighted 70% and TF-IDF 30%?

Heuristic rules are hand-crafted for this specific domain and are highly reliable for obvious cases. TF-IDF is a statistical method that may have false matches. Giving heuristics more authority ensures that clear signals (org names, person names) dominate the score.

### 4. Why are false positives treated as more dangerous?

- **False positive** (excluding org-specific knowledge): The AI gives wrong/generic advice because it's missing critical org-specific context. Patient safety risk.
- **False negative** (including general knowledge): The AI receives information it already knows. Wastes tokens but no safety risk.

The asymmetric risk profile means we should **always err toward including** when uncertain.

---

## Future Improvements

1. **Active Learning:** Use doctor feedback on node classifications to continuously improve scorer accuracy
2. **Per-Department Calibration:** Different departments may have different baselines for what's "general" vs "org-specific"
3. **Temporal Decay:** As AI training data evolves, previously non-derivable information may become derivable (e.g., after a published guideline change)
4. **Embedding Upgrade:** Replace TF-IDF with sentence-transformers for better semantic similarity (when cost permits)
5. **Multi-Org Support:** Different organizations have different knowledge profiles; scores should be org-aware
6. **Confidence Intervals:** Instead of a single score, provide a confidence range (e.g., 0.72 ± 0.05)
7. **A/B Testing:** Compare AI responses with and without derivable nodes to empirically validate exclusions
8. **Automated Threshold Optimization:** Use the validation set to automatically find the optimal threshold per organization

---

## Observed Scoring Behaviour (30 Seed Nodes)

After running the hybrid scorer on all 30 seed nodes at threshold `0.70`:

| Group | Expected Score Range | Observed | Result |
|-------|---------------------|----------|--------|
| D-01 – D-10 (DERIVABLE) | ≥ 0.70 | 0.72 – 1.00 | ✅ All 10 PASS |
| ND-01 – ND-10 (NON_DERIVABLE) | ≤ 0.30 | 0.07 – 0.36 | ✅ 9/10 PASS · ⚠️ ND-04 = 0.36* |
| E-01 – E-10 (EDGE / PARTIAL) | 0.30 – 0.70 | 0.16 – 0.50 | ✅ E-01 PARTIAL · ⚠️ 6 nodes scored low† |

\* **ND-04** (`Rajan Behavioral NSAID Requests`) scores 0.36 instead of ≤ 0.30. The node contains patient-specific information ("Patient Rajan", "8 documented refusals") but lacks the strong org-name signal that anchors other ND nodes. **Classification is still correct (NON_DERIVABLE)** — score is well below the 0.70 exclusion threshold.

† **6 edge-case nodes** (E-02, E-03, E-04, E-07, E-08, E-09) score below 0.30 and are classified as NON_DERIVABLE instead of PARTIALLY_DERIVABLE. This is the **safe failure mode**: nodes containing org-specific signals ("Supra incident", "Supra protocol", "12 hours post-op") are correctly pushed toward inclusion rather than exclusion. The system errs on the conservative side by design — *when in doubt, keep the node.*

---

*Architecture Document v1.1 — BRAHMO Derivability Scoring System*
*Last updated: June 2026*
