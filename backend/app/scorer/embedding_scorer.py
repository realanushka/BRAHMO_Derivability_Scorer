"""
TF-IDF Similarity Scorer (Embedding Scorer) for derivability classification.

Uses scikit-learn's TfidfVectorizer and cosine_similarity to compare
node content against a curated general medical knowledge corpus.

High similarity → content is general knowledge → more derivable.
Low similarity → content is organization-specific → less derivable.
"""

from __future__ import annotations

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.scorer.reference_corpus import REFERENCE_CORPUS


class TFIDFScorer:
    """
    Computes derivability score based on TF-IDF cosine similarity
    between node content and a general medical knowledge corpus.
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=5000,
            ngram_range=(1, 2),   # unigrams + bigrams for better matching
            min_df=1,
            max_df=0.95,
            sublinear_tf=True,    # apply sublinear TF scaling (1 + log(tf))
        )
        self.corpus = REFERENCE_CORPUS
        self.corpus_vectors = None
        self._fit_corpus()

    def _fit_corpus(self) -> None:
        """Fit the vectorizer on the reference corpus."""
        self.corpus_vectors = self.vectorizer.fit_transform(self.corpus)

    def score(self, content: str, title: str = "") -> float:
        """
        Compute TF-IDF similarity score for the given content.

        Args:
            content: The node content text
            title: Optional node title (prepended to content)

        Returns:
            float: Similarity score between 0.0 and 1.0
                   High = more similar to general knowledge = more derivable
                   Low = less similar = more org-specific
        """
        if not content:
            return 0.5  # neutral for empty content

        # Combine title and content for richer signal
        combined = f"{title} {content}".strip()

        try:
            # Transform the node content using the fitted vectorizer
            node_vector = self.vectorizer.transform([combined])

            # Compute cosine similarity against all corpus entries
            similarities = cosine_similarity(node_vector, self.corpus_vectors)

            # Use the maximum similarity (best match in corpus)
            max_similarity = float(np.max(similarities))

            # Also compute mean of top-3 similarities for stability
            top_k = min(3, similarities.shape[1])
            top_similarities = np.sort(similarities[0])[-top_k:]
            mean_top_k = float(np.mean(top_similarities))

            # Blend max and top-k mean (70/30) for robustness
            blended_score = 0.7 * max_similarity + 0.3 * mean_top_k

            # Scale to make scores more discriminative
            # Raw cosine similarities tend to cluster in 0.05-0.40 range
            # We scale to fill the 0.0-1.0 range better
            scaled_score = min(1.0, blended_score * 2.5)

            return round(max(0.0, min(1.0, scaled_score)), 4)

        except Exception:
            # Fallback to neutral if vectorization fails
            return 0.5

    def get_top_matches(self, content: str, title: str = "", top_n: int = 3) -> list[dict]:
        """
        Get the top matching corpus entries for explanation purposes.

        Returns:
            list of dicts with 'corpus_text' (truncated) and 'similarity'
        """
        combined = f"{title} {content}".strip()
        try:
            node_vector = self.vectorizer.transform([combined])
            similarities = cosine_similarity(node_vector, self.corpus_vectors)[0]

            # Get top N indices
            top_indices = np.argsort(similarities)[-top_n:][::-1]

            results = []
            for idx in top_indices:
                results.append({
                    "corpus_text": self.corpus[idx][:120] + "...",
                    "similarity": round(float(similarities[idx]), 4),
                })
            return results
        except Exception:
            return []
