from fastapi import APIRouter, HTTPException
from db.supabase_client import SupabaseService
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/graph", tags=["graph"])
supabase = SupabaseService()

@router.get("/{document_id}")
async def get_graph(document_id: str):
    """
    Retrieves the knowledge graph for a specific document.
    """
    try:
        graph = await supabase.get_graph(document_id)
        logger.info("fetching_graph", document_id=document_id, nodes_count=len(graph["nodes"]), edges_count=len(graph["edges"]))
        return graph
    except Exception as e:
        logger.error("get_graph_failed", doc_id=document_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve graph")
