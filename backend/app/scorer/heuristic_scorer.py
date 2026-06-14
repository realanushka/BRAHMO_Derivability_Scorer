"""
Heuristic Scorer for derivability classification.

Uses spaCy NER (PERSON, DATE, ORG) and regex patterns to detect
positive signals (toward DERIVABLE) and negative signals (toward NON_DERIVABLE).

Base score: 0.50 (neutral)
Positive signals add weight, negative signals subtract weight.
Final score clamped to [0.0, 1.0].
"""

from __future__ import annotations

import re
from typing import Optional

import spacy

from app.models.schemas import ScoringSignal

# ---------------------------------------------------------------------------
# Load spaCy model (loaded once at module import)
# ---------------------------------------------------------------------------
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # Model not installed — provide a helpful error
    raise RuntimeError(
        "spaCy model 'en_core_web_sm' not found. "
        "Install it with: python -m spacy download en_core_web_sm"
    )

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_SCORE = 0.50

# Organization names to detect (expandable per org)
ORG_NAMES = {"supra", "supra hospital", "supra ortho", "supra multi-specialty"}

# Incident keywords
INCIDENT_KEYWORDS = {
    "incident", "near miss", "near-miss", "readmission", "readmitted",
    "past case", "adverse event", "sentinel event", "safety event",
}

# Decision rationale keywords
DECISION_KEYWORDS = {
    "because", "based on", "reviewed", "updated", "decided",
    "decision by", "approved", "rationale",
}

# Patient reference patterns
PATIENT_PATTERNS = [
    r"\bpatient\s+[A-Z][a-z]+",
    r"\bmrs?\.\s*[A-Z][a-z]+",
    r"\bpatient\b",
]

# Standard / generic keywords
STANDARD_KEYWORDS = {
    "standard", "normal", "common", "typical", "usual", "general",
    "worldwide", "globally", "universal",
}

# Definition patterns
DEFINITION_PATTERNS = [
    r"^[A-Z][\w\s\(\)]+\bis\s+(?:a|an)\b",
    r"\bwhat\s+is\b",
    r"\bis\s+(?:a|an)\s+(?:surgical|medical|chronic|life-threatening|clinical)",
    r"\bis\s+(?:a|an)\s+\w+\s+(?:that|which|used|designed)",
    r"\balso\s+(?:known|called)\s+as\b",
]

# Specific count patterns
COUNT_PATTERNS = [
    r"\b\d+\s+(?:refusals?|beds?|times?|episodes?|patients?|cases?|incidents?)",
    r"\b\d+\s*%",
    r"[₹$€]\s*[\d,.]+",
    r"\b\d+\s*(?:Cr|crore|lakh)\b",
]

# Date patterns (beyond spaCy)
DATE_PATTERNS = [
    r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
    r"\b(?:Q[1-4])\s*\d{4}\b",
    r"\b20[12]\d\b",
    r"\bFY\s*\d{4}\b",
]

# Medical terminology (generic, textbook)
MEDICAL_TERMS = {
    "analgesic", "antipyretic", "anticoagulant", "prostaglandin", "mechanism",
    "inhibits", "opioid", "receptor", "metabolism", "pharmacology",
    "pathophysiology", "etiology", "prognosis", "diagnosis", "symptoms",
    "risk factors", "complications", "treatment", "therapy", "clinical",
    "surgical", "procedure", "chronic", "acute", "infection",
    "inflammation", "assessment", "evaluation", "criteria", "score",
    "classification", "dysfunction", "disorder", "disease", "syndrome",
}


# ---------------------------------------------------------------------------
# Heuristic Scorer
# ---------------------------------------------------------------------------

class HeuristicScorer:
    """
    Rule-based derivability scorer using spaCy NER and regex patterns.
    """

    def __init__(self, org_names: Optional[set[str]] = None):
        self.org_names = org_names or ORG_NAMES
        self.nlp = nlp

    def score(self, content: str, title: str = "") -> tuple[float, list[ScoringSignal]]:
        """
        Score content for derivability using heuristic rules.

        Returns:
            tuple of (score: float, signals: list[ScoringSignal])
        """
        signals: list[ScoringSignal] = []
        combined_text = f"{title} {content}".strip()
        content_lower = content.lower()
        combined_lower = combined_text.lower()

        # Run spaCy NER
        doc = self.nlp(combined_text)

        # --- POSITIVE SIGNALS ---
        signals.extend(self._check_definition_patterns(content, title))
        signals.extend(self._check_textbook_structure(content, combined_lower))
        signals.extend(self._check_standard_keywords(combined_lower))
        signals.extend(self._check_medical_terminology(combined_lower))
        signals.extend(self._check_no_org_references(combined_lower))

        # --- NEGATIVE SIGNALS ---
        signals.extend(self._check_org_names(combined_lower))
        signals.extend(self._check_person_names(doc))
        signals.extend(self._check_dates(doc, combined_text))
        signals.extend(self._check_incident_references(combined_lower))
        signals.extend(self._check_policy_protocol(combined_lower))
        signals.extend(self._check_specific_counts(combined_text))
        signals.extend(self._check_patient_references(combined_text, combined_lower))
        signals.extend(self._check_decision_rationale(combined_lower))

        # Compute final score
        score = BASE_SCORE
        for signal in signals:
            score += signal.weight
        score = max(0.0, min(1.0, score))

        return score, signals

    # ------------------------------------------------------------------
    # Positive Signal Detectors
    # ------------------------------------------------------------------

    def _check_definition_patterns(self, content: str, title: str) -> list[ScoringSignal]:
        """Check for 'X is a...' definition patterns. Weight: +0.30"""
        signals = []
        combined = f"{title} {content}"
        for pattern in DEFINITION_PATTERNS:
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                signals.append(ScoringSignal(
                    name="definition_pattern",
                    weight=0.30,
                    description="Content follows a definition pattern (e.g., 'X is a...')",
                    matched_text=match.group()[:80],
                ))
                break  # Only count once
        return signals

    def _check_textbook_structure(self, content: str, content_lower: str) -> list[ScoringSignal]:
        """Check for textbook-style structure. Weight: +0.20"""
        signals = []
        # Short, definitional, no org terms
        has_no_org = not any(org in content_lower for org in self.org_names)
        word_count = len(content.split())
        has_medical = sum(1 for term in MEDICAL_TERMS if term in content_lower)

        if has_no_org and word_count < 60 and has_medical >= 3:
            signals.append(ScoringSignal(
                name="textbook_structure",
                weight=0.20,
                description="Short, structured content with medical terminology and no org-specific terms",
                matched_text=f"{word_count} words, {has_medical} medical terms",
            ))
        return signals

    def _check_standard_keywords(self, content_lower: str) -> list[ScoringSignal]:
        """Check for 'standard', 'normal', 'common' keywords. Weight: +0.20"""
        signals = []
        found = [kw for kw in STANDARD_KEYWORDS if kw in content_lower]
        if found:
            signals.append(ScoringSignal(
                name="standard_keyword",
                weight=0.20,
                description=f"Contains standard/generic keywords: {', '.join(found[:3])}",
                matched_text=", ".join(found[:3]),
            ))
        return signals

    def _check_medical_terminology(self, content_lower: str) -> list[ScoringSignal]:
        """Check generic medical terminology density. Weight: +0.20"""
        signals = []
        word_count = len(content_lower.split())
        if word_count == 0:
            return signals
        medical_count = sum(1 for term in MEDICAL_TERMS if term in content_lower)
        density = medical_count / word_count

        if density > 0.08 and medical_count >= 3:
            signals.append(ScoringSignal(
                name="generic_terminology_density",
                weight=0.20,
                description=f"High density of generic medical terms ({medical_count} terms, {density:.1%} density)",
                matched_text=f"{medical_count} medical terms in {word_count} words",
            ))
        return signals

    def _check_no_org_references(self, content_lower: str) -> list[ScoringSignal]:
        """Check for absence of organization references. Weight: +0.10"""
        signals = []
        has_org = any(org in content_lower for org in self.org_names)
        if not has_org:
            signals.append(ScoringSignal(
                name="no_org_references",
                weight=0.10,
                description="No organization-specific references detected",
            ))
        return signals

    # ------------------------------------------------------------------
    # Negative Signal Detectors
    # ------------------------------------------------------------------

    def _check_org_names(self, content_lower: str) -> list[ScoringSignal]:
        """Detect organization names. Weight: -0.40"""
        signals = []
        found = [org for org in self.org_names if org in content_lower]
        if found:
            signals.append(ScoringSignal(
                name="org_name_present",
                weight=-0.40,
                description=f"Contains organization name(s): {', '.join(found)}",
                matched_text=", ".join(found),
            ))
        return signals

    def _check_person_names(self, doc: spacy.tokens.Doc) -> list[ScoringSignal]:
        """Detect person names using spaCy PERSON NER. Weight: -0.30"""
        signals = []
        persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON" and not re.search(r"\d", ent.text)]
        # Also check for Dr. pattern
        dr_matches = re.findall(r"\bDr\.?\s+[A-Z][a-z]+", doc.text)
        all_persons = list(set(persons + dr_matches))

        if all_persons:
            signals.append(ScoringSignal(
                name="person_name_present",
                weight=-0.30,
                description=f"Person name(s) detected: {', '.join(all_persons[:5])}",
                matched_text=", ".join(all_persons[:5]),
            ))
        return signals

    def _check_dates(self, doc: spacy.tokens.Doc, text: str) -> list[ScoringSignal]:
        """Detect specific dates using spaCy DATE + regex. Weight: -0.20"""
        signals = []
        # spaCy DATE entities
        dates_spacy = [ent.text for ent in doc.ents if ent.label_ == "DATE"]
        # Regex date patterns
        dates_regex = []
        for pattern in DATE_PATTERNS:
            dates_regex.extend(re.findall(pattern, text))
        all_dates = list(set(dates_spacy + dates_regex))

        if all_dates:
            signals.append(ScoringSignal(
                name="specific_date_present",
                weight=-0.20,
                description=f"Specific date(s) detected: {', '.join(all_dates[:5])}",
                matched_text=", ".join(all_dates[:5]),
            ))
        return signals

    def _check_incident_references(self, content_lower: str) -> list[ScoringSignal]:
        """Detect incident/near-miss references. Weight: -0.30"""
        signals = []
        found = [kw for kw in INCIDENT_KEYWORDS if kw in content_lower]
        if found:
            signals.append(ScoringSignal(
                name="incident_reference",
                weight=-0.30,
                description=f"Incident-related keywords detected: {', '.join(found)}",
                matched_text=", ".join(found),
            ))
        return signals

    def _check_policy_protocol(self, content_lower: str) -> list[ScoringSignal]:
        """Detect 'policy' or 'protocol' with org name. Weight: -0.20"""
        signals = []
        has_policy = "policy" in content_lower or "protocol" in content_lower
        has_org = any(org in content_lower for org in self.org_names)

        if has_policy and has_org:
            signals.append(ScoringSignal(
                name="policy_protocol_with_org",
                weight=-0.20,
                description="Policy/protocol reference combined with organization name",
            ))
        return signals

    def _check_specific_counts(self, text: str) -> list[ScoringSignal]:
        """Detect specific counts (8 refusals, 45 beds). Weight: -0.10"""
        signals = []
        for pattern in COUNT_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                signals.append(ScoringSignal(
                    name="specific_count",
                    weight=-0.10,
                    description=f"Specific count/measure detected: {', '.join(matches[:3])}",
                    matched_text=", ".join(matches[:3]),
                ))
                break  # Only count once
        return signals

    def _check_patient_references(self, text: str, text_lower: str) -> list[ScoringSignal]:
        """Detect patient references. Weight: -0.30"""
        signals = []
        for pattern in PATIENT_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                signals.append(ScoringSignal(
                    name="patient_reference",
                    weight=-0.30,
                    description=f"Patient reference detected: '{match.group()}'",
                    matched_text=match.group(),
                ))
                break  # Only count once
        return signals

    def _check_decision_rationale(self, content_lower: str) -> list[ScoringSignal]:
        """Detect decision rationale keywords. Weight: -0.20"""
        signals = []
        found = [kw for kw in DECISION_KEYWORDS if kw in content_lower]
        if found:
            signals.append(ScoringSignal(
                name="decision_rationale",
                weight=-0.20,
                description=f"Decision rationale keywords: {', '.join(found[:3])}",
                matched_text=", ".join(found[:3]),
            ))
        return signals
