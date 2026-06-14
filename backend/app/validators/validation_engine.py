"""
Validation Engine — Computes confusion matrix, precision, recall, F1
by comparing scored results against expected_derivability ground truth.
"""

from __future__ import annotations

from app.models.schemas import (
    ConfusionMatrix,
    KnowledgeNode,
    ThresholdDataPoint,
    ValidationMatrixResponse,
)


class ValidationEngine:
    """
    Compares derivability_class (scored) against expected_derivability (ground truth)
    to produce a validation matrix with precision, recall, and F1 metrics.
    """

    def compute_matrix(
        self,
        nodes: list[KnowledgeNode],
        threshold: float = 0.7,
    ) -> ValidationMatrixResponse:
        """
        Compute the validation matrix for all scored nodes.

        Classification logic:
        - "Scored DERIVABLE" = node with derivability_score >= threshold
        - "Actually Derivable" = expected_derivability == "DERIVABLE"

        For the binary confusion matrix:
        - TP = scored DERIVABLE AND expected DERIVABLE
        - FP = scored DERIVABLE AND expected NOT DERIVABLE (DANGER!)
        - TN = scored NOT DERIVABLE AND expected NOT DERIVABLE
        - FN = scored NOT DERIVABLE AND expected DERIVABLE (acceptable waste)

        PARTIALLY_DERIVABLE expected nodes are treated as borderline:
        - If scored DERIVABLE → counted as FP (conservative)
        - If scored NON_DERIVABLE → counted as borderline (not counted in FP/FN)
        """
        tp = 0
        fp = 0
        tn = 0
        fn = 0
        false_positive_nodes: list[str] = []
        false_negative_nodes: list[str] = []
        partial_matches: list[str] = []
        total_evaluated = 0

        for node in nodes:
            if not node.expected_derivability or node.derivability_class == "UNKNOWN":
                continue

            total_evaluated += 1
            score = node.derivability_score
            scored_derivable = score >= threshold
            expected = node.expected_derivability

            if expected == "DERIVABLE":
                if scored_derivable:
                    tp += 1  # Correctly identified as derivable
                else:
                    fn += 1  # Missed a derivable node (acceptable — wasted tokens)
                    false_negative_nodes.append(node.id)

            elif expected == "NON_DERIVABLE":
                if scored_derivable:
                    fp += 1  # DANGEROUS! Excluded org-specific knowledge
                    false_positive_nodes.append(node.id)
                else:
                    tn += 1  # Correctly kept non-derivable

            elif expected == "PARTIALLY_DERIVABLE":
                if scored_derivable:
                    # Scoring a partial as fully derivable is somewhat dangerous
                    fp += 1
                    false_positive_nodes.append(node.id)
                elif node.derivability_class == "PARTIALLY_DERIVABLE":
                    # Correctly identified as partial
                    partial_matches.append(node.id)
                    tn += 1  # Count as correct (not excluded)
                else:
                    # Scored as NON_DERIVABLE — conservative but fine
                    tn += 1
                    partial_matches.append(node.id)

        # Compute metrics
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1_score = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )
        false_positive_rate = fp / (fp + tn) if (fp + tn) > 0 else 0.0

        return ValidationMatrixResponse(
            confusion_matrix=ConfusionMatrix(
                true_positives=tp,
                false_positives=fp,
                true_negatives=tn,
                false_negatives=fn,
            ),
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1_score, 4),
            false_positive_rate=round(false_positive_rate, 4),
            false_positive_nodes=false_positive_nodes,
            false_negative_nodes=false_negative_nodes,
            partial_matches=partial_matches,
            total_evaluated=total_evaluated,
        )

    def compute_threshold_analysis(
        self,
        nodes: list[KnowledgeNode],
        thresholds: list[float] | None = None,
    ) -> list[ThresholdDataPoint]:
        """
        Compute metrics at multiple threshold levels for the threshold chart.
        """
        if thresholds is None:
            thresholds = [
                round(t * 0.05 + 0.40, 2)
                for t in range(12)  # 0.40, 0.45, ..., 0.95
            ]

        data_points = []

        for threshold in thresholds:
            # Classify nodes at this threshold
            derivable_count = 0
            partial_count = 0
            non_derivable_count = 0
            total_tokens = 0
            saved_tokens = 0

            for node in nodes:
                score = node.derivability_score
                tokens_full = node.tokens_full or 0
                tokens_delta = node.tokens_delta or 0
                total_tokens += tokens_full

                if score >= threshold:
                    derivable_count += 1
                    saved_tokens += tokens_full
                elif score >= 0.40:
                    partial_count += 1
                    saved_tokens += max(0, tokens_full - tokens_delta)
                else:
                    non_derivable_count += 1

            savings_pct = (
                round(saved_tokens / total_tokens * 100, 1)
                if total_tokens > 0
                else 0.0
            )

            # Compute validation at this threshold
            matrix = self.compute_matrix(nodes, threshold)

            data_points.append(ThresholdDataPoint(
                threshold=threshold,
                derivable_count=derivable_count,
                partial_count=partial_count,
                non_derivable_count=non_derivable_count,
                savings_percentage=savings_pct,
                precision=matrix.precision,
                recall=matrix.recall,
                f1_score=matrix.f1_score,
                false_positive_count=matrix.confusion_matrix.false_positives,
            ))

        return data_points

    def find_optimal_threshold(
        self,
        data_points: list[ThresholdDataPoint],
    ) -> float | None:
        """
        Find the optimal threshold that maximizes F1 while keeping precision >= 0.85.
        """
        valid_points = [p for p in data_points if p.precision >= 0.85]

        if not valid_points:
            # If no threshold achieves 85% precision, pick highest precision
            if data_points:
                return max(data_points, key=lambda p: p.precision).threshold
            return None

        # Among valid points, pick the one with the best F1
        best = max(valid_points, key=lambda p: p.f1_score)
        return best.threshold
