"""
Scoring Service — Orchestration layer connecting API endpoints
to the scorer engine, database, and validation.

Handles:
- Score all nodes (batch)
- Score single node (ad-hoc / surprise test)
- Metrics computation
- Token savings calculation
- Validation matrix generation
- Threshold analysis
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.models.schemas import (
    KnowledgeNode,
    MetricsResponse,
    NodesResponse,
    ScoreAllResponse,
    ScoreNodeResponse,
    ScoringResult,
    ThresholdAnalysisResponse,
    TokenSavingsResponse,
    ValidationMatrixResponse,
)
from app.scorer.hybrid_scorer import HybridScorer
from app.services.node_parser import parse_csv, parse_sql
from app.services.supabase_client import SupabaseService
from app.utils.token_counter import compute_cost_savings, compute_token_savings
from app.validators.validation_engine import ValidationEngine


# Columns accepted from an uploaded file. Scorer-managed columns
# (derivability_score/class, scoring_reason, type_floor_applied) are
# intentionally excluded — they are filled in by "Rescore All".
VALID_NODE_TYPES = {"CONSTRAINT", "DECISION", "ANTI_PATTERN", "FACT"}
_TEXT_COLS = (
    "org_id", "type", "title", "content",
    "expected_derivability", "expected_score_range",
    "department", "non_derivable_portion",
)


def _to_float(value, default: float = 0.5) -> float:
    """Coerce a parsed value to float, falling back to a default."""
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value):
    """Coerce a parsed value to int, or None if not parseable."""
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


class ScoringService:
    """
    Central service for all scoring operations.
    Coordinates between scorers, database, and validators.
    """

    def __init__(self):
        self.db = SupabaseService()
        self.validator = ValidationEngine()
        self._scorer: Optional[HybridScorer] = None

    def _get_scorer(self, org_id: str = "supra") -> HybridScorer:
        """Get or create a scorer with org-specific configuration."""
        org_config = self.db.get_org_config(org_id)
        return HybridScorer(
            type_floors=org_config.type_floors,
        )

    # ------------------------------------------------------------------
    # Fetch Nodes
    # ------------------------------------------------------------------

    def get_nodes(self, org_id: str = "supra") -> NodesResponse:
        """Get all nodes for an organization."""
        nodes = self.db.get_all_nodes(org_id)
        return NodesResponse(nodes=nodes, total=len(nodes))

    # ------------------------------------------------------------------
    # Score All Nodes
    # ------------------------------------------------------------------

    def score_all(
        self,
        algorithm: str = "hybrid",
        threshold: float = 0.7,
        org_id: str = "supra",
    ) -> ScoreAllResponse:
        """Score all nodes and update the database."""
        scorer = self._get_scorer(org_id)
        nodes = self.db.get_all_nodes(org_id)
        results: list[ScoringResult] = []

        for node in nodes:
            result = scorer.score_node(
                content=node.content,
                title=node.title,
                node_type=node.type,
                node_id=node.id,
                threshold=threshold,
                algorithm=algorithm,
            )
            results.append(result)

            # Update database
            self.db.update_node_score(
                node_id=node.id,
                derivability_score=result.final_score,
                derivability_class=result.classification,
                scoring_reason=result.scoring_reason,
                type_floor_applied=result.type_floor_applied,
                non_derivable_portion=result.non_derivable_portion,
            )

        return ScoreAllResponse(
            scored_count=len(results),
            algorithm=algorithm,
            threshold=threshold,
            results=results,
        )

    # ------------------------------------------------------------------
    # Score Single Node
    # ------------------------------------------------------------------

    def score_node(
        self,
        node_id: Optional[str] = None,
        content: Optional[str] = None,
        title: Optional[str] = None,
        node_type: str = "FACT",
        algorithm: str = "hybrid",
        threshold: float = 0.7,
        org_id: str = "supra",
    ) -> ScoreNodeResponse:
        """
        Score a single node — either by ID (fetch from DB) or by content
        (ad-hoc / surprise test).
        """
        scorer = self._get_scorer(org_id)

        # If node_id provided, fetch from database
        if node_id:
            node = self.db.get_node_by_id(node_id)
            if node:
                content = node.content
                title = node.title
                node_type = node.type
            else:
                raise ValueError(f"Node '{node_id}' not found")

        if not content:
            raise ValueError("Either node_id or content must be provided")

        result = scorer.score_node(
            content=content,
            title=title or "",
            node_type=node_type,
            node_id=node_id or "ad-hoc",
            threshold=threshold,
            algorithm=algorithm,
        )

        # If this was a real node, update the database
        if node_id:
            self.db.update_node_score(
                node_id=node_id,
                derivability_score=result.final_score,
                derivability_class=result.classification,
                scoring_reason=result.scoring_reason,
                type_floor_applied=result.type_floor_applied,
                non_derivable_portion=result.non_derivable_portion,
            )

        return ScoreNodeResponse(result=result)

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def get_metrics(
        self,
        threshold: float = 0.7,
        org_id: str = "supra",
    ) -> MetricsResponse:
        """Compute classification metrics at the given threshold."""
        nodes = self.db.get_all_nodes(org_id)

        scored = [n for n in nodes if n.derivability_class != "UNKNOWN"]
        derivable = sum(1 for n in nodes if n.derivability_score >= threshold)
        partial = sum(
            1 for n in nodes
            if 0.40 <= n.derivability_score < threshold
        )
        non_derivable = sum(1 for n in nodes if n.derivability_score < 0.40)
        unknown = sum(1 for n in nodes if n.derivability_class == "UNKNOWN")

        return MetricsResponse(
            total_nodes=len(nodes),
            scored_nodes=len(scored),
            derivable_count=derivable,
            partial_count=partial,
            non_derivable_count=non_derivable,
            unknown_count=unknown,
            threshold=threshold,
        )

    # ------------------------------------------------------------------
    # Validation Matrix
    # ------------------------------------------------------------------

    def get_validation_matrix(
        self,
        threshold: float = 0.7,
        org_id: str = "supra",
    ) -> ValidationMatrixResponse:
        """Compute the validation confusion matrix."""
        nodes = self.db.get_all_nodes(org_id)
        return self.validator.compute_matrix(nodes, threshold)

    # ------------------------------------------------------------------
    # Token Savings
    # ------------------------------------------------------------------

    def get_token_savings(
        self,
        threshold: float = 0.7,
        org_id: str = "supra",
    ) -> TokenSavingsResponse:
        """Compute token savings at current threshold."""
        nodes = self.db.get_all_nodes(org_id)

        total_tokens = 0
        saved_tokens = 0
        derivable_tokens = 0
        partial_tokens_saved = 0
        non_derivable_tokens = 0

        for node in nodes:
            tokens_full = node.tokens_full or 0
            tokens_delta = node.tokens_delta or 0
            total_tokens += tokens_full
            score = node.derivability_score

            if score >= threshold:
                # DERIVABLE — exclude entirely
                derivable_tokens += tokens_full
                saved_tokens += tokens_full
            elif score >= 0.40:
                # PARTIALLY_DERIVABLE — use delta only
                saved = max(0, tokens_full - tokens_delta)
                partial_tokens_saved += saved
                saved_tokens += saved
            else:
                # NON_DERIVABLE — include full
                non_derivable_tokens += tokens_full

        savings_pct = round(saved_tokens / total_tokens * 100, 1) if total_tokens > 0 else 0.0

        cost = compute_cost_savings(saved_tokens)

        return TokenSavingsResponse(
            total_tokens=total_tokens,
            saved_tokens=saved_tokens,
            savings_percentage=savings_pct,
            derivable_tokens=derivable_tokens,
            partial_tokens_saved=partial_tokens_saved,
            non_derivable_tokens=non_derivable_tokens,
            **cost,
        )

    # ------------------------------------------------------------------
    # Threshold Analysis
    # ------------------------------------------------------------------

    def get_threshold_analysis(
        self,
        org_id: str = "supra",
    ) -> ThresholdAnalysisResponse:
        """Generate threshold vs metrics data for the chart."""
        nodes = self.db.get_all_nodes(org_id)
        data_points = self.validator.compute_threshold_analysis(nodes)
        optimal = self.validator.find_optimal_threshold(data_points)

        return ThresholdAnalysisResponse(
            data_points=data_points,
            optimal_threshold=optimal,
        )

    # ------------------------------------------------------------------
    # Upload / Import Nodes
    # ------------------------------------------------------------------

    def import_nodes(self, content: str, fmt: str) -> dict:
        """
        Parse uploaded file content (csv|sql) and insert the nodes.

        Never drops a node on an id collision — instead it assigns a new
        unique id (e.g. 'D-01' -> 'D-01-1') and reports the rename.
        Nodes are stored unscored; the caller scores them via "Rescore All".
        """
        if fmt == "csv":
            raw_nodes = parse_csv(content)
        elif fmt == "sql":
            raw_nodes = parse_sql(content)
        else:
            raise ValueError(f"Unsupported format '{fmt}' (expected 'csv' or 'sql')")

        # Unique, time-sortable tag for this upload. Only stored if the
        # optional upload_batch column exists (otherwise uploads still work).
        batch_id = "upload-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        tag_uploads = self.db.has_upload_batch_column()

        used_ids = set(self.db.get_all_node_ids())
        rows: list[dict] = []
        renamed: list[dict] = []
        warnings: list[str] = []

        for index, raw in enumerate(raw_nodes):
            node, warning = self._normalize_node(raw, index)
            if warning:
                warnings.append(warning)
            if node is None:
                continue

            original_id = node.get("id") or f"NODE-{index + 1}"
            new_id = original_id
            if (not node.get("id")) or (new_id in used_ids):
                new_id = self._make_unique_id(original_id, used_ids)
                renamed.append({"original_id": original_id, "new_id": new_id})
            node["id"] = new_id
            if tag_uploads:
                node["upload_batch"] = batch_id
            used_ids.add(new_id)
            rows.append(node)

        inserted = self.db.insert_nodes(rows)

        return {
            "format": fmt,
            "parsed_count": len(raw_nodes),
            "inserted_count": inserted,
            "batch_id": (batch_id if (inserted and tag_uploads) else None),
            "renamed": renamed,
            "warnings": warnings,
        }

    def delete_nodes_by_file(self, content: str, fmt: str) -> dict:
        """
        Delete uploaded nodes that match the nodes in the given file.

        Matching is by node CONTENT (exact, whitespace-trimmed) so it still
        works if ids were auto-renamed on upload. Only nodes added via upload
        (upload_batch IS NOT NULL) are considered, so the original seed nodes
        are never deleted — even if their content happens to match.
        """
        if fmt == "csv":
            file_nodes = parse_csv(content)
        elif fmt == "sql":
            file_nodes = parse_sql(content)
        else:
            raise ValueError(f"Unsupported format '{fmt}' (expected 'csv' or 'sql')")

        # Build the set of contents present in the uploaded file.
        file_contents = {
            (n.get("content") or "").strip()
            for n in file_nodes
            if (n.get("content") or "").strip()
        }

        uploaded = self.db.get_uploaded_nodes()
        to_delete = [
            node["id"]
            for node in uploaded
            if (node.get("content") or "").strip() in file_contents
        ]

        deleted = self.db.delete_nodes_by_ids(to_delete)

        if deleted == 0:
            message = (
                f"No matching uploaded nodes found for this file "
                f"(parsed {len(file_nodes)} node(s)). Seed nodes are never matched."
            )
        else:
            message = f"Deleted {deleted} node(s) matching this file."

        return {
            "parsed_count": len(file_nodes),
            "deleted_count": deleted,
            "deleted_ids": to_delete,
            "message": message,
        }

    def _normalize_node(self, raw: dict, index: int) -> tuple[Optional[dict], Optional[str]]:
        """Coerce a raw parsed row into a valid insertable node dict."""
        node: dict = {}
        for col in _TEXT_COLS:
            value = raw.get(col)
            if value is not None and value != "":
                node[col] = str(value)

        if raw.get("id") is not None and str(raw["id"]).strip() != "":
            node["id"] = str(raw["id"]).strip()

        # org_id is a required FK; default to the seed org.
        node.setdefault("org_id", "supra")

        # type must satisfy the DB CHECK constraint.
        warning = None
        node_type = (node.get("type") or "").upper()
        if node_type not in VALID_NODE_TYPES:
            warning = (
                f"Row {index + 1}: invalid/missing type "
                f"'{node.get('type')}' -> defaulted to FACT"
            )
            node_type = "FACT"
        node["type"] = node_type

        node.setdefault("title", "")
        node.setdefault("content", "")

        # importance is NOT NULL; default to neutral 0.5.
        node["importance"] = _to_float(raw.get("importance"), default=0.5)

        tokens_full = _to_int(raw.get("tokens_full"))
        if tokens_full is not None:
            node["tokens_full"] = tokens_full
        tokens_delta = _to_int(raw.get("tokens_delta"))
        if tokens_delta is not None:
            node["tokens_delta"] = tokens_delta

        # Drop junk rows that carry neither title nor content.
        if not node["title"] and not node["content"]:
            return None, warning

        return node, warning

    @staticmethod
    def _make_unique_id(base: str, used: set[str]) -> str:
        """Return base, or base-1 / base-2 / ... if base is already taken."""
        n = 1
        candidate = f"{base}-{n}"
        while candidate in used:
            n += 1
            candidate = f"{base}-{n}"
        return candidate
