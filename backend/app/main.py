"""
BRAHMO Derivability Scoring System — FastAPI Application

Entry point for the backend server.
Run with: uvicorn app.main:app --reload --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers.nodes import router as nodes_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events — startup and shutdown."""
    # Startup: log that the server is ready
    print("[STARTUP] BRAHMO Derivability Scoring System - Starting up...")
    print("[INFO] API docs available at: http://localhost:8000/docs")
    yield
    # Shutdown
    print("[SHUTDOWN] BRAHMO Derivability Scoring System - Shutting down...")


app = FastAPI(
    title="BRAHMO Derivability Scoring System",
    description=(
        "Token Savings Engine: Pre-compute derivability scores for knowledge nodes "
        "to classify them as DERIVABLE, PARTIALLY_DERIVABLE, or NON_DERIVABLE. "
        "Zero LLM calls at query time."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # Alternative dev server
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API router
app.include_router(nodes_router)


@app.get("/", tags=["health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "BRAHMO Derivability Scoring System",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "service": "brahmo-derivability-scorer",
        "version": "1.0.0",
        "endpoints": [
            "GET  /api/nodes",
            "POST /api/score-all",
            "POST /api/score-node",
            "GET  /api/metrics",
            "GET  /api/validation-matrix",
            "GET  /api/token-savings",
            "GET  /api/threshold-analysis",
        ],
    }
