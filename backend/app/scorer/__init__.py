"""
Scorer Package — Derivability scoring engines.

Contains:
  - HeuristicScorer:  Rule-based scoring using spaCy NER and regex patterns.
  - TFIDFScorer:      TF-IDF cosine similarity against a medical reference corpus.
  - HybridScorer:     Weighted fusion of heuristic + TF-IDF with type safety floors.
  - DeltaExtractor:   Extracts non-derivable (org-specific) portions from content.
  - REFERENCE_CORPUS: Curated general medical knowledge corpus for TF-IDF comparison.
"""

from app.scorer.delta_extractor import DeltaExtractor
from app.scorer.embedding_scorer import TFIDFScorer
from app.scorer.heuristic_scorer import HeuristicScorer
from app.scorer.hybrid_scorer import HybridScorer
from app.scorer.reference_corpus import REFERENCE_CORPUS

__all__ = [
    "DeltaExtractor",
    "HeuristicScorer",
    "HybridScorer",
    "REFERENCE_CORPUS",
    "TFIDFScorer",
]
