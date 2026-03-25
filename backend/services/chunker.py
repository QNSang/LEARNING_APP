import re
from typing import List, Dict, Any
import structlog
import tiktoken

logger = structlog.get_logger()

# Regex nhận diện ranh giới tự nhiên để cắt chunk
_HEADING_RE = re.compile(r"^\[.+\]$", re.MULTILINE)          # [Heading] từ parser docx
_SLIDE_RE   = re.compile(r"^\[Slide \d+\]", re.MULTILINE)    # [Slide N] từ parser pptx

class ChunkerService:
    def __init__(
        self,
        # FIX: Áp dụng Micro-chunking: Giảm target_chunk_size xuống
        min_tokens: int = 400,    
        max_tokens: int = 1000,     
        overlap: int = 150,        
    ):
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens
        self.overlap = overlap
        # Khởi tạo Tokenizer thực thụ (Dùng cl100k_base là chuẩn chung tốt nhất hiện nay)
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning("tiktoken_init_failed", error=str(e))
            self.tokenizer = None

    # ─────────────────────────────────────────
    # Token estimation
    # ─────────────────────────────────────────
    def estimate_tokens(self, text: str) -> int:
        """
        Đếm chính xác số lượng token bằng Tiktoken.
        Nếu thư viện lỗi, fallback về tỷ lệ an toàn 3.0 cho Tiếng Việt.
        """
        if not text:
            return 0
            
        if self.tokenizer:
            # Đếm chính xác 100% số lượng token
            return len(self.tokenizer.encode(text, disallowed_special=()))
        
        # Fallback kinh nghiệm nếu không cài tiktoken
        return int(len(text) / 3.0)
    # ─────────────────────────────────────────
    # Main: create chunks cho Groq flow
    # ─────────────────────────────────────────
    async def create_chunks(
        self, parsed_pages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        raw_chunks: List[tuple] =[]  
        current_text = ""
        current_pages = []

        for page in parsed_pages:
            page_text = page["content"]
            page_tokens = self.estimate_tokens(page_text)

            if page_tokens > self.max_tokens:
                if current_text:
                    raw_chunks.append((current_text, current_pages))
                    current_text = ""
                    current_pages =[]

                sub_chunks = self._smart_split(page_text, self.max_tokens)
                for sub in sub_chunks:
                    raw_chunks.append((sub, [page]))
                continue

            combined = (current_text + "\n\n" + page_text) if current_text else page_text
            if self.estimate_tokens(combined) > self.max_tokens:
                if current_text:
                    raw_chunks.append((current_text, current_pages))
                current_text = page_text
                current_pages =[page]
            else:
                current_text = combined
                current_pages.append(page)

        if current_text:
            raw_chunks.append((current_text, current_pages))

        return self._apply_overlap_and_finalize(raw_chunks)

    # ─────────────────────────────────────────
    # Large parts cho Gemini flow
    # ─────────────────────────────────────────
    def create_large_parts(
        self,
        parsed_pages: List[Dict[str, Any]],
        # FIX: Ép Gemini đọc kỹ hơn bằng cách giảm số trang mỗi phần
        pages_per_part: int = 10,  # Cũ: 150. Slide 25 trang sẽ chia làm 3 phần thay vì 1 phần.
    ) -> List[Dict[str, Any]]:
        parts =[]
        i = 0
        part_index = 0

        while i < len(parsed_pages):
            batch = parsed_pages[i : i + pages_per_part]

            cut_point = self._find_natural_cut(batch, pages_per_part)
            # Đảm bảo cut_point tối thiểu là 1 để tránh loop vô hạn
            cut_point = max(1, cut_point)
            batch = parsed_pages[i : i + cut_point]

            content = "\n\n".join(p["content"] for p in batch)
            start_page = batch[0]["page_num"]
            end_page = batch[-1]["page_num"]
            file_name = batch[0]["metadata"].get("file_name", "")

            parts.append({
                "part_index": part_index,
                "content": content,
                "source_ref": f"{file_name} — trang {start_page}-{end_page}",
                "page_count": len(batch),
                "metadata": {
                    "page_range": [start_page, end_page],
                    "file_name": file_name,
                }
            })

            i += cut_point
            part_index += 1

        logger.info("large_parts_created", total_parts=len(parts))
        return parts

    # ─────────────────────────────────────────
    # Smart split — boundary-aware
    # ─────────────────────────────────────────
    def _smart_split(self, text: str, max_tokens: int) -> List[str]:
        parts = self._split_by_pattern(text, _HEADING_RE, max_tokens)
        if parts: return parts

        parts = self._split_by_pattern(text, _SLIDE_RE, max_tokens)
        if parts: return parts

        paragraphs = re.split(r"\n\n+", text)
        parts = self._merge_until_max(paragraphs, max_tokens)
        if parts: return parts

        sentences = re.split(r"(?<=[.!?])\s+", text)
        parts = self._merge_until_max(sentences, max_tokens)
        if parts: return parts

        logger.warning("fallback_char_split", text_length=len(text))
        chars_per_chunk = max_tokens * 3  # Đổi hệ số khớp với estimate_tokens
        return [text[i : i + chars_per_chunk] for i in range(0, len(text), chars_per_chunk)]

    def _split_by_pattern(
        self, text: str, pattern: re.Pattern, max_tokens: int
    ) -> List[str]:
        positions =[m.start() for m in pattern.finditer(text)]
        if len(positions) < 2:
            return[]

        segments = []
        prev = 0
        for pos in positions[1:]:
            segments.append(text[prev:pos].strip())
            prev = pos
        segments.append(text[prev:].strip())
        segments = [s for s in segments if s]

        return self._merge_until_max(segments, max_tokens)

    def _merge_until_max(
        self, segments: List[str], max_tokens: int
    ) -> List[str]:
        if not segments: return[]

        result =[]
        current = ""

        for seg in segments:
            candidate = (current + "\n\n" + seg).strip() if current else seg
            if self.estimate_tokens(candidate) <= max_tokens:
                current = candidate
            else:
                if current:
                    result.append(current)
                current = seg

        if current:
            result.append(current)

        return result if result else[]

    # ─────────────────────────────────────────
    # Overlap
    # ─────────────────────────────────────────
    def _apply_overlap_and_finalize(
        self, raw_chunks: List[tuple]
    ) -> List[Dict[str, Any]]:
        final_chunks =[]
        overlap_chars = self.overlap * 3  # Cập nhật theo estimate_tokens (x3)

        for i, (text, pages) in enumerate(raw_chunks):
            if i > 0 and self.overlap > 0:
                prev_text = raw_chunks[i - 1][0]
                # Lấy phần đuôi của chunk trước
                overlap_text = prev_text[-overlap_chars:].strip()

                # Cắt gọn từ đầu câu tiếp theo gần nhất
                sentence_start = re.search(r"(?<=[.!?\n])\s+\S", overlap_text)
                if sentence_start:
                    # Fix lỗi cắt mất chữ cái đầu tiên của câu
                    overlap_text = overlap_text[sentence_start.end()-1:].strip()

                # FIX: Gắn nhãn để LLM phân biệt được đâu là ngữ cảnh nối tiếp, đâu là content chính
                text = f"[Ngữ cảnh nối tiếp: {overlap_text}]\n\n{text}"

            source_ref = self._generate_source_ref(pages)
            file_name = pages[0]["metadata"].get("file_name", "") if pages else ""

            final_chunks.append({
                "chunk_index": i,
                "content": text,
                "source_ref": source_ref,
                "metadata": {
                    "file_name": file_name,
                    "page_range": (
                        [min(p["page_num"] for p in pages), max(p["page_num"] for p in pages)]
                        if pages else [1, 1]
                    ),
                    "sources": list(set(p["metadata"]["source"] for p in pages)),
                },
            })

        logger.info("chunks_created", total=len(final_chunks))
        return final_chunks

    # ─────────────────────────────────────────
    # Source ref & Utility
    # ─────────────────────────────────────────
    def _generate_source_ref(self, pages: List[Dict[str, Any]]) -> str:
        if not pages: return "Unknown"

        if len(pages) == 1 and pages[0]["metadata"].get("source_ref"):
            return pages[0]["metadata"]["source_ref"]

        source_type = pages[0]["metadata"].get("source", "")
        file_name = pages[0]["metadata"].get("file_name", "")
        page_nums = sorted(set(p["page_num"] for p in pages))

        label = "Trang" if source_type == "pdf" else "Slide" if source_type == "pptx" else "Phần"
        page_str = f"{label} {page_nums[0]}" if len(page_nums) == 1 else f"{label} {page_nums[0]}-{page_nums[-1]}"

        return f"{file_name} — {page_str}" if file_name else page_str

    def _find_natural_cut(
        self, pages: List[Dict[str, Any]], target: int
    ) -> int:
        if len(pages) <= target:
            return len(pages)

        search_from = int(target * 0.7)
        for j in range(target - 1, search_from, -1):
            content = pages[j]["content"]
            if _HEADING_RE.search(content) or _SLIDE_RE.search(content):
                return j + 1

        return target