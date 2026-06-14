"""
Tests for Surprise Nodes — the critical assessment test.

These test ad-hoc nodes that the scorer has never seen before.
The scorer should classify them correctly without code changes.
"""

import pytest

from app.scorer.hybrid_scorer import HybridScorer


@pytest.fixture
def scorer():
    return HybridScorer()


class TestSurpriseNodes:
    """
    Surprise node tests — new content the scorer has never seen.
    These simulate the live demo surprise test.
    """

    def test_patient_ramaiah_ibuprofen(self, scorer):
        """
        Patient Ramaiah's Ibuprofen request history — should be NON_DERIVABLE.
        Contains: patient name, specific count (8 times), org context.
        Expected score: 0.05-0.15
        """
        result = scorer.score_node(
            content=(
                "A nurse documents: 'Patient Ramaiah's son keeps requesting "
                "Ibuprofen for knee pain. We've refused 8 times due to cardiac "
                "stent. Family needs continued education.'"
            ),
            title="Patient Ramaiah Ibuprofen History",
            node_type="FACT",
            node_id="surprise-01",
            threshold=0.7,
        )
        assert result.final_score < 0.3, (
            f"Surprise node scored {result.final_score}, expected < 0.3. "
            f"Reason: {result.scoring_reason}"
        )
        assert result.classification == "NON_DERIVABLE"

    def test_general_aspirin_definition(self, scorer):
        """
        General aspirin definition — should be DERIVABLE.
        Pure medical textbook content.
        """
        result = scorer.score_node(
            content=(
                "Aspirin (acetylsalicylic acid) is a nonsteroidal anti-inflammatory "
                "drug used to treat pain, fever, and inflammation. It also inhibits "
                "platelet aggregation, making it useful for cardiovascular prevention."
            ),
            title="What is Aspirin",
            node_type="FACT",
            node_id="surprise-02",
            threshold=0.7,
        )
        assert result.final_score >= 0.7, (
            f"General definition scored {result.final_score}, expected >= 0.7"
        )
        assert result.classification == "DERIVABLE"

    def test_org_specific_nurse_rotation(self, scorer):
        """
        Org-specific nurse rotation schedule — should be NON_DERIVABLE.
        """
        result = scorer.score_node(
            content=(
                "Supra ICU nurse rotation: 3 shifts × 8 hours. Day shift 7am-3pm, "
                "Evening 3pm-11pm, Night 11pm-7am. Senior nurse Priya leads day shift. "
                "Updated March 2026 by nursing HOD."
            ),
            title="Supra ICU Nurse Rotation",
            node_type="DECISION",
            node_id="surprise-03",
            threshold=0.7,
        )
        assert result.final_score < 0.3, (
            f"Org-specific content scored {result.final_score}, expected < 0.3"
        )

    def test_constraint_with_general_content(self, scorer):
        """
        A CONSTRAINT that sounds general but has org context.
        Type floor should cap it at 0.50.
        """
        result = scorer.score_node(
            content=(
                "All patients must be assessed for pressure ulcer risk "
                "using the Braden Scale within 4 hours of admission."
            ),
            title="Pressure Ulcer Assessment",
            node_type="CONSTRAINT",
            node_id="surprise-04",
            threshold=0.7,
        )
        assert result.final_score <= 0.50, (
            f"CONSTRAINT scored {result.final_score}, should be capped at 0.50"
        )
