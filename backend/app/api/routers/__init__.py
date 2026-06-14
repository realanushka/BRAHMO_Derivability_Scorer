"""
API Routers Package — Contains route handlers for all REST endpoints.
"""

from app.api.routers.nodes import router as nodes_router

__all__ = ["nodes_router"]
