"""Optional Neo4j runtime API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.models.neo4j_runtime import Neo4jRuntimeStatus, Neo4jSyncResult
from app.services.neo4j_service import Neo4jMirrorService, get_neo4j_mirror_service


router = APIRouter(prefix="/neo4j", tags=["neo4j"])


@router.get("/status", response_model=Neo4jRuntimeStatus)
async def get_neo4j_status(
    service: Neo4jMirrorService = Depends(get_neo4j_mirror_service),
) -> Neo4jRuntimeStatus:
    """Return optional Neo4j runtime status."""

    return service.status()


@router.post("/documents/{document_id}/sync", response_model=Neo4jSyncResult)
async def sync_document_to_neo4j(
    document_id: UUID,
    service: Neo4jMirrorService = Depends(get_neo4j_mirror_service),
) -> Neo4jSyncResult:
    """Mirror one document graph to Neo4j."""

    return service.sync_document(document_id)
