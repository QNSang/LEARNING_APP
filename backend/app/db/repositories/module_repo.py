"""Module repository."""

from uuid import UUID

from app.core.errors import AppError
from app.db.supabase_client import get_supabase_client
from app.models.module import Module, ModuleCreate, ModuleNode, ModuleNodeCreate

from .base import execute_query, first_or_none, to_record


class ModuleRepository:
    """Persistence operations for learning modules."""

    def __init__(self) -> None:
        self.client = get_supabase_client()

    def list_by_document(self, document_id: UUID) -> list[Module]:
        response = execute_query(
            self.client.table("modules")
            .select("*")
            .eq("document_id", str(document_id))
            .order("order_index")
        )
        return [Module.model_validate(row) for row in response.data or []]

    def create(self, payload: ModuleCreate) -> Module:
        response = execute_query(self.client.table("modules").insert(to_record(payload)))
        row = first_or_none(response.data or [])
        if not row:
            raise AppError("Module was not created.", status_code=500)
        return Module.model_validate(row)

    def add_node(self, payload: ModuleNodeCreate) -> ModuleNode:
        response = execute_query(
            self.client.table("module_nodes").insert(to_record(payload))
        )
        row = first_or_none(response.data or [])
        if not row:
            raise AppError("Module node link was not created.", status_code=500)
        return ModuleNode.model_validate(row)


def get_module_repository() -> ModuleRepository:
    return ModuleRepository()
