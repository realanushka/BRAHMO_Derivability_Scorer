"""
Tests for the TF-IDF (Embedding) Scorer.

Validates that the TF-IDF scorer assigns high similarity scores
to general medical knowledge and low scores to org-specific content.
"""

import pytest

from app.scorer.embedding_scorer import TFIDFScorer


@pytest.fixture
def scorer():
    return TFIDFScorer()


class TestTFIDFScoring:
    """TF-IDF similarity scorer tests."""

    def test_general_medical_definition_high_score(self, scorer):
        """General medical definitions should score high (similar to corpus)."""
        score = scorer.score(
            "Total knee replacement is a surgical procedure where damaged knee "
            "joint surfaces are replaced with artificial components.",
            title="What is TKR",
        )
        assert score > 0.3, f"General medical definition scored {score}, expected > 0.3"

    def test_org_specific_low_score(self, scorer):
        """Org-specific content should score low (dissimilar to corpus)."""
        score = scorer.score(
            "Supra Ortho Department uses Zimmer Biomet as preferred TKR implant vendor. "
            "Alternative: Smith & Nephew for revision cases only.",
            title="Zimmer Biomet Implant Preference",
        )
        # Org-specific content should have lower similarity to general corpus
        assert score < 0.8, f"Org-specific scored {score}, expected < 0.8"

    def test_empty_content(self, scorer):
        """Empty content should return neutral score."""
        score = scorer.score("")
        assert score == 0.5, f"Empty content scored {score}, expected 0.5"

    def test_top_matches_returns_results(self, scorer):
        """Top matches should return corpus entries with similarity."""
        results = scorer.get_top_matches(
            "Paracetamol is an analgesic and antipyretic drug.",
            top_n=3,
        )
        assert len(results) <= 3
        for r in results:
            assert "corpus_text" in r
            assert "similarity" in r
            assert 0.0 <= r["similarity"] <= 1.0
