"""
Tests for threshold sensitivity.

Validates that changing the threshold produces expected behavior:
- Higher threshold → more conservative → fewer exclusions
- Lower threshold → more aggressive → more exclusions
"""

import pytest

from app.scorer.hybrid_scorer import HybridScorer


@pytest.fixture
def scorer():
    return HybridScorer()


# A clearly derivable node
DERIVABLE_CONTENT = (
    "Paracetamol (acetaminophen) is an analgesic and antipyretic. "
    "Mechanism: inhibits prostaglandin synthesis in the CNS."
)

# A clearly non-derivable node
NON_DERIVABLE_CONTENT = (
    "Supra Ortho uses Paracetamol 650mg QDS as first-line post-TKR. "
    "Decision by Dr. Vikram, January 2025."
)


class TestThresholdSensitivity:
    """Test that threshold changes produce expected classification shifts."""

    def test_derivable_at_default_threshold(self, scorer):
        """Derivable content should be DERIVABLE at threshold 0.7."""
        result = scorer.score_node(
            content=DERIVABLE_CONTENT,
            title="Paracetamol Mechanism",
            node_type="FACT",
            threshold=0.7,
        )
        assert result.classification == "DERIVABLE"

    def test_derivable_at_high_threshold(self, scorer):
        """At very high threshold (0.95), fewer nodes are DERIVABLE."""
        result = scorer.score_node(
            content=DERIVABLE_CONTENT,
            title="Paracetamol Mechanism",
            node_type="FACT",
            threshold=0.95,
        )
        # At 0.95 threshold, even clearly derivable content
        # might become PARTIALLY_DERIVABLE
        assert result.classification in ("DERIVABLE", "PARTIALLY_DERIVABLE")

    def test_non_derivable_at_all_thresholds(self, scorer):
        """Non-derivable content should never be DERIVABLE."""
        for threshold in [0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
            result = scorer.score_node(
                content=NON_DERIVABLE_CONTENT,
                title="Supra Protocol",
                node_type="DECISION",
                threshold=threshold,
            )
            assert result.classification != "DERIVABLE", (
                f"Non-derivable content wrongly classified as DERIVABLE "
                f"at threshold {threshold}"
            )

    def test_lower_threshold_more_derivable(self, scorer):
        """Lower threshold should classify more nodes as DERIVABLE."""
        result_low = scorer.score_node(
            content=DERIVABLE_CONTENT,
            title="Paracetamol",
            node_type="FACT",
            threshold=0.5,
        )
        result_high = scorer.score_node(
            content=DERIVABLE_CONTENT,
            title="Paracetamol",
            node_type="FACT",
            threshold=0.9,
        )
        # At lower threshold, the same content is more likely DERIVABLE
        derivable_classes = ("DERIVABLE",)
        low_is_derivable = result_low.classification in derivable_classes
        high_is_derivable = result_high.classification in derivable_classes

        # If it's derivable at high threshold, it must be derivable at low threshold
        if high_is_derivable:
            assert low_is_derivable

    def test_threshold_configurable(self, scorer):
        """Threshold should be configurable without code changes."""
        for threshold in [0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95]:
            result = scorer.score_node(
                content=DERIVABLE_CONTENT,
                title="Test",
                node_type="FACT",
                threshold=threshold,
            )
            # Just verify it runs without error at all threshold values
            assert 0.0 <= result.final_score <= 1.0
