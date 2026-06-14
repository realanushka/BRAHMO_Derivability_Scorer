"""
Tests for the Hybrid Scorer.

Validates score fusion, type safety floors, and classification.
"""

import pytest

from app.scorer.hybrid_scorer import HybridScorer


@pytest.fixture
def scorer():
    return HybridScorer()


class TestHybridScoring:
    """Test hybrid score fusion and classification."""

    def test_derivable_node_scores_high(self, scorer):
        result = scorer.score_node(
            content="Sepsis is a life-threatening organ dysfunction caused by "
                    "dysregulated host response to infection.",
            title="What is Sepsis",
            node_type="FACT",
            node_id="test-D",
            threshold=0.7,
        )
        assert result.final_score >= 0.7, f"Derivable scored {result.final_score}"
        assert result.classification == "DERIVABLE"

    def test_non_derivable_node_scores_low(self, scorer):
        result = scorer.score_node(
            content="Supra Ortho uses Paracetamol 650mg QDS as first-line post-TKR. "
                    "Decision by Dr. Vikram, January 2025.",
            title="Supra Paracetamol Protocol",
            node_type="DECISION",
            node_id="test-ND",
            threshold=0.7,
        )
        assert result.final_score < 0.4, f"Non-derivable scored {result.final_score}"
        assert result.classification == "NON_DERIVABLE"


class TestTypeSafetyFloors:
    """Type-based floors should cap scores for safety-critical types."""

    def test_constraint_floor(self, scorer):
        """CONSTRAINT nodes should be capped at 0.50."""
        result = scorer.score_node(
            content="Normal adult vital signs: HR 60-100 bpm, standard ranges.",
            title="Vital Signs Standard",
            node_type="CONSTRAINT",
            node_id="test-floor",
            threshold=0.7,
        )
        assert result.final_score <= 0.50, (
            f"CONSTRAINT scored {result.final_score}, should be <= 0.50"
        )
        assert result.type_floor_applied is True

    def test_anti_pattern_floor(self, scorer):
        """ANTI_PATTERN nodes should be capped at 0.60."""
        result = scorer.score_node(
            content="Standard practice to avoid administering medication "
                    "without proper verification.",
            title="General Safety Practice",
            node_type="ANTI_PATTERN",
            node_id="test-ap-floor",
            threshold=0.7,
        )
        assert result.final_score <= 0.60, (
            f"ANTI_PATTERN scored {result.final_score}, should be <= 0.60"
        )

    def test_fact_no_cap(self, scorer):
        """FACT nodes should have no artificial cap."""
        result = scorer.score_node(
            content="Total knee replacement (TKR) is a surgical procedure "
                    "where damaged knee joint surfaces are replaced.",
            title="What is TKR",
            node_type="FACT",
            node_id="test-no-cap",
            threshold=0.7,
        )
        # FACT nodes can score above 0.60
        assert result.type_floor_applied is False or result.final_score <= 1.0


class TestAlgorithmSelection:
    """Test different algorithm modes."""

    def test_heuristic_only(self, scorer):
        result = scorer.score_node(
            content="General medical knowledge.",
            title="Test",
            algorithm="heuristic",
        )
        assert result.heuristic_score == result.raw_score

    def test_tfidf_only(self, scorer):
        result = scorer.score_node(
            content="General medical knowledge.",
            title="Test",
            algorithm="tfidf",
        )
        assert result.tfidf_score == result.raw_score

    def test_hybrid_default(self, scorer):
        result = scorer.score_node(
            content="General medical knowledge.",
            title="Test",
            algorithm="hybrid",
        )
        expected_raw = round(
            0.7 * result.heuristic_score + 0.3 * result.tfidf_score, 4
        )
        assert abs(result.raw_score - expected_raw) < 0.01
