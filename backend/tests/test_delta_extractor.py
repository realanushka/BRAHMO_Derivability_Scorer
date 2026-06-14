"""
Tests for the Delta Extractor.

Validates org-specific content extraction from mixed-content nodes.
"""

import pytest

from app.scorer.delta_extractor import DeltaExtractor


@pytest.fixture
def extractor():
    return DeltaExtractor()


class TestDeltaExtraction:
    """Test extraction of non-derivable portions."""

    def test_mixed_content_extracts_org_specific(self, extractor):
        """Content with mix of general + org-specific should extract delta."""
        content = (
            "ALL ortho surgical patients receive DVT prophylaxis. "
            "Enoxaparin 40mg SC daily starting 12 hours post-op. "
            "Supra protocol requires duration: 14 days for TKR."
        )
        delta = extractor.extract(content, "DVT Prophylaxis")
        assert delta is not None
        assert "Supra" in delta or len(delta) < len(content)

    def test_single_sentence_returns_full(self, extractor):
        """Single-sentence content should return full content."""
        content = "Supra uses specific protocols for all patients."
        delta = extractor.extract(content)
        assert delta == content

    def test_empty_content_returns_none(self, extractor):
        """Empty content should return None."""
        delta = extractor.extract("")
        assert delta is None

    def test_fully_org_specific_returns_full(self, extractor):
        """Content that is fully org-specific should return everything."""
        content = (
            "Supra Ortho uses Zimmer Biomet implants. "
            "Dr. Vikram reviewed outcomes in 2024. "
            "Supra policy requires documentation."
        )
        delta = extractor.extract(content)
        assert delta == content
