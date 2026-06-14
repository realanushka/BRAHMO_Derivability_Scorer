"""
Supabase Client — Database access layer for knowledge nodes.

Uses the supabase-py client to CRUD knowledge_nodes and organizations.
Reads credentials from environment variables.
"""

from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv
from supabase import create_client, Client

from app.models.schemas import KnowledgeNode, OrgConfig

# Load .env from backend directory
load_dotenv()


def get_supabase_client() -> Client:
    """Create and return a Supabase client instance."""
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "")

    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_KEY must be set in .env file. "
            "See .env.example for details."
        )

    return create_client(url, key)


class SupabaseService:
    """Database access layer for the derivability scoring system."""

    def __init__(self):
        self.client = get_supabase_client()
        self._has_batch_col: Optional[bool] = None

    def has_upload_batch_column(self) -> bool:
        """
        Detect (once, cached) whether the optional `upload_batch` column exists.
        When present, uploads are tagged and deletes are restricted to uploaded
        nodes (seed nodes protected). When absent, the feature still works but
        without the seed-protection guarantee. Run database/add_upload_batch_column.sql
        and restart the server to enable it.
        """
        if self._has_batch_col is None:
            try:
                self.client.table("knowledge_nodes").select("upload_batch").limit(1).execute()
                self._has_batch_col = True
            except Exception:
                self._has_batch_col = False
        return self._has_batch_col

    # ------------------------------------------------------------------
    # Organizations
    # ------------------------------------------------------------------

    def get_org_config(self, org_id: str = "supra") -> OrgConfig:
        """Get organization configuration including type floors and threshold."""
        try:
            result = (
                self.client.table("organizations")
                .select("config")
                .eq("id", org_id)
                .single()
                .execute()
            )
            config_data = result.data.get("config", {})
            return OrgConfig(**config_data)
        except Exception:
            # Return defaults if org not found
            return OrgConfig()

    # ------------------------------------------------------------------
    # Knowledge Nodes — Read
    # ------------------------------------------------------------------

    def get_all_nodes(self, org_id: str = "supra") -> list[KnowledgeNode]:
        """Get all knowledge nodes for an organization."""
        result = (
            self.client.table("knowledge_nodes")
            .select("*")
            .eq("org_id", org_id)
            .order("id")
            .execute()
        )
        return [KnowledgeNode(**row) for row in result.data]

    def get_node_by_id(self, node_id: str) -> Optional[KnowledgeNode]:
        """Get a single knowledge node by ID."""
        try:
            result = (
                self.client.table("knowledge_nodes")
                .select("*")
                .eq("id", node_id)
                .single()
                .execute()
            )
            return KnowledgeNode(**result.data)
        except Exception:
            return None

    def get_all_node_ids(self) -> set[str]:
        """Return the set of all existing node IDs (across all orgs)."""
        result = self.client.table("knowledge_nodes").select("id").execute()
        return {row["id"] for row in result.data}

    # ------------------------------------------------------------------
    # Knowledge Nodes — Insert (uploaded nodes)
    # ------------------------------------------------------------------

    def insert_nodes(self, rows: list[dict]) -> int:
        """
        Bulk-insert new knowledge nodes. Each row must already have a unique
        `id` (callers are responsible for de-duplicating against existing IDs).
        Returns the number of rows inserted.
        """
        if not rows:
            return 0
        result = self.client.table("knowledge_nodes").insert(rows).execute()
        return len(result.data or [])

    # ------------------------------------------------------------------
    # Knowledge Nodes — Delete uploaded nodes (by file match)
    # ------------------------------------------------------------------

    def get_uploaded_nodes(self) -> list[dict]:
        """
        Return id/title/content for nodes eligible for delete-by-file.

        If the `upload_batch` column exists, only nodes added via upload
        (upload_batch IS NOT NULL) are returned — seed nodes are excluded and
        can never be matched. If the column does not exist, all nodes are
        returned (the feature still works, but seed protection is not enforced).
        """
        if self.has_upload_batch_column():
            result = (
                self.client.table("knowledge_nodes")
                .select("id, title, content, upload_batch")
                .execute()
            )
            return [
                {"id": row["id"], "title": row.get("title", ""), "content": row.get("content", "")}
                for row in result.data
                if row.get("upload_batch")
            ]

        # Fallback: column not present yet — match across all nodes.
        result = (
            self.client.table("knowledge_nodes")
            .select("id, title, content")
            .execute()
        )
        return [
            {"id": row["id"], "title": row.get("title", ""), "content": row.get("content", "")}
            for row in result.data
        ]

    def delete_nodes_by_ids(self, ids: list[str]) -> int:
        """Delete nodes whose id is in the given list. Returns count deleted."""
        if not ids:
            return 0
        result = (
            self.client.table("knowledge_nodes")
            .delete()
            .in_("id", ids)
            .execute()
        )
        return len(result.data or [])

    # ------------------------------------------------------------------
    # Knowledge Nodes — Update (scoring results)
    # ------------------------------------------------------------------

    def update_node_score(
        self,
        node_id: str,
        derivability_score: float,
        derivability_class: str,
        scoring_reason: str,
        type_floor_applied: bool = False,
        non_derivable_portion: Optional[str] = None,
    ) -> bool:
        """Update a node's scoring results in the database."""
        update_data = {
            "derivability_score": derivability_score,
            "derivability_class": derivability_class,
            "scoring_reason": scoring_reason,
            "type_floor_applied": type_floor_applied,
        }

        if non_derivable_portion is not None:
            update_data["non_derivable_portion"] = non_derivable_portion

        try:
            self.client.table("knowledge_nodes").update(
                update_data
            ).eq("id", node_id).execute()
            return True
        except Exception as e:
            print(f"Error updating node {node_id}: {e}")
            return False

    def batch_update_scores(
        self,
        updates: list[dict],
    ) -> int:
        """
        Batch update multiple nodes' scores.

        Args:
            updates: List of dicts with node_id and scoring fields

        Returns:
            Number of successfully updated nodes
        """
        success_count = 0
        for update in updates:
            node_id = update.pop("node_id", None)
            if not node_id:
                continue
            try:
                self.client.table("knowledge_nodes").update(
                    update
                ).eq("id", node_id).execute()
                success_count += 1
            except Exception as e:
                print(f"Error updating node {node_id}: {e}")
        return success_count
