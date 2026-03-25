import os
import structlog
from typing import List, Dict, Any, Optional
from .parser import ParserService
from .chunker import ChunkerService
from .extractor import ExtractorService
from .deduplicator import DeduplicatorService
from db.supabase_client import SupabaseService

logger = structlog.get_logger()

class PipelineService:
    def __init__(
        self,
        parser: ParserService,
        chunker: ChunkerService,
        extractor: ExtractorService,
        deduplicator: DeduplicatorService,
        supabase: SupabaseService
    ):
        self.parser = parser
        self.chunker = chunker
        self.extractor = extractor
        self.deduplicator = deduplicator
        self.supabase = supabase

    async def process_file(self, file_path: str, subject_name: str, doc_id: str):
        """Processes a single file. (Legacy support, now redirects to process_files)"""
        return await self.process_files([file_path], subject_name, doc_id)

    async def process_files(self, file_paths: List[str], subject_name: str, doc_id: str):
        """
        Coordinates the full extraction pipeline for multiple files as one unified project.
        """
        try:
            logger.info("pipeline_started", doc_id=doc_id, file_count=len(file_paths))
            
            # 1. Parse all files
            all_parsed_pages = []
            for fp in file_paths:
                pages = await self.parser.parse_file(fp)
                all_parsed_pages.extend(pages)
            
            if not all_parsed_pages:
                raise ValueError("No content extracted from the provided files.")

            # 2. Token Estimation & Routing
            full_text = "\n".join([p["content"] for p in all_parsed_pages])
            total_tokens = self.chunker.estimate_tokens(full_text)
            logger.info("token_estimation", total_tokens=total_tokens)

            if total_tokens < 75000:
                # Path A: Groq Flow (Small documents)
                logger.info("routing_to_groq_flow")
                chunks = await self.chunker.create_chunks(all_parsed_pages)
                raw_graph = await self.extractor.run_groq_pipeline(chunks, subject_name)
            else:
                # Path B: Gemini Flow (Large documents)
                logger.info("routing_to_gemini_flow")
                parts = self.chunker.create_large_parts(all_parsed_pages, pages_per_part=150)
                raw_graph = await self.extractor.run_gemini_large_pipeline(parts, subject_name)
            
            # 4. Deduplicate (Merge across all files)
            refined_graph = self.deduplicator.dedup_nodes(
                raw_graph.get("nodes", []), 
                raw_graph.get("edges", [])
            )
            
            # 5. Save to Database
            await self.supabase.save_graph(doc_id, refined_graph)
            
            # Update status to ready
            await self.supabase.update_document_status(doc_id, "ready")
            
            logger.info("pipeline_completed_successfully", doc_id=doc_id)
            return refined_graph

        except Exception as e:
            logger.error("pipeline_failed", doc_id=doc_id, error=str(e))
            await self.supabase.update_document_status(doc_id, "error")
            raise e
        finally:
            # Clean up all temp files
            for fp in file_paths:
                if os.path.exists(fp):
                    try:
                        os.remove(fp)
                    except:
                        pass
