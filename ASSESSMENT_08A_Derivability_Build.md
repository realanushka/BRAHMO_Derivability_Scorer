# DEVELOPER ASSESSMENT 8 — OPTION A (Build & Demo)
# Score Knowledge Without AI — Save 40-60% of Tokens
## Derivability Scoring Without LLM
### BRAHMO — Full-Stack Developer Assessment

**Time:** 5-8 hours | **Demo:** 20-25 minutes | **Deadline:** 72 hours
**Stack:** Supabase + Python (FastAPI) + React + Tailwind CSS
**Tools:** Use ANY AI tool — no paid subscriptions required (see Setup Guide)
**Deliverables:** Working demo + source code + architecture notes

---

## THE STORY THAT STARTED THIS (Why This Matters)

Dr. Vikram opens an AI session at Supra Hospital. The Rules Engine produces 28 candidate nodes. Among them is node N-D01: "Total knee replacement (TKR) is a surgical procedure where damaged knee joint surfaces are replaced with artificial components." This costs ~120 tokens.

Claude already knows what a TKR is. It learned that from its training data. Those 120 tokens are wasted — they tell the AI something it already knows. But node N-O02: "Supra Ortho uses Paracetamol 650mg QDS as first-line post-TKR pain management" — Claude does NOT know this. It's Supra-specific. Those tokens are essential.

Across 28 candidates, 40-60% contain knowledge the AI can derive from general training: "What is osteoarthritis," "Paracetamol mechanism of action," "Normal vital sign ranges." Excluding these saves 1,200-1,800 tokens per session. At 50 engineers × 10 sessions/day × 250 working days, that's $8,750/year in API cost savings. At scale (500 engineers), $87,500/year.

But here's the constraint: the Rules Engine (L2) uses **ZERO LLM**. Every decision is binary and deterministic. You cannot call Claude to ask "is this derivable?" — that adds latency, costs tokens, and violates the fundamental L2/L3 separation. The derivability score must be computed WITHOUT any LLM call at query time.

**Your job:** Design and implement a derivability scoring mechanism that classifies knowledge nodes as DERIVABLE (exclude), PARTIALLY_DERIVABLE (include delta only), or NON_DERIVABLE (include full) — entirely without runtime LLM calls. Show the token savings. Show the edge cases. Show what happens when the scorer is wrong.

---

## WHAT YOU'RE BUILDING (2-minute read)

A Derivability Scoring system that pre-computes a score (0.0-1.0) for each knowledge node, stored in the database, and used as Check 5 in the Rules Engine pipeline. Nodes scoring above the threshold (default 0.7) are excluded from the candidate set, saving tokens without losing organization-specific knowledge.

**The data flow:**
```
Node created or updated:
  → Derivability Scorer runs (batch or on-creation):
    ├── Approach A: Heuristic rules
    │   ├── Contains org name/brand/person? → LOW derivability (0.1-0.3)
    │   ├── Matches Wikipedia heading pattern? → HIGH derivability (0.8-0.9)
    │   ├── Contains specific numbers/dates? → MEDIUM (0.4-0.6)
    │   ├── Node type = CONSTRAINT? → FLOOR at 0.3 (never exclude constraints)
    │   └── Content length < 50 chars? → HIGH (likely definition)
    │
    ├── Approach B: Pre-computed embeddings comparison
    │   ├── Generate embedding for node content
    │   ├── Compare against "general knowledge" reference corpus
    │   ├── High similarity to general corpus → HIGH derivability
    │   └── Low similarity → LOW derivability (org-specific)
    │
    └── Approach C: Hybrid (recommended)
        ├── Heuristic rules for obvious cases (fast, free)
        ├── Embedding comparison for ambiguous cases
        └── Type-based floor (CONSTRAINT never > 0.5)

  → Score stored: UPDATE nodes SET derivability_score = 0.XX

At query time (Rules Engine Check 5):
  → WHERE derivability_score < 0.7
  → Nodes above threshold EXCLUDED from candidate set
  → PARTIALLY_DERIVABLE: use non_derivable_portion field instead
  → ZERO LLM calls — just a column comparison
```

**What we provide:** 30 seed nodes with known derivability expectations (10 clearly derivable, 10 clearly non-derivable, 10 ambiguous edge cases), scoring rubric, test validation matrix — all in Setup Guide.

**What you figure out (the ENTIRE 25-30%):** The scoring APPROACH itself. This assessment is intentionally open-ended. There is no single correct algorithm. We evaluate your reasoning about tradeoffs, not whether you match a specific implementation.

---

## HOW TO THINK ABOUT THIS (Read Before You Code)

### Mental Model

Think of derivability scoring as a spam filter for AI context. Just as a spam filter prevents junk email from reaching your inbox, the derivability filter prevents "junk tokens" (general knowledge the AI already has) from wasting your context budget. Both must be:

- **Pre-computed** (you don't run the spam filter when you open each email — it already ran)
- **Conservative by default** (false positive = missing an important email/node is WORSE than false negative = seeing a spam/derivable node)
- **Tunable** (threshold adjustable without code changes)
- **Type-aware** (emails from your boss are never spam; CONSTRAINT nodes are never fully derivable)

### The Three Classifications

| Classification | Score Range | Action | Example |
|---|---|---|---|
| **DERIVABLE** | 0.7-1.0 | EXCLUDE entirely | "Paracetamol is an analgesic and antipyretic" |
| **PARTIALLY_DERIVABLE** | 0.4-0.69 | Include NON_DERIVABLE_PORTION only | "Supra uses Paracetamol 650mg QDS post-TKR" (the "650mg QDS post-TKR" part is org-specific) |
| **NON_DERIVABLE** | 0.0-0.39 | Include FULL content | "Dr. Vikram decided Jan 2025 to use Zimmer Biomet based on 3-year outcomes" |

### Decision Priority

| Priority | Component | Why | Time Allocation |
|---|---|---|---|
| 1 | Scoring algorithm design + implementation | The CORE — your creative contribution | 35% |
| 2 | Edge case handling + type-based floors | Safety — a wrong exclusion of a CONSTRAINT is dangerous | 25% |
| 3 | Token savings demonstration | Business value — show the $ impact | 15% |
| 4 | Threshold tuning + validation | Accuracy — show how you'd measure and improve | 15% |
| 5 | Innovation | Additional approaches, calibration ideas | 10% |

**The single most important thing:** A false positive (excluding a NON_DERIVABLE node because the scorer wrongly classified it as DERIVABLE) is FAR more dangerous than a false negative (including a DERIVABLE node because the scorer didn't catch it). False positive = missing critical org-specific knowledge. False negative = wasting some tokens. Design accordingly: when in doubt, include.

---

## WHAT YOUR FINISHED PRODUCT LOOKS LIKE

**Scoring Dashboard:**
```
┌──────────────────────────────────────────────────────────────────┐
│  BRAHMO Derivability Scorer — Token Savings Engine                │
│                                                                  │
│  Threshold: [0.7 ▼] | Algorithm: [Hybrid ▼] | [Rescore All]    │
│                                                                  │
│  TOKEN SAVINGS SUMMARY:                                          │
│  30 nodes total | 10 DERIVABLE | 5 PARTIAL | 15 NON_DERIVABLE   │
│  Tokens saved: 1,450 / 4,200 total = 34.5% savings              │
│  Cost saved per session: $0.022 | Annual (500 sessions/day):     │
│  $2,750/year                                                     │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  SCORING DETAIL (per node):                                      │
│                                                                  │
│  ┌─ N-D01: "What is TKR" ──────────────────────────────────┐    │
│  │ Score: 0.92 | Class: 🔴 DERIVABLE | Action: EXCLUDE      │    │
│  │ Reason: Matches Wikipedia pattern. No org-specific terms. │    │
│  │ Tokens saved: 120                                         │    │
│  │ Validation: ✅ Correct (AI knows TKR definition)          │    │
│  └───────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─ N-O02: "Supra Paracetamol QDS Post-TKR" ────────────────┐   │
│  │ Score: 0.08 | Class: 🟢 NON_DERIVABLE | Action: FULL      │   │
│  │ Reason: Contains org name "Supra", specific dose "QDS",   │   │
│  │         person name "Dr. Vikram", decision date.           │   │
│  │ Tokens: 95 (included in full)                              │   │
│  │ Validation: ✅ Correct (AI doesn't know Supra's protocol)  │   │
│  └───────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─ N-O06: "DVT Prophylaxis Enoxaparin 40mg" ───────────────┐   │
│  │ Score: 0.52 | Class: 🟡 PARTIAL | Action: DELTA ONLY      │   │
│  │ Reason: Standard DVT protocol (derivable) but Supra-      │   │
│  │         specific timing "12 hours post-op" (non-derivable) │   │
│  │ Full: 80 tokens | Delta only: 25 tokens | Saved: 55       │   │
│  │ Validation: ⚠️ Review — is timing standard or org-specific?│   │
│  └───────────────────────────────────────────────────────────┘    │
│                                                                  │
│  TYPE SAFETY FLOORS:                                             │
│  CONSTRAINT: max score 0.50 (never fully excluded)               │
│  ANTI_PATTERN: max score 0.60                                    │
│  DECISION: no floor                                              │
│  FACT: no floor                                                  │
│                                                                  │
│  [Show All 30 Nodes] [Export Validation Matrix] [Tune Threshold] │
└──────────────────────────────────────────────────────────────────┘
```

**Validation Matrix:**
```
┌──────────────────────────────────────────────────────────────────┐
│  VALIDATION MATRIX — Scorer Accuracy                              │
│                                                                  │
│                  │ Actually Derivable │ Actually Non-Derivable   │
│  ────────────────┼───────────────────┼─────────────────────────  │
│  Scored DERIVABLE│ ✅ True Positive   │ 🔴 FALSE POSITIVE        │
│  (excluded)      │    8 nodes         │    1 node (DANGER!)      │
│  ────────────────┼───────────────────┼─────────────────────────  │
│  Scored NON_DERIV│ ⚠️ False Negative  │ ✅ True Negative          │
│  (included)      │    2 nodes (waste) │    14 nodes              │
│  ────────────────┼───────────────────┼─────────────────────────  │
│                                                                  │
│  Precision: 8/9 = 89% | Recall: 8/10 = 80%                      │
│  FALSE POSITIVES: 1 (critical — investigate immediately)         │
│  FALSE NEGATIVES: 2 (acceptable — just wasted tokens)            │
│                                                                  │
│  🔴 FALSE POSITIVE: N-O06 "DVT Prophylaxis" scored 0.72          │
│     but contains Supra-specific "12 hours post-op" timing.       │
│     Action: Lower threshold to 0.75? Or add org-term detection?  │
└──────────────────────────────────────────────────────────────────┘
```

---

## DEMO SCENARIOS (Run all 4)

### Scenario 1: "The Obvious Cases" (Clearly derivable vs clearly not)
**Action:** Show 5 clearly derivable nodes (definitions, general knowledge) and 5 clearly non-derivable nodes (org decisions, patient data).
**What to show:** The scorer correctly classifies all 10. Derivable: "What is osteoarthritis" (0.93), "Normal vital signs" (0.98). Non-derivable: "Supra uses Zimmer implants" (0.05), "Dr. Vikram decided Jan 2025" (0.03). Show the REASON for each score.

### Scenario 2: "The Edge Cases" (Where it gets hard)
**Action:** Show 5 ambiguous nodes where derivability is debatable.
**What to show:** "Standard dose of Paracetamol is 650mg" — derivable? Yes, Claude knows this. But "Paracetamol 650mg QDS" — the QDS (four times daily) frequency is Supra-specific. Where's the boundary? Show how your scorer handles these. Show where it gets it wrong. Acknowledge the limitation.

### Scenario 3: "Type Safety Floors" (CONSTRAINTs protected)
**Action:** Show a CONSTRAINT node with general-sounding content: "Hand hygiene 5-moment compliance" — the WHO 5 moments are general knowledge (derivable). But at Supra, the target is 95% and non-compliance is reportable (org-specific).
**What to show:** Even though content sounds general, the CONSTRAINT type floor caps the score at 0.50. The node is NEVER excluded. Show: if you remove the floor, the scorer might exclude a safety-critical constraint. The floor is a safety net.

### Scenario 4: "Token Savings + Cost Impact" (The business case)
**Action:** Show the aggregate token savings.
**What to show:** 30 nodes. 10 excluded (DERIVABLE). 5 delta-only (PARTIAL). 15 full (NON_DERIVABLE). Total savings: 1,450 tokens / 4,200 = 34.5%. Annual savings at scale. Show: the threshold slider — move from 0.7 to 0.5 (more aggressive) → savings increase but false positive risk increases. Move to 0.9 (more conservative) → fewer savings but safer.

---

## SURPRISE TEST (CRITICAL — READ THIS)

After your 4 demos, we give you a **NEW node** and ask you to predict the score:

**Example:** "A nurse documents: 'Patient Ramaiah's son keeps requesting Ibuprofen for knee pain. We've refused 8 times due to cardiac stent. Family needs continued education.'"

**What we're testing:**
- Your scorer should classify this as NON_DERIVABLE (0.05-0.15)
- Contains patient name (Ramaiah), specific count (8 times), org context (cardiac stent refusal history)
- Zero of this is in AI training data
- If your scorer returns > 0.5 → your heuristics are wrong

**The Architecture Question:**
"After 6 months, you have 1,042 nodes. 200 were manually classified by doctors during creation. 842 were scored by your algorithm. How do you measure accuracy?"

**Right answer:** "Use the 200 manually classified nodes as ground truth. Compare my algorithm's scores against manual labels. Compute precision (of the ones I excluded, how many were actually derivable?) and recall (of the actually derivable ones, how many did I catch?). False positive rate is the critical metric — if I'm excluding org-specific knowledge, that's dangerous. I'd run this comparison monthly and tune the threshold."

---

## WHAT 10/10 LOOKS LIKE

*"The hybrid approach was clever — heuristic rules caught the obvious cases (org names, specific dates, patient references → non-derivable; Wikipedia-pattern definitions → derivable) and embedding comparison handled the ambiguous middle. The type-based floor was the insight that made me trust the system — even if the scorer thinks a CONSTRAINT sounds 'general,' it caps at 0.50 and stays in the context. The validation matrix was honest — 89% precision, 80% recall, one false positive identified and explained. The threshold slider showed the tradeoff: aggressive saves more tokens but risks excluding org-specific knowledge. And when I gave them a surprise node about patient Ramaiah's Ibuprofen requests, the scorer returned 0.08 immediately — no hesitation. This developer understands that derivability is about protecting org-specific knowledge, not just saving tokens."*

---

## OPEN-ENDED THINKING GUIDE (Your ENTIRE 25-30%)

### Problem 1: "Heuristic rules — what signals matter?"
Design 5-10 heuristic rules for derivability scoring. Consider: org name detection, person name detection, specific date/number patterns, content length, node type, Wikipedia heading matching, medical terminology density (high generic term count → more derivable), presence of decision rationale ("because" + org context). Which rules contribute most? How do you weight them?

### Problem 2: "Embedding comparison — what's the reference corpus?"
If you compare node embeddings against a "general knowledge" corpus, what IS that corpus? Wikipedia medical articles? LLM training data summaries? A curated set of "things Claude knows"? How do you build and maintain this reference? What's the embedding cost for 1,000 nodes?

### Problem 3: "PARTIALLY_DERIVABLE — extracting the delta"
"Supra uses Paracetamol 650mg QDS as first-line post-TKR pain management." The general part: "Paracetamol is used for pain." The org-specific delta: "650mg QDS, first-line, post-TKR, Supra's decision." How do you automatically extract the non-derivable portion? LLM at CREATION time (acceptable — this isn't query-time)? Heuristic sentence splitting? Manual by the author?

### Problem 4: "False positive safeguards"
A false positive (excluding org-specific knowledge) is dangerous. What safeguards do you build?
- Type-based floors (CONSTRAINT max 0.5)
- Manual override (doctor marks node as "never exclude")
- Periodic validation against manually classified ground truth
- Logging every exclusion for audit
- "Derivability review" queue for nodes near the threshold

### Problem 5: "Scoring at creation vs batch"
When do you compute scores? On node creation (immediate but adds latency to create flow)? Batch job (delayed but no user-facing latency)? Periodic refresh (catches content changes)? What about nodes created by the Capture Agent at 0.85+ confidence — do they get scored immediately?

---

## EVALUATION CRITERIA

| Criteria | Weight | 10/10 looks like |
|----------|:------:|-----------------|
| **Scoring approach design** | 35% | Clear algorithm with explained tradeoffs. Heuristic, embedding, or hybrid with rationale for choice. Handles obvious cases correctly. Acknowledges limitations. |
| **Edge case handling** | 25% | Type-based floors protect CONSTRAINTs. Ambiguous cases explicitly addressed. False positive acknowledged as worse than false negative. Threshold tunable. |
| **Token savings demonstration** | 15% | Aggregate savings computed and displayed. Cost impact at scale calculated. Threshold slider shows savings-vs-safety tradeoff. |
| **Validation approach** | 15% | Validation matrix with precision/recall. False positives identified. Ground truth comparison plan. Monthly calibration strategy. |
| **Innovation** | 10% | Novel signals (decision rationale detection, entity recognition, embedding comparison). PARTIALLY_DERIVABLE delta extraction. Calibration pipeline design. |

---

## COMMON PITFALLS

- ❌ Using an LLM at QUERY TIME to check derivability → violates fundamental rule, adds latency + cost
- ❌ Defaulting uncertain cases to DERIVABLE → false positive, excludes org-specific knowledge
- ❌ No type-based floor → CONSTRAINT "hand hygiene" excluded because content sounds general
- ❌ Same threshold for all orgs → different orgs have different knowledge profiles
- ❌ No validation mechanism → can't measure accuracy, can't improve over time
- ❌ Character count as sole heuristic → "DVT" is 3 chars but critical; definitions can be long
- ❌ Not logging exclusions → can't audit what was filtered out
- ❌ Binary classification only (derivable/not) → misses PARTIALLY_DERIVABLE middle ground
- ❌ Scoring only at creation, never refreshing → AI training data changes over time
- ❌ Hardcoded threshold → must be configurable per org via org_config

---

## PRE-DEMO CHECKLIST

```
□ 30 seed nodes loaded with expected derivability (10 high, 10 low, 10 ambiguous)
□ Scoring algorithm implemented (heuristic, embedding, or hybrid)
□ Scores computed and stored for all 30 nodes
□ Clearly derivable nodes score > 0.7 (definitions, general knowledge)
□ Clearly non-derivable nodes score < 0.3 (org decisions, patient data)
□ Type-based floors enforced (CONSTRAINT max 0.50)
□ Threshold configurable via UI slider
□ Token savings computed and displayed
□ Validation matrix shows precision/recall
□ False positives identified and explained
□ PARTIALLY_DERIVABLE nodes show delta-only content
□ Scoring works on surprise nodes without code changes
□ docs/architecture.md explains algorithm design + tradeoffs
□ Clean git, README present
```

---

## DAY-OF-DEMO

- **Format:** Video call. Screen share.
- **Duration:** 20-25 minutes.
- **The money moment:** The threshold slider showing token savings change from 20% (conservative, 0.9 threshold) to 45% (aggressive, 0.5 threshold) — and the evaluator understanding the tradeoff between saving tokens and risking false positives. Then the validation matrix showing one false positive and explaining WHY it happened and HOW to fix it.
- **Surprise test:** New node to score live. Predict before running.
- **Questions:** "What if your heuristic is wrong and excludes a CONSTRAINT?" "How do you measure accuracy over time?" "What's the cost of a false positive vs false negative?" "Why 0.7 and not 0.6 or 0.8?"

---

## DEMO STRUCTURE (20-25 minutes)

1. **[3 min]** Architecture: Scoring approaches (heuristic/embedding/hybrid). Pre-computed, not query-time. Three classifications. Type-based floors. Patent Claim 2.
2. **[5 min]** Scenario 1: Obvious cases. 5 derivable + 5 non-derivable. Scoring reasons visible.
3. **[5 min]** Scenario 2: Edge cases. Ambiguous nodes. Where the scorer struggles. Honest limitations.
4. **[3 min]** Scenario 3: Type safety floors. CONSTRAINT protection. What happens without floors.
5. **[3 min]** Scenario 4: Token savings + cost impact. Threshold slider. Business case.
6. **[2 min]** Your algorithm design — explain your approach and why.
7. **[4 min]** Surprise node + accuracy measurement question + our questions

---

*Version: 1.0 | BRAHMO Core — Knowledge Infrastructure*
*Seed data, scoring rubric, and setup instructions are in the separate Setup Guide document.*
