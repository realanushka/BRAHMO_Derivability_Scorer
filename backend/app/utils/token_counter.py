"""
Token Counter Utility.

Estimates token count for text content using a simple word-based heuristic.
For production, you could use tiktoken for exact OpenAI token counts.
This approximation (words × 1.3) is sufficient for the assessment.
"""

from __future__ import annotations

import re


def count_tokens(text: str) -> int:
    """
    Estimate token count for a given text.

    Uses the approximation: tokens ≈ words × 1.3
    This is a reasonable estimate for English text with GPT-4 tokenization.

    Args:
        text: Input text to count tokens for

    Returns:
        Estimated token count
    """
    if not text:
        return 0

    # Split on whitespace and count words
    words = text.split()
    word_count = len(words)

    # Approximate token count (GPT-4 uses ~1.3 tokens per English word)
    token_count = int(word_count * 1.3)

    return max(1, token_count)  # at least 1 token for non-empty text


def compute_token_savings(
    tokens_full: int,
    tokens_delta: int | None,
    classification: str,
) -> int:
    """
    Compute tokens saved for a node based on its classification.

    Args:
        tokens_full: Total tokens in full content
        tokens_delta: Tokens in delta-only content (for PARTIAL nodes)
        classification: DERIVABLE | PARTIALLY_DERIVABLE | NON_DERIVABLE

    Returns:
        Number of tokens saved
    """
    if classification == "DERIVABLE":
        return tokens_full or 0
    elif classification == "PARTIALLY_DERIVABLE":
        full = tokens_full or 0
        delta = tokens_delta or 0
        return max(0, full - delta)
    else:
        return 0


def compute_cost_savings(
    saved_tokens: int,
    cost_per_1k_tokens: float = 0.015,
    sessions_per_day: int = 10,
) -> dict:
    """
    Compute cost savings projections at various scales.

    Args:
        saved_tokens: Tokens saved per session
        cost_per_1k_tokens: Cost per 1K tokens (default: GPT-4 pricing $0.015/1K)
        sessions_per_day: Sessions per engineer per day

    Returns:
        Dict with savings at different scales
    """
    cost_per_token = cost_per_1k_tokens / 1000
    session_savings = saved_tokens * cost_per_token

    return {
        "session_savings_dollars": round(session_savings, 4),
        "daily_savings_50_engineers": round(session_savings * sessions_per_day * 50, 2),
        "annual_savings_50_engineers": round(session_savings * sessions_per_day * 50 * 250, 2),
        "daily_savings_500_engineers": round(session_savings * sessions_per_day * 500, 2),
        "annual_savings_500_engineers": round(session_savings * sessions_per_day * 500 * 250, 2),
    }
