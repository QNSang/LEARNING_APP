from fastapi import APIRouter, HTTPException
from db.supabase_client import SupabaseService
from services.gemini_client import GeminiClient
import structlog
import json
from pydantic import BaseModel

logger = structlog.get_logger()
router = APIRouter(prefix="/api/ai", tags=["ai"])

supabase = SupabaseService()
gemini = GeminiClient()

class ExplainRequest(BaseModel):
    node_label: str

@router.post("/explain/{node_db_id}")
async def explain_node(node_db_id: str, request: ExplainRequest):
    """
    Generates a real-world intuition for a specific node and caches it in the database.
    """
    node_label = request.node_label

    prompt = f"""Bạn là một chuyên gia sư phạm. Hãy giải thích khái niệm "{node_label}" theo phong cách "ELI5" (giải thích như cho đứa trẻ 5 tuổi).
    
    Yêu cầu trả về JSON với cấu trúc:
    {{
      "intuition": "Trình bày ngữ cảnh,Một đoạn văn ngắn sử dụng ẩn dụ hoặc ngôn ngữ đời thường để giải thích bản chất khái niệm. ",
      "applications": ["Ứng dụng thực tế 1", "Ứng dụng thực tế 2", "Ứng dụng thực tế 3"],
      "requirements": ["Yêu cầu bắt buộc phải hiểu 1", "Yêu cầu 2", "Kỹ năng cần có 3"]
    }}
    Chỉ trả về JSON, không có text khác."""

    try:
        raw_json = await gemini.generate_content(prompt, is_json=True)
        explanation_data = json.loads(raw_json)
        
        # Cache the result in database
        await supabase.cache_node_explanation(node_db_id, explanation_data)
        
        return explanation_data
    except Exception as e:
        logger.error("explain_node_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to generate AI explanation")
