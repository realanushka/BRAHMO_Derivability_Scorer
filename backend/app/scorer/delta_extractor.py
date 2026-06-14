"""
Delta Extractor — Extracts the non-derivable (org-specific) portion
from PARTIALLY_DERIVABLE node content.

Uses spaCy for sentence segmentation and entity detection.
Keeps sentences that contain organization-specific markers.
"""

from __future__ import annotations

import re
from typing import Optional

import spacy

# Reuse the same spaCy model loaded by heuristic_scorer
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    raise RuntimeError(
        "spaCy model 'en_core_web_sm' not found. "
        "Install it with: python -m spacy download en_core_web_sm"
    )


# Default org names
DEFAULT_ORG_NAMES = {"supra", "supra hospital", "supra ortho", "supra multi-specialty"}

# Markers that indicate org-specific content
ORG_SPECIFIC_PATTERNS = [
    r"\bSupra\b",
    r"\bDr\.\s*[A-Z][a-z]+",
    r"\bPatient\s+[A-Z][a-z]+",
    r"\bMrs?\.\s*[A-Z][a-z]+",
    r"\bFY\s*\d{4}",
    r"₹[\d,.]+",
    r"\bpolicy\b",
    r"\bprotocol\b",
    r"\bincident\b",
    r"\bnear[- ]miss\b",
    r"\breadmission\b",
    r"\bformulary\b",
    r"\bauto-alert",
    r"\bHOD\b",
    r"\bnon-compliance\b",
    r"\breportable\b",
]


class DeltaExtractor:
    """
    Extracts the non-derivable portion from content with mixed
    general + org-specific knowledge.
    """

    def __init__(self, org_names: Optional[set[str]] = None):
        self.org_names = org_names or DEFAULT_ORG_NAMES
        self.nlp = nlp

    def extract(self, content: str, title: str = "") -> Optional[str]:
        """
        Extract the non-derivable (org-specific) portion of content.

        Strategy:
        1. Split content into sentences using spaCy
        2. Score each sentence for org-specificity
        3. Keep sentences with org-specific markers
        4. Return joined result

        Returns:
            The org-specific delta text, or None if extraction fails
        """
        if not content:
            return None

        doc = self.nlp(content)
        sentences = list(doc.sents)

        if len(sentences) <= 1:
            # Single sentence — can't split, return full content
            return content

        org_specific_sentences = []

        for sent in sentences:
            sent_text = sent.text.strip()
            if not sent_text:
                continue

            if self._is_org_specific(sent_text, sent):
                org_specific_sentences.append(sent_text)

        if not org_specific_sentences:
            # Nothing detected as org-specific — return full content
            # (conservative: when in doubt, include everything)
            return content

        if len(org_specific_sentences) == len(sentences):
            # Everything is org-specific — return full content
            return content

        return " ".join(org_specific_sentences)

    def _is_org_specific(self, text: str, span) -> bool:
        """
        Determine if a sentence contains org-specific content.
        """
        text_lower = text.lower()

        # Check org name references
        for org in self.org_names:
            if org in text_lower:
                return True

        # Check org-specific regex patterns
        for pattern in ORG_SPECIFIC_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        # Check spaCy entities
        for ent in span.ents:
            if ent.label_ == "PERSON":
                return True
            if ent.label_ == "DATE":
                # Specific dates with year often indicate org decisions
                if re.search(r"\d{4}", ent.text):
                    return True

        # Check for specific numbers with context (e.g., "8 refusals", "45 beds")
        if re.search(r"\b\d+\s+(?:refusals?|beds?|episodes?|incidents?)\b", text, re.IGNORECASE):
            return True

        # Check for budget/cost figures
        if re.search(r"[₹$€]\s*[\d,.]+", text):
            return True

        return False
