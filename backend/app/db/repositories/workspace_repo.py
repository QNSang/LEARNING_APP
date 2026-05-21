"""Workspace repository."""

from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from app.core.errors import AppError
from app.db.supabase_client import get_supabase_client
from app.models.workspace import (
    CrossDocumentConcept,
    Workspace,
    WorkspaceCreate,
    WorkspaceDocument,
    WorkspaceDocumentCreate,
    WorkspaceDocumentDetail,
    WorkspaceKnowledgeBase,
)
from app.pipeline.validator import normalize_node_key

from .base import execute_query, first_or_none, to_record


class WorkspaceRepository:
    """Persistence operations for subject-level workspaces."""

    def __init__(self) -> None:
        self.client = get_supabase_client()

    def list(self, user_id: UUID | None = None) -> list[Workspace]:
        query = self.client.table("workspaces").select("*").order("created_at", desc=True)
        if user_id is not None:
            query = query.eq("user_id", str(user_id))
        response = execute_query(query)
        return [Workspace.model_validate(row) for row in response.data or []]

    def get(self, workspace_id: UUID) -> Workspace | None:
        response = execute_query(
            self.client.table("workspaces")
            .select("*")
            .eq("id", str(workspace_id))
            .limit(1)
        )
        row = first_or_none(response.data or [])
        return Workspace.model_validate(row) if row else None

    def create(self, payload: WorkspaceCreate) -> Workspace:
        response = execute_query(self.client.table("workspaces").insert(to_record(payload)))
        row = first_or_none(response.data or [])
        if not row:
            raise AppError("Workspace was not created.", status_code=500)
        return Workspace.model_validate(row)

    def add_document(self, payload: WorkspaceDocumentCreate) -> WorkspaceDocument:
        response = execute_query(
            self.client.table("workspace_documents").upsert(
                to_record(payload),
                on_conflict="workspace_id,document_id",
            )
        )
        row = first_or_none(response.data or [])
        if not row:
            raise AppError("Document was not added to workspace.", status_code=500)
        return WorkspaceDocument.model_validate(row)

    def list_documents(self, workspace_id: UUID) -> list[WorkspaceDocumentDetail]:
        response = execute_query(
            self.client.table("workspace_documents")
            .select("documents!inner(id, title, subject, status, created_at)")
            .eq("workspace_id", str(workspace_id))
            .order("created_at")
        )
        documents = []
        for row in response.data or []:
            document = row.get("documents")
            if document:
                documents.append(WorkspaceDocumentDetail.model_validate(document))
        return documents

    def get_knowledge_base(self, workspace_id: UUID) -> WorkspaceKnowledgeBase:
        workspace = self.get(workspace_id)
        if workspace is None:
            raise AppError("Workspace not found.", status_code=404)

        documents = self.list_documents(workspace_id)
        return WorkspaceKnowledgeBase(
            workspace=workspace,
            documents=documents,
            cross_document_concepts=self.find_cross_document_concepts(workspace_id),
        )

    def find_cross_document_concepts(
        self,
        workspace_id: UUID,
        *,
        limit: int = 50,
    ) -> list[CrossDocumentConcept]:
        documents = self.list_documents(workspace_id)
        document_by_id = {document.id: document for document in documents}
        if not document_by_id:
            return []

        response = execute_query(
            self.client.table("knowledge_nodes")
            .select("id, document_id, label, term, description")
            .in_("document_id", [str(document_id) for document_id in document_by_id])
        )

        groups: dict[str, list[dict]] = defaultdict(list)
        for row in response.data or []:
            key = normalize_node_key(row.get("term") or row.get("label") or "")
            if key:
                groups[key].append(row)

        concepts: list[CrossDocumentConcept] = []
        for key, rows in groups.items():
            concept_document_ids = {UUID(str(row["document_id"])) for row in rows}
            if len(concept_document_ids) < 2:
                continue
            first = rows[0]
            descriptions = []
            for row in rows:
                description = row.get("description")
                if description and description not in descriptions:
                    descriptions.append(description)
            concepts.append(
                CrossDocumentConcept(
                    canonical_key=key,
                    label=first.get("label") or first.get("term") or key,
                    document_count=len(concept_document_ids),
                    node_count=len(rows),
                    documents=[
                        document_by_id[document_id]
                        for document_id in concept_document_ids
                        if document_id in document_by_id
                    ],
                    descriptions=descriptions[:5],
                )
            )

        concepts.sort(key=lambda concept: (concept.document_count, concept.node_count), reverse=True)
        return concepts[:limit]


def get_workspace_repository() -> WorkspaceRepository:
    return WorkspaceRepository()
