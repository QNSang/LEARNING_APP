"""Document repository."""

from uuid import UUID

from app.core.errors import AppError
from app.db.supabase_client import get_supabase_client
from app.models.document import Document, DocumentCreate, DocumentUpdate

from .base import execute_query, first_or_none, to_record


class DocumentRepository:
    """Persistence operations for documents."""

    table_name = "documents"

    def __init__(self) -> None:
        self.client = get_supabase_client()

    def list(self) -> list[Document]:
        response = execute_query(
            self.client.table(self.table_name)
            .select("*")
            .order("created_at", desc=True)
        )
        return [Document.model_validate(row) for row in response.data or []]

    def get(self, document_id: UUID) -> Document | None:
        response = execute_query(
            self.client.table(self.table_name)
            .select("*")
            .eq("id", str(document_id))
            .limit(1)
        )
        row = first_or_none(response.data or [])
        return Document.model_validate(row) if row else None

    def create(self, payload: DocumentCreate) -> Document:
        response = execute_query(
            self.client.table(self.table_name)
            .insert(to_record(payload))
        )
        row = first_or_none(response.data or [])
        if not row:
            raise AppError("Document was not created.", status_code=500)
        return Document.model_validate(row)

    def update(self, document_id: UUID, payload: DocumentUpdate) -> Document:
        record = to_record(payload)
        if not record:
            document = self.get(document_id)
            if document is None:
                raise AppError("Document not found.", status_code=404)
            return document

        response = execute_query(
            self.client.table(self.table_name)
            .update(record)
            .eq("id", str(document_id))
        )
        row = first_or_none(response.data or [])
        if not row:
            raise AppError("Document not found.", status_code=404)
        return Document.model_validate(row)


def get_document_repository() -> DocumentRepository:
    return DocumentRepository()
