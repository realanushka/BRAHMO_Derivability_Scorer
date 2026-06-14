"""
Pydantic schemas for BRAHMO Derivability Scoring System.

Defines request/response models for all API endpoints,
plus internal data models used by the scoring pipeline.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Internal Data Models
# ---------------------------------------------------------------------------

class ScoringSignal(BaseModel):
    """A single scoring signal detected by the heuristic scorer."""
    name: str
    weight: float
    description: str
    matched_text: Optional[str] = None


class OrgConfig(BaseModel):
    """Organization-level configuration for derivability scoring."""
    derivability_threshold: float = 0.7
    type_floors: dict[str, float] = Field(
        default_factory=lambda: {
            "CONSTRAINT": 0.50,
            "ANTI_PATTERN": 0.60,
            "DECISION": 1.0,
            "FACT": 1.0,
        }
    )


# ---------------------------------------------------------------------------
# Knowledge Node Models
# ---------------------------------------------------------------------------

class KnowledgeNode(BaseModel):
    """Full representation of a knowledge node from the database."""
    id: str
    org_id: str
    type: str
    title: str
    content: str
    importance: float
    derivability_score: float = 0.5
    derivability_class: str = "UNKNOWN"
    non_derivable_portion: Optional[str] = None
    expected_derivability: Optional[str] = None
    expected_score_range: Optional[str] = None
    department: Optional[str] = None
    tokens_full: Optional[int] = None
    tokens_delta: Optional[int] = None
    scoring_reason: Optional[str] = None
    type_floor_applied: bool = False
    upload_batch: Optional[str] = None
    created_at: Optional[datetime] = None


class ScoringResult(BaseModel):
    """Result of scoring a single node."""
    node_id: str
    raw_score: float
    heuristic_score: float
    tfidf_score: float
    final_score: float
    classification: str
    signals: list[ScoringSignal] = []
    scoring_reason: str
    type_floor_applied: bool = False
    non_derivable_portion: Optional[str] = None


# ---------------------------------------------------------------------------
# API Request Models
# ---------------------------------------------------------------------------

class ScoreAllRequest(BaseModel):
    """Request body for POST /score-all."""
    algorithm: str = Field(
        default="hybrid",
        description="Scoring algorithm: 'heuristic', 'tfidf', or 'hybrid'",
    )
    threshold: float = Field(
        default=0.7,
        ge=0.0, le=1.0,
        description="Derivability threshold for classification",
    )
    org_id: str = Field(
        default="supra",
        description="Organization ID",
    )


class ScoreNodeRequest(BaseModel):
    """Request body for POST /score-node."""
    node_id: Optional[str] = None
    content: Optional[str] = None
    title: Optional[str] = None
    node_type: Optional[str] = "FACT"
    algorithm: str = "hybrid"
    threshold: float = 0.7


# ---------------------------------------------------------------------------
# API Response Models
# ---------------------------------------------------------------------------

class NodesResponse(BaseModel):
    """Response for GET /nodes."""
    nodes: list[KnowledgeNode]
    total: int


class ScoreAllResponse(BaseModel):
    """Response for POST /score-all."""
    scored_count: int
    algorithm: str
    threshold: float
    results: list[ScoringResult]


class ScoreNodeResponse(BaseModel):
    """Response for POST /score-node."""
    result: ScoringResult


class MetricsResponse(BaseModel):
    """Response for GET /metrics."""
    total_nodes: int
    scored_nodes: int
    derivable_count: int
    partial_count: int
    non_derivable_count: int
    unknown_count: int
    threshold: float


class ConfusionMatrix(BaseModel):
    """Confusion matrix values."""
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0


class ValidationMatrixResponse(BaseModel):
    """Response for GET /validation-matrix."""
    confusion_matrix: ConfusionMatrix
    precision: float
    recall: float
    f1_score: float
    false_positive_rate: float
    false_positive_nodes: list[str] = []
    false_negative_nodes: list[str] = []
    partial_matches: list[str] = []
    total_evaluated: int


class TokenSavingsResponse(BaseModel):
    """Response for GET /token-savings."""
    total_tokens: int
    saved_tokens: int
    savings_percentage: float
    derivable_tokens: int
    partial_tokens_saved: int
    non_derivable_tokens: int
    session_savings_dollars: float
    daily_savings_50_engineers: float
    annual_savings_50_engineers: float
    daily_savings_500_engineers: float
    annual_savings_500_engineers: float


class ThresholdDataPoint(BaseModel):
    """Single data point for threshold analysis."""
    threshold: float
    derivable_count: int
    partial_count: int
    non_derivable_count: int
    savings_percentage: float
    precision: float
    recall: float
    f1_score: float
    false_positive_count: int


class ThresholdAnalysisResponse(BaseModel):
    """Response for GET /threshold-analysis."""
    data_points: list[ThresholdDataPoint]
    optimal_threshold: Optional[float] = None


# ---------------------------------------------------------------------------
# Upload Models
# ---------------------------------------------------------------------------

class RenamedNode(BaseModel):
    """Records a node whose id was changed to avoid a duplicate."""
    original_id: str
    new_id: str


class PasteNodesRequest(BaseModel):
    """Request body for pasting raw node text (CSV or SQL) directly."""
    text: str = Field(..., description="Raw CSV or SQL text of one or more nodes")
    format: Optional[str] = Field(
        default=None,
        description="'csv' or 'sql'. If omitted, the format is auto-detected.",
    )


class UploadNodesResponse(BaseModel):
    """Response for POST /upload-nodes."""
    format: str
    parsed_count: int
    inserted_count: int
    batch_id: Optional[str] = None
    renamed: list[RenamedNode] = []
    warnings: list[str] = []


class DeleteByFileResponse(BaseModel):
    """Response for POST /nodes/delete-by-file."""
    parsed_count: int
    deleted_count: int
    deleted_ids: list[str] = []
    message: str
