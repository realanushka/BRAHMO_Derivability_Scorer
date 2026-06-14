"""
API Router — All REST endpoints for the BRAHMO Derivability Scoring System.

Endpoints:
  GET  /api/nodes              → List all knowledge nodes
  POST /api/score-all          → Score all nodes (batch)
  POST /api/score-node         → Score a single node
  GET  /api/metrics            → Classification metrics
  GET  /api/validation-matrix  → Confusion matrix + precision/recall
  GET  /api/token-savings      → Token savings projections
  GET  /api/threshold-analysis → Threshold vs metrics chart data
"""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.models.schemas import (
    DeleteByFileResponse,
    MetricsResponse,
    NodesResponse,
    PasteNodesRequest,
    ScoreAllRequest,
    ScoreAllResponse,
    ScoreNodeRequest,
    ScoreNodeResponse,
    ThresholdAnalysisResponse,
    TokenSavingsResponse,
    UploadNodesResponse,
    ValidationMatrixResponse,
)
from app.services.scoring_service import ScoringService

router = APIRouter(prefix="/api", tags=["derivability"])

# Shared service instance
_service: ScoringService | None = None


def get_service() -> ScoringService:
    """Lazy-init the scoring service singleton."""
    global _service
    if _service is None:
        _service = ScoringService()
    return _service


def _detect_format(text: str, explicit: str | None = None) -> str:
    """
    Resolve the upload format. Honors an explicit 'csv'/'sql' if given,
    otherwise sniffs: text containing an INSERT statement is SQL, else CSV.
    """
    fmt = (explicit or "").lower()
    if fmt in ("csv", "sql"):
        return fmt
    return "sql" if "insert into" in text.lower() else "csv"


# ------------------------------------------------------------------
# GET /api/nodes — List all knowledge nodes
# ------------------------------------------------------------------

@router.get("/nodes", response_model=NodesResponse)
async def list_nodes(
    org_id: str = Query(default="supra", description="Organization ID"),
):
    """Get all knowledge nodes with their current scores."""
    try:
        service = get_service()
        return service.get_nodes(org_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------
# POST /api/score-all — Score all nodes
# ------------------------------------------------------------------

@router.post("/score-all", response_model=ScoreAllResponse)
async def score_all_nodes(request: ScoreAllRequest):
    """
    Run the scoring pipeline on ALL nodes in the database.
    Updates each node's derivability_score, derivability_class,
    scoring_reason, and non_derivable_portion.
    """
    try:
        service = get_service()
        return service.score_all(
            algorithm=request.algorithm,
            threshold=request.threshold,
            org_id=request.org_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------
# POST /api/score-node — Score a single node
# ------------------------------------------------------------------

@router.post("/score-node", response_model=ScoreNodeResponse)
async def score_single_node(request: ScoreNodeRequest):
    """
    Score a single node by ID (from database) or by content (ad-hoc).
    Use this for the surprise test — pass content directly.
    """
    try:
        service = get_service()
        return service.score_node(
            node_id=request.node_id,
            content=request.content,
            title=request.title,
            node_type=request.node_type or "FACT",
            algorithm=request.algorithm,
            threshold=request.threshold,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------
# POST /api/upload-nodes — Upload a CSV or SQL file of nodes
# ------------------------------------------------------------------

@router.post("/upload-nodes", response_model=UploadNodesResponse)
async def upload_nodes(file: UploadFile = File(...)):
    """
    Upload a file of knowledge nodes and store them in the database.

    Accepts:
      - .csv  — header row mapping to knowledge_nodes columns
      - .sql  — INSERT INTO knowledge_nodes (...) VALUES (...) statements
                (the SQL is parsed, NOT executed)

    Nodes are stored UNSCORED. Run "Rescore All" afterwards to score them.
    Duplicate ids are auto-renamed (e.g. D-01 -> D-01-1) so no node is dropped.
    """
    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")

    name = (file.filename or "").lower()
    if name.endswith(".csv"):
        fmt = "csv"
    elif name.endswith(".sql"):
        fmt = "sql"
    else:
        # Sniff: SQL files contain an INSERT statement; otherwise treat as CSV.
        fmt = "sql" if "insert into" in text.lower() else "csv"

    try:
        service = get_service()
        result = service.import_nodes(text, fmt)
        return UploadNodesResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------
# POST /api/nodes/delete-by-file — Delete uploaded nodes matching a file
# ------------------------------------------------------------------

@router.post("/nodes/delete-by-file", response_model=DeleteByFileResponse)
async def delete_nodes_by_file(file: UploadFile = File(...)):
    """
    Upload the SAME file again to delete its nodes from the database.

    The file's nodes are matched (by content) against the previously
    uploaded nodes and only those matches are deleted. The original seed
    nodes (upload_batch = NULL) are never matched, so they stay intact.
    Re-uploading the file afterwards re-inserts the nodes.
    """
    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")

    name = (file.filename or "").lower()
    if name.endswith(".csv"):
        fmt = "csv"
    elif name.endswith(".sql"):
        fmt = "sql"
    else:
        fmt = "sql" if "insert into" in text.lower() else "csv"

    try:
        service = get_service()
        return DeleteByFileResponse(**service.delete_nodes_by_file(text, fmt))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------
# POST /api/paste-nodes — Paste raw CSV/SQL text of nodes
# ------------------------------------------------------------------

@router.post("/paste-nodes", response_model=UploadNodesResponse)
async def paste_nodes(request: PasteNodesRequest):
    """
    Paste raw node text (CSV or SQL) directly — no file needed.

    Accepts one or many nodes:
      - CSV: a header row mapping to knowledge_nodes columns, then data rows.
      - SQL: INSERT INTO knowledge_nodes (...) VALUES (...) statements
             (the SQL is parsed, NOT executed).

    Format is auto-detected when not given. Nodes are stored UNSCORED — run
    "Rescore All" afterwards. Duplicate ids are auto-renamed so none is dropped.
    """
    text = request.text or ""
    if not text.strip():
        raise HTTPException(status_code=400, detail="No text provided to import.")

    fmt = _detect_format(text, request.format)
    try:
        service = get_service()
        return UploadNodesResponse(**service.import_nodes(text, fmt))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------
# POST /api/nodes/delete-by-text — Delete uploaded nodes matching pasted text
# ------------------------------------------------------------------

@router.post("/nodes/delete-by-text", response_model=DeleteByFileResponse)
async def delete_nodes_by_text(request: PasteNodesRequest):
    """
    Paste the SAME node text again to delete those nodes from the database.

    The pasted nodes are matched (by content) against the previously uploaded
    nodes and only those matches are deleted. The original seed nodes
    (upload_batch = NULL) are never matched, so they stay intact.
    """
    text = request.text or ""
    if not text.strip():
        raise HTTPException(status_code=400, detail="No text provided to delete.")

    fmt = _detect_format(text, request.format)
    try:
        service = get_service()
        return DeleteByFileResponse(**service.delete_nodes_by_file(text, fmt))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------
# GET /api/metrics — Classification metrics
# ------------------------------------------------------------------

@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    org_id: str = Query(default="supra"),
    threshold: float = Query(default=0.7, ge=0.0, le=1.0),
):
    """Get classification counts at the given threshold."""
    try:
        service = get_service()
        return service.get_metrics(threshold=threshold, org_id=org_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------
# GET /api/validation-matrix — Confusion matrix + precision/recall
# ------------------------------------------------------------------

@router.get("/validation-matrix", response_model=ValidationMatrixResponse)
async def get_validation_matrix(
    org_id: str = Query(default="supra"),
    threshold: float = Query(default=0.7, ge=0.0, le=1.0),
):
    """Get the validation confusion matrix comparing scored vs expected."""
    try:
        service = get_service()
        return service.get_validation_matrix(threshold=threshold, org_id=org_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------
# GET /api/token-savings — Token savings projections
# ------------------------------------------------------------------

@router.get("/token-savings", response_model=TokenSavingsResponse)
async def get_token_savings(
    org_id: str = Query(default="supra"),
    threshold: float = Query(default=0.7, ge=0.0, le=1.0),
):
    """Compute token savings and cost impact projections."""
    try:
        service = get_service()
        return service.get_token_savings(threshold=threshold, org_id=org_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------------
# GET /api/threshold-analysis — Threshold vs metrics chart data
# ------------------------------------------------------------------

@router.get("/threshold-analysis", response_model=ThresholdAnalysisResponse)
async def get_threshold_analysis(
    org_id: str = Query(default="supra"),
):
    """Generate threshold impact analysis data for the chart."""
    try:
        service = get_service()
        return service.get_threshold_analysis(org_id=org_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
