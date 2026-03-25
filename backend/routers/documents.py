from fastapi import APIRouter, HTTPException
from db.supabase_client import SupabaseService
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/documents", tags=["documents"])
supabase = SupabaseService()

@router.get("")
async def list_documents():
    """
    Retrieves all documents from the database.
    """
    try:
        # In a real app, you'd filter by user_id
        response = supabase.client.table("documents").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        logger.error("list_documents_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve documents")

@router.get("/{document_id}")
async def get_document(document_id: str):
    """
    Retrieves a single document's metadata.
    """
    try:
        response = supabase.client.table("documents").select("*").eq("id", document_id).single().execute()
        return response.data
    except Exception as e:
        logger.error("get_document_failed", doc_id=document_id, error=str(e))
        raise HTTPException(status_code=404, detail="Document not found")

@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    Deletes a document and its knowledge graph.
    """
    try:
        await supabase.delete_document(document_id)
        return {"status": "success", "message": "Document deleted"}
    except Exception as e:
        logger.error("delete_document_failed", doc_id=document_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete document")
