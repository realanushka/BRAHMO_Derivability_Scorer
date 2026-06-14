# SETUP GUIDE: Derivability Scoring Without LLM
## Token Savings Engine: Environment Setup + 30 Categorized Nodes + Scoring Rubric

---

## ENVIRONMENT SETUP

### What You Need Installed

| Tool | Why |
|------|-----|
| Python (3.11+) | Backend + scoring algorithm |
| Node.js (v18+) | Frontend |
| Git | Version control |
| Supabase (free) | PostgreSQL |
| Optional: Embedding API | If using embedding comparison approach |

### Mac Setup

```bash
brew install python@3.11 node

mkdir brahmo-derivability
cd brahmo-derivability && git init

python3 -m venv venv && source venv/bin/activate
pip install fastapi uvicorn supabase python-dotenv

npx create-next-app@latest frontend --typescript --tailwind --app --src-dir --no-import-alias
cd frontend && npm install @supabase/supabase-js

cd ..
echo "SUPABASE_URL=your_url" > .env
echo "SUPABASE_KEY=your_key" >> .env
```

### Supabase Setup

```
1. supabase.com → Create project: "brahmo-derivability"
2. SQL Editor → Run schema + seed data below
3. Verify: SELECT COUNT(*) FROM knowledge_nodes → 30
```

---

## DATABASE SCHEMA

```sql
CREATE TABLE organizations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    config JSONB DEFAULT '{}'
);

CREATE TABLE knowledge_nodes (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL REFERENCES organizations(id),
    type TEXT NOT NULL CHECK (type IN ('CONSTRAINT', 'DECISION', 'ANTI_PATTERN', 'FACT')),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    importance DECIMAL(3,2) NOT NULL,
    derivability_score DECIMAL(3,2) DEFAULT 0.5,   -- computed by scorer
    derivability_class TEXT DEFAULT 'UNKNOWN' CHECK (derivability_class IN (
        'DERIVABLE', 'PARTIALLY_DERIVABLE', 'NON_DERIVABLE', 'UNKNOWN'
    )),
    non_derivable_portion TEXT,     -- for PARTIAL: only this part gets injected
    expected_derivability TEXT,      -- ground truth for validation
    expected_score_range TEXT,       -- e.g., "0.85-0.95" for validation
    department TEXT,
    tokens_full INTEGER,
    tokens_delta INTEGER,           -- tokens if only non_derivable_portion used
    scoring_reason TEXT,            -- human-readable explanation of score
    type_floor_applied BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO organizations (id, name, config) VALUES
('supra', 'Supra Multi-Specialty Hospital',
 '{"derivability_threshold": 0.7, "type_floors": {"CONSTRAINT": 0.50, "ANTI_PATTERN": 0.60, "DECISION": 1.0, "FACT": 1.0}}');
```

---

## SEED DATA — 30 NODES (Categorized by Expected Derivability)

```sql
INSERT INTO knowledge_nodes (id, org_id, type, title, content, importance, expected_derivability, expected_score_range, department, tokens_full, tokens_delta) VALUES

-- ============================================================
-- CLEARLY DERIVABLE (10 nodes) — AI knows from training
-- Expected score: 0.70-0.99
-- ============================================================

('D-01', 'supra', 'FACT', 'What is Total Knee Replacement',
 'Total knee replacement (TKR) is a surgical procedure where damaged knee joint surfaces are replaced with artificial components. Also called total knee arthroplasty (TKA). Most common joint replacement surgery worldwide.',
 0.40, 'DERIVABLE', '0.85-0.95', 'ortho', 65, 0),

('D-02', 'supra', 'FACT', 'Paracetamol Mechanism of Action',
 'Paracetamol (acetaminophen) is an analgesic and antipyretic. Mechanism: inhibits prostaglandin synthesis in the CNS. Standard adult dose: 500-1000mg every 4-6 hours, maximum 4g/day.',
 0.35, 'DERIVABLE', '0.90-0.98', 'medicine', 58, 0),

('D-03', 'supra', 'FACT', 'Normal Adult Vital Sign Ranges',
 'Normal adult vital signs: HR 60-100 bpm, BP 120/80 mmHg (normal), RR 12-20/min, SpO2 >95%, Temperature 36.1-37.2°C. Variations normal for age, activity, medication.',
 0.30, 'DERIVABLE', '0.92-0.99', NULL, 52, 0),

('D-04', 'supra', 'FACT', 'What is Deep Vein Thrombosis',
 'Deep vein thrombosis (DVT) is a blood clot in a deep vein, usually in the legs. Risk factors: surgery, immobility, cancer, pregnancy, obesity. Symptoms: leg swelling, pain, warmth, redness.',
 0.35, 'DERIVABLE', '0.88-0.95', 'ortho', 55, 0),

('D-05', 'supra', 'FACT', 'What is Type 2 Diabetes Mellitus',
 'Type 2 diabetes mellitus is a chronic condition where the body becomes resistant to insulin or does not produce enough. Most common form of diabetes. Risk factors: obesity, sedentary lifestyle, family history.',
 0.30, 'DERIVABLE', '0.90-0.97', 'medicine', 50, 0),

('D-06', 'supra', 'FACT', 'What is Warfarin',
 'Warfarin is an anticoagulant medication that prevents blood clots. Mechanism: inhibits vitamin K-dependent clotting factors. Common brand: Coumadin. Monitored via INR (target usually 2.0-3.0).',
 0.35, 'DERIVABLE', '0.88-0.95', NULL, 52, 0),

('D-07', 'supra', 'FACT', 'Morse Fall Scale Description',
 'The Morse Fall Scale is a rapid assessment tool for fall risk in hospitalized patients. Six items scored: history of falling, secondary diagnosis, ambulatory aid, IV/heparin lock, gait, mental status. Score 0-125.',
 0.40, 'DERIVABLE', '0.82-0.92', NULL, 58, 0),

('D-08', 'supra', 'FACT', 'SBAR Communication Tool',
 'SBAR is a structured communication tool: Situation (what is happening), Background (context), Assessment (your assessment), Recommendation (what you think should happen). Used in healthcare handovers.',
 0.35, 'DERIVABLE', '0.85-0.93', NULL, 50, 0),

('D-09', 'supra', 'FACT', 'What is Sepsis',
 'Sepsis is a life-threatening organ dysfunction caused by dysregulated host response to infection. Criteria: suspected infection + SOFA score ≥2. Septic shock: sepsis + vasopressor requirement + lactate >2.',
 0.40, 'DERIVABLE', '0.85-0.93', 'medicine', 55, 0),

('D-10', 'supra', 'FACT', 'Tramadol Pharmacology',
 'Tramadol is a centrally acting synthetic opioid analgesic. Binds to mu-opioid receptors. Also inhibits serotonin and norepinephrine reuptake. Adult dose: 50-100mg q4-6h. Max: 400mg/day.',
 0.30, 'DERIVABLE', '0.88-0.95', NULL, 52, 0),

-- ============================================================
-- CLEARLY NON-DERIVABLE (10 nodes) — org-specific, AI can't know
-- Expected score: 0.01-0.30
-- ============================================================

('ND-01', 'supra', 'DECISION', 'Supra Paracetamol QDS Post-TKR',
 'Supra Ortho uses Paracetamol 650mg QDS as first-line post-TKR pain management. Escalation: Tramadol 50mg if VAS > 6. AVOID NSAIDs. Decision by Dr. Vikram, January 2025.',
 0.88, 'NON_DERIVABLE', '0.02-0.10', 'ortho', 85, NULL),

('ND-02', 'supra', 'CONSTRAINT', 'Patient Rajan NSAID Ban',
 'ABSOLUTE CONTRAINDICATION: No ibuprofen, no aspirin, no diclofenac for patient Rajan. Cardiac stent (2022) + dual antiplatelet. Previous 8 NSAID refusals documented. Paracetamol ONLY.',
 0.99, 'NON_DERIVABLE', '0.01-0.05', 'ortho', 72, NULL),

('ND-03', 'supra', 'DECISION', 'Zimmer Biomet Implant Preference',
 'Supra Ortho Department uses Zimmer Biomet as preferred TKR implant vendor. Alternative: Smith & Nephew for revision cases only. Decision based on 3-year outcomes review, Dr. Vikram, 2024.',
 0.72, 'NON_DERIVABLE', '0.02-0.08', 'ortho', 68, NULL),

('ND-04', 'supra', 'FACT', 'Rajan Behavioral NSAID Requests',
 'Patient Rajan repeatedly requests Ibuprofen for knee pain despite 8 documented refusals. Family (son) also requests. Counseled each visit. Behavioral note for future visits.',
 0.72, 'NON_DERIVABLE', '0.01-0.05', 'ortho', 62, NULL),

('ND-05', 'supra', 'DECISION', 'Sepsis Protocol v3 Supra',
 'Supra Sepsis Bundle v3 (2026): blood cultures before antibiotics, lactate within 1 HOUR (tightened from v2 3-hour window). Pip-Tazo empiric. Dr. Meera, updated June 2026.',
 0.92, 'NON_DERIVABLE', '0.05-0.15', 'medicine', 75, NULL),

('ND-06', 'supra', 'ANTI_PATTERN', 'TKR Discharge Under 48 Hours',
 'Do NOT discharge TKR patients before 48 hours. Past incident: patient discharged at 36 hours developed DVT at home, emergency readmission. Supra policy since 2024.',
 0.91, 'NON_DERIVABLE', '0.05-0.15', 'ortho', 68, NULL),

('ND-07', 'supra', 'FACT', 'Ortho Ward 45 Beds',
 'Ortho Ward: 45 beds total. 12 post-surgical, 8 traction, 25 general ortho. Usual occupancy 85-90%. Winter peak: 100%+, overflow to Medicine Ward.',
 0.50, 'NON_DERIVABLE', '0.05-0.15', 'ortho', 55, NULL),

('ND-08', 'supra', 'DECISION', 'Ortho Budget 2026',
 'FY 2026 Ortho budget: ₹4.2 Cr. Implants 45%, Staffing 30%, Equipment 15%, Training 10%. New arthroscopy equipment approved Q3.',
 0.70, 'NON_DERIVABLE', '0.01-0.05', 'ortho', 58, NULL),

('ND-09', 'supra', 'FACT', 'Padma Ekadashi Fasting',
 'Mrs. Padma (62F, Type 2 DM) observes Ekadashi fasting twice monthly. Skip Glimepiride on fast days. Continue Metformin with evening meal. 3 hypoglycemia episodes before adjustment.',
 0.82, 'NON_DERIVABLE', '0.01-0.05', 'medicine', 65, NULL),

('ND-10', 'supra', 'FACT', 'Supra Formulary Brands',
 'Supra formulary preferred brands: Paracetamol (Calpol/Dolo), Omeprazole (Omez), Amoxicillin (Mox), Metformin (Glycomet). Use formulary brand unless clinical reason documented.',
 0.65, 'NON_DERIVABLE', '0.08-0.20', NULL, 55, NULL),

-- ============================================================
-- AMBIGUOUS EDGE CASES (10 nodes) — the hard ones
-- Expected: PARTIALLY_DERIVABLE or debatable
-- ============================================================

('E-01', 'supra', 'CONSTRAINT', 'DVT Prophylaxis Protocol',
 'ALL ortho surgical patients receive DVT prophylaxis: Enoxaparin 40mg SC daily starting 12 hours post-op. Duration: 14 days for TKR, 28 days for THR. Contraindication: active bleeding, platelet <50K.',
 0.93, 'PARTIALLY_DERIVABLE', '0.40-0.60', 'ortho', 80, 25),

('E-02', 'supra', 'CONSTRAINT', 'Hand Hygiene 5-Moment Compliance',
 'WHO 5-moment hand hygiene compliance mandatory. Supra target: 95%. Current: 88%. Alcohol-based handrub at every bed. Non-compliance is a reportable incident.',
 0.90, 'PARTIALLY_DERIVABLE', '0.40-0.55', NULL, 55, 22),

('E-03', 'supra', 'CONSTRAINT', 'Fall Risk Morse Scale',
 'Every patient assessed for fall risk using Morse Fall Scale on admission and every shift change. Score >= 45: high risk, bed alarm required. Supra threshold and documentation requirements.',
 0.85, 'PARTIALLY_DERIVABLE', '0.45-0.60', NULL, 55, 20),

('E-04', 'supra', 'DECISION', 'Antibiotic 72-Hour Review',
 'All empiric antibiotics reviewed at 72 hours. De-escalate based on culture results. Supra policy: pharmacy auto-alerts at 72 hours. Non-compliance flagged to department HOD.',
 0.88, 'PARTIALLY_DERIVABLE', '0.35-0.55', NULL, 60, 22),

('E-05', 'supra', 'CONSTRAINT', 'Blood Transfusion Verification',
 'ALL blood transfusions require two-person verification of patient identity, blood type, and unit number. Supra incident 2024: near-miss due to single verification.',
 0.97, 'PARTIALLY_DERIVABLE', '0.35-0.50', NULL, 58, 18),

('E-06', 'supra', 'FACT', 'Supra Emergency Codes',
 'Code Blue: cardiac arrest. Code Red: fire. Code Pink: infant abduction. Code Grey: combative patient. All staff must know codes for their floor.',
 0.70, 'PARTIALLY_DERIVABLE', '0.50-0.65', NULL, 48, 15),

('E-07', 'supra', 'ANTI_PATTERN', 'Verbal Orders Without Confirmation',
 'NEVER accept verbal orders for medication changes without written confirmation within 1 hour. Supra incident 2023: wrong dose from mishearing. Exception: cardiac arrest.',
 0.90, 'PARTIALLY_DERIVABLE', '0.35-0.50', NULL, 55, 20),

('E-08', 'supra', 'DECISION', 'Post-Surgical Pain Escalation',
 'Pain escalation: Step 1 Paracetamol 650mg QDS → Step 2 Tramadol 50mg TDS → Step 3 Morphine 5mg PRN. Skip Step 2 for elderly >75 (fall risk). Supra protocol.',
 0.80, 'PARTIALLY_DERIVABLE', '0.40-0.55', 'ortho', 68, 25),

('E-09', 'supra', 'CONSTRAINT', 'Contrast Allergy Pre-Treatment',
 'Patients with contrast allergy: Hydrocortisone 200mg IV + Chlorpheniramine 10mg IV, 1 hour before procedure. Supra uses this as standard protocol.',
 0.88, 'PARTIALLY_DERIVABLE', '0.45-0.60', 'medicine', 55, 18),

('E-10', 'supra', 'ANTI_PATTERN', 'Insulin Sliding Scale Alone',
 'Do NOT use insulin sliding scale as sole glycemic management. Supra past incident: DKA patient readmitted 48 hours. Always include basal insulin. Sliding scale supplements only.',
 0.87, 'PARTIALLY_DERIVABLE', '0.35-0.50', 'medicine', 58, 20);
```

Set non_derivable_portion for PARTIAL nodes:

```sql
UPDATE knowledge_nodes SET non_derivable_portion = 'Supra: Enoxaparin 12 hours post-op. TKR 14d, THR 28d. Active bleeding/platelet <50K contraindicated.' WHERE id = 'E-01';
UPDATE knowledge_nodes SET non_derivable_portion = 'Supra target 95%, current 88%. Handrub at every bed. Non-compliance is reportable incident.' WHERE id = 'E-02';
UPDATE knowledge_nodes SET non_derivable_portion = 'Supra: score ≥45 = bed alarm. Assessment on admission + every shift. Documentation required.' WHERE id = 'E-03';
UPDATE knowledge_nodes SET non_derivable_portion = 'Supra: pharmacy auto-alerts at 72h. Non-compliance flagged to HOD.' WHERE id = 'E-04';
UPDATE knowledge_nodes SET non_derivable_portion = 'Supra incident 2024: near-miss single verification. Two-person mandatory.' WHERE id = 'E-05';
UPDATE knowledge_nodes SET non_derivable_portion = 'Supra floor-specific assignments for each code.' WHERE id = 'E-06';
UPDATE knowledge_nodes SET non_derivable_portion = 'Supra incident 2023: wrong dose mishearing. 1-hour written confirmation mandatory.' WHERE id = 'E-07';
UPDATE knowledge_nodes SET non_derivable_portion = 'Supra protocol: skip Tramadol step for elderly >75 (fall risk). QDS/TDS specific timing.' WHERE id = 'E-08';
UPDATE knowledge_nodes SET non_derivable_portion = 'Supra standard: Hydrocortisone 200mg + Chlorpheniramine 10mg, 1 hour before.' WHERE id = 'E-09';
UPDATE knowledge_nodes SET non_derivable_portion = 'Supra incident: DKA readmission 48h on sliding scale alone. Mandatory basal insulin.' WHERE id = 'E-10';
```

---

## HEURISTIC SCORING SIGNALS (Reference for your algorithm)

| Signal | Detection Method | Score Impact | Example |
|--------|-----------------|:----------:|---------|
| Org name present | String match ("Supra", org_name) | -0.4 (toward NON_DERIVABLE) | "Supra uses..." |
| Person name present | NER or pattern ("Dr. X", "Patient Y") | -0.3 | "Dr. Vikram decided" |
| Specific date | Regex (month year, YYYY) | -0.2 | "January 2025" |
| Specific count/measure | Regex (number + unit context) | -0.1 | "8 refusals" |
| Definition pattern | Starts with "X is a/an" | +0.3 (toward DERIVABLE) | "DVT is a blood clot" |
| "Standard" keyword | Word match | +0.2 | "Standard adult dose" |
| Textbook structure | Short, definitional, no org terms | +0.2 | General pharmacology |
| Node type CONSTRAINT | Type check | Floor at 0.50 max | Safety nodes protected |
| Node type ANTI_PATTERN | Type check | Floor at 0.60 max | Past incidents protected |
| Incident reference | Pattern ("incident", "past case") | -0.3 | "Supra incident 2023" |
| "Policy" or "protocol" with org | Combined check | -0.2 | "Supra policy" |

---

## VALIDATION MATRIX TEMPLATE

After running your scorer on all 30 nodes:

```
                    ACTUALLY DERIVABLE  ACTUALLY NON-DERIVABLE  ACTUALLY PARTIAL
SCORED DERIVABLE    True Positive (TP)  FALSE POSITIVE (FP)     Borderline
SCORED NON-DERIV    False Negative (FN) True Negative (TN)      Borderline
SCORED PARTIAL      Borderline          Borderline              True Partial (TP)

Precision = TP / (TP + FP)    ← of excluded, how many were ACTUALLY derivable?
Recall = TP / (TP + FN)       ← of ACTUALLY derivable, how many did we catch?

TARGET: Precision ≥ 85%, Recall ≥ 70%
(We'd rather MISS some derivable nodes than EXCLUDE org-specific ones)
```

---

## SUBMISSION CHECKLIST

```
□ 30 nodes loaded with expected_derivability ground truth
□ Scoring algorithm implemented (document your approach in architecture.md)
□ All 30 nodes scored with derivability_score and scoring_reason
□ Clearly derivable nodes (D-01 to D-10) score > 0.7
□ Clearly non-derivable (ND-01 to ND-10) score < 0.3
□ Edge cases (E-01 to E-10) score between 0.3-0.7
□ Type-based floors applied (CONSTRAINT max 0.50, ANTI_PATTERN max 0.60)
□ Threshold configurable via org_config (default 0.7)
□ Token savings computed (total saved, percentage, annual projection)
□ Validation matrix with precision/recall
□ False positives identified and explained
□ PARTIALLY_DERIVABLE nodes show non_derivable_portion
□ Threshold slider shows savings-vs-safety tradeoff
□ Surprise node scores correctly without code changes
□ docs/architecture.md explains algorithm + tradeoffs + calibration plan
□ Clean git, README present
```

---

## FREE TIER SUFFICIENCY

| Resource | Free Tier | Sufficient? |
|---|---|---|
| **Supabase** | 500 MB | YES |
| **Embedding API** | Optional ($0.01 for 30 nodes) | YES if using embedding approach |
| **LLM API** | Not needed at query time | ZERO LLM at runtime |

**Total cost: $0 (heuristic) or $0.01 (embedding approach)**

---

*Setup Guide v1.0 — Derivability Scoring Without LLM*


