"""
Hybrid Scorer — Combines heuristic and TF-IDF scores with type safety floors.

Fusion formula: final_score = 0.7 × heuristic_score + 0.3 × tfidf_score
Then applies type-based ceiling (floors from org perspective):
  CONSTRAINT  → max 0.50
  ANTI_PATTERN → max 0.60
  DECISION    → no cap (1.0)
  FACT        → no cap (1.0)
"""

from __future__ import annotations

from typing import Optional

from app.models.schemas import ScoringResult, ScoringSignal
from app.scorer.heuristic_scorer import HeuristicScorer
from app.scorer.embedding_scorer import TFIDFScorer
from app.scorer.delta_extractor import DeltaExtractor


# Default type floors from the assessment spec
DEFAULT_TYPE_FLOORS = {
    "CONSTRAINT": 0.50,
    "ANTI_PATTERN": 0.60,
    "DECISION": 1.0,
    "FACT": 1.0,
}

# Fusion weights
HEURISTIC_WEIGHT = 0.70
TFIDF_WEIGHT = 0.30


class HybridScorer:
    """
    Combines heuristic and TF-IDF scores using weighted fusion,
    applies type safety floors, and classifies nodes.
    """

    def __init__(
        self,
        type_floors: Optional[dict[str, float]] = None,
        org_names: Optional[set[str]] = None,
    ):
        self.type_floors = type_floors or DEFAULT_TYPE_FLOORS
        self.heuristic_scorer = HeuristicScorer(org_names=org_names)
        self.tfidf_scorer = TFIDFScorer()
        self.delta_extractor = DeltaExtractor(org_names=org_names)

    def score_node(
        self,
        content: str,
        title: str = "",
        node_type: str = "FACT",
        node_id: str = "",
        threshold: float = 0.7,
        algorithm: str = "hybrid",
    ) -> ScoringResult:
        """
        Score a single node and return a ScoringResult.

        Args:
            content: Node content text
            title: Node title
            node_type: Node type (CONSTRAINT, DECISION, ANTI_PATTERN, FACT)
            node_id: Node identifier
            threshold: Classification threshold
            algorithm: 'heuristic', 'tfidf', or 'hybrid'

        Returns:
            ScoringResult with final score, classification, and explanation
        """
        # --- Step 1: Run individual scorers ---
        heuristic_score, signals = self.heuristic_scorer.score(content, title)
        tfidf_score = self.tfidf_scorer.score(content, title)

        # --- Step 2: Compute fused score based on algorithm ---
        if algorithm == "heuristic":
            raw_score = heuristic_score
        elif algorithm == "tfidf":
            raw_score = tfidf_score
        else:  # hybrid (default)
            raw_score = (HEURISTIC_WEIGHT * heuristic_score) + (TFIDF_WEIGHT * tfidf_score)

        raw_score = max(0.0, min(1.0, raw_score))

        # --- Step 3: Apply type safety floor ---
        type_floor_applied = False
        final_score = raw_score
        max_allowed = self.type_floors.get(node_type, 1.0)

        if final_score > max_allowed:
            final_score = max_allowed
            type_floor_applied = True

        final_score = round(final_score, 4)

        # --- Step 4: Classify ---
        classification = self._classify(final_score, threshold)

        # --- Step 5: Extract delta for PARTIALLY_DERIVABLE ---
        non_derivable_portion = None
        if classification == "PARTIALLY_DERIVABLE":
            non_derivable_portion = self.delta_extractor.extract(content, title)

        # --- Step 6: Build scoring reason ---
        scoring_reason = self._build_reason(
            heuristic_score, tfidf_score, final_score,
            signals, classification, type_floor_applied,
            node_type, algorithm
        )

        return ScoringResult(
            node_id=node_id,
            raw_score=round(raw_score, 4),
            heuristic_score=round(heuristic_score, 4),
            tfidf_score=round(tfidf_score, 4),
            final_score=final_score,
            classification=classification,
            signals=signals,
            scoring_reason=scoring_reason,
            type_floor_applied=type_floor_applied,
            non_derivable_portion=non_derivable_portion,
        )

    def _classify(self, score: float, threshold: float) -> str:
        """Classify a score into DERIVABLE / PARTIALLY_DERIVABLE / NON_DERIVABLE."""
        if score >= threshold:
            return "DERIVABLE"
        elif score >= 0.40:
            return "PARTIALLY_DERIVABLE"
        else:
            return "NON_DERIVABLE"

    def _build_reason(
        self,
        heuristic_score: float,
        tfidf_score: float,
        final_score: float,
        signals: list[ScoringSignal],
        classification: str,
        type_floor_applied: bool,
        node_type: str,
        algorithm: str,
    ) -> str:
        """Build a human-readable scoring reason."""
        parts = []

        # Algorithm info
        if algorithm == "hybrid":
            parts.append(
                f"Hybrid score: {final_score:.2f} "
                f"(H={heuristic_score:.2f} × 0.7 + T={tfidf_score:.2f} × 0.3)"
            )
        elif algorithm == "heuristic":
            parts.append(f"Heuristic score: {final_score:.2f}")
        else:
            parts.append(f"TF-IDF score: {final_score:.2f}")

        # Type floor
        if type_floor_applied:
            max_allowed = self.type_floors.get(node_type, 1.0)
            parts.append(
                f"Type floor applied: {node_type} capped at {max_allowed:.2f}"
            )

        # Top signals
        positive = [s for s in signals if s.weight > 0]
        negative = [s for s in signals if s.weight < 0]

        if positive:
            top_pos = sorted(positive, key=lambda s: s.weight, reverse=True)[:3]
            pos_str = "; ".join(
                f"{s.name} (+{s.weight:.2f})" for s in top_pos
            )
            parts.append(f"Positive: {pos_str}")

        if negative:
            top_neg = sorted(negative, key=lambda s: s.weight)[:3]
            neg_str = "; ".join(
                f"{s.name} ({s.weight:.2f})" for s in top_neg
            )
            parts.append(f"Negative: {neg_str}")

        # Classification
        parts.append(f"→ {classification}")

        return ". ".join(parts)
