from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
import shutil
import os
import uuid
from typing import Optional
import structlog

from services.parser import ParserService
from services.chunker import ChunkerService
from services.extractor import ExtractorService
from services.deduplicator import DeduplicatorService
from services.groq_client import GroqClient
from services.gemini_client import GeminiClient
from services.pipeline import PipelineService
from db.supabase_client import SupabaseService

logger = structlog.get_logger()
router = APIRouter(prefix="/api/upload", tags=["upload"])

# Initialize services
supabase_service = SupabaseService()
groq_client = GroqClient()
gemini_client = GeminiClient()
# Global instances tracking
_pipeline_service = None

def get_pipeline_service() -> PipelineService:
    global _pipeline_service
    if _pipeline_service is None:
        logger.info("initializing_heavy_ml_models")
        _pipeline_service = PipelineService(
            parser=ParserService(),
            chunker=ChunkerService(),
            extractor=ExtractorService(groq_client=groq_client, gemini_client=gemini_client),
            deduplicator=DeduplicatorService(),
            supabase=supabase_service
        )
    return _pipeline_service

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@router.post("")
async def upload_files(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    subject: str = Form(...),
    user_id: Optional[str] = Form(None)
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    temp_paths = []
    try:
        # 1. Save all files to temp directory
        for file in files:
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in [".pdf", ".docx", ".pptx", ".txt"]:
                continue
                
            file_id = str(uuid.uuid4())
            temp_file_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_ext}")
            
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            temp_paths.append(temp_file_path)

        if not temp_paths:
            raise HTTPException(status_code=400, detail="No valid supported files found")

        # 2. Create ONE document entry for the whole collection
        # Use subject as title if multiple files, or file name if only one
        doc_title = subject if len(files) > 1 else files[0].filename
        
        doc_entry = await supabase_service.create_document(
            title=doc_title,
            subject=subject,
            user_id=user_id
        )
        doc_id = doc_entry["id"]

        # 3. Start unified pipeline in background
        async def run_pipeline_task():
            import asyncio
            pipeline = await asyncio.to_thread(get_pipeline_service)
            await pipeline.process_files(temp_paths, subject, doc_id)
            
        background_tasks.add_task(run_pipeline_task)
        
        return {
            "message": f"Started processing {len(temp_paths)} files as a unified graph",
            "document_id": doc_id,
            "title": doc_title,
            "status": "processing"
        }

    except Exception as e:
        logger.error("upload_processing_failed", error=str(e))
        # Cleanup any saved files if we failed before starting background task
        for path in temp_paths:
            if os.path.exists(path):
                os.remove(path)
        raise HTTPException(status_code=500, detail=str(e))
