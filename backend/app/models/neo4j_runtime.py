"""Optional Neo4j runtime models."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


Neo4jRuntimeState = Literal["disabled", "not_configured", "ready", "unavailable"]


class Neo4jRuntimeStatus(BaseModel):
    state: Neo4jRuntimeState
    enabled: bool
    configured: bool
    message: str


class Neo4jSyncResult(BaseModel):
    document_id: UUID
    synced_at: datetime
    nodes_synced: int
    edges_synced: int
    chunks_synced: int
    runtime_status: Neo4jRuntimeStatus
