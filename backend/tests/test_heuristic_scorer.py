"""
Tests for the Heuristic Scorer.

Validates that the scorer correctly identifies positive signals
(toward DERIVABLE) and negative signals (toward NON_DERIVABLE).
"""

import pytest

from app.scorer.heuristic_scorer import HeuristicScorer


@pytest.fixture
def scorer():
    return HeuristicScorer()


class TestDerivableNodes:
    """Clearly derivable content should score > 0.7."""

    def test_tkr_definition(self, scorer):
        score, signals = scorer.score(
            "Total knee replacement (TKR) is a surgical procedure where "
            "damaged knee joint surfaces are replaced with artificial components. "
            "Also called total knee arthroplasty (TKA).",
            title="What is Total Knee Replacement",
        )
        assert score >= 0.7, f"TKR definition scored {score}, expected >= 0.7"

    def test_paracetamol_mechanism(self, scorer):
        score, signals = scorer.score(
            "Paracetamol (acetaminophen) is an analgesic and antipyretic. "
            "Mechanism: inhibits prostaglandin synthesis in the CNS. "
            "Standard adult dose: 500-1000mg every 4-6 hours, maximum 4g/day.",
            title="Paracetamol Mechanism of Action",
        )
        assert score >= 0.7, f"Paracetamol scored {score}, expected >= 0.7"

    def test_vital_signs(self, scorer):
        score, signals = scorer.score(
            "Normal adult vital signs: HR 60-100 bpm, BP 120/80 mmHg (normal), "
            "RR 12-20/min, SpO2 >95%, Temperature 36.1-37.2°C.",
            title="Normal Adult Vital Sign Ranges",
        )
        assert score >= 0.7, f"Vital signs scored {score}, expected >= 0.7"


class TestNonDerivableNodes:
    """Clearly non-derivable content should score < 0.3."""

    def test_supra_paracetamol_protocol(self, scorer):
        score, signals = scorer.score(
            "Supra Ortho uses Paracetamol 650mg QDS as first-line post-TKR pain "
            "management. Escalation: Tramadol 50mg if VAS > 6. AVOID NSAIDs. "
            "Decision by Dr. Vikram, January 2025.",
            title="Supra Paracetamol QDS Post-TKR",
        )
        assert score < 0.3, f"Supra protocol scored {score}, expected < 0.3"

    def test_patient_nsaid_ban(self, scorer):
        score, signals = scorer.score(
            "ABSOLUTE CONTRAINDICATION: No ibuprofen, no aspirin, no diclofenac "
            "for patient Rajan. Cardiac stent (2022) + dual antiplatelet. "
            "Previous 8 NSAID refusals documented. Paracetamol ONLY.",
            title="Patient Rajan NSAID Ban",
        )
        assert score < 0.3, f"Patient ban scored {score}, expected < 0.3"

    def test_budget_decision(self, scorer):
        score, signals = scorer.score(
            "FY 2026 Ortho budget: ₹4.2 Cr. Implants 45%, Staffing 30%, "
            "Equipment 15%, Training 10%. New arthroscopy equipment approved Q3.",
            title="Ortho Budget 2026",
        )
        assert score < 0.4, f"Budget scored {score}, expected < 0.4"


class TestSignalDetection:
    """Test individual signal detectors."""

    def test_detects_org_names(self, scorer):
        _, signals = scorer.score("Supra Hospital uses this protocol.")
        org_signals = [s for s in signals if s.name == "org_name_present"]
        assert len(org_signals) > 0, "Should detect org name"

    def test_detects_person_names(self, scorer):
        _, signals = scorer.score("Dr. Vikram decided on this approach.")
        person_signals = [s for s in signals if s.name == "person_name_present"]
        assert len(person_signals) > 0, "Should detect person name"

    def test_detects_definition_pattern(self, scorer):
        _, signals = scorer.score("Sepsis is a life-threatening organ dysfunction.")
        def_signals = [s for s in signals if s.name == "definition_pattern"]
        assert len(def_signals) > 0, "Should detect definition pattern"

    def test_detects_incident_reference(self, scorer):
        _, signals = scorer.score(
            "Past incident: patient discharged early, emergency readmission."
        )
        incident_signals = [s for s in signals if s.name == "incident_reference"]
        assert len(incident_signals) > 0, "Should detect incident reference"
