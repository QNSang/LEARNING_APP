import asyncio
import json
import re
from typing import List, Dict, Any
from .gemini_client import GeminiClient
from .groq_client import GroqClient
import structlog

logger = structlog.get_logger()

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
GROQ_BATCH_SIZE       = 5
GROQ_MAX_CONCURRENT   = 2
GEMINI_MAX_CONCURRENT = 3
MAX_NODES_PER_DOC     = 300
RETRY_DELAYS          = [2, 4, 8, 16]
BATCH_SEPARATOR       = "\n\n════ BATCH {idx} ════\n"


class ExtractorService:
    def __init__(self, groq_client: GroqClient, gemini_client: GeminiClient):
        self.groq             = groq_client
        self.gemini           = gemini_client
        self.groq_semaphore   = asyncio.Semaphore(GROQ_MAX_CONCURRENT)
        self.gemini_semaphore = asyncio.Semaphore(GEMINI_MAX_CONCURRENT)

    # ─────────────────────────────────────────
    # Groq Pipeline (< 75k tokens)
    # ─────────────────────────────────────────
    async def run_groq_pipeline(
        self, chunks: List[Dict[str, Any]], subject_name: str
    ) -> Dict[str, Any]:
        logger.info("groq_pipeline_start", chunks=len(chunks))

        batches = [
            chunks[i : i + GROQ_BATCH_SIZE]
            for i in range(0, len(chunks), GROQ_BATCH_SIZE)
        ]
        tasks = [
            self._summarize_batch(batch, subject_name, idx, len(batches))
            for idx, batch in enumerate(batches)
        ]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        summaries = []
        for idx, res in enumerate(raw_results):
            if isinstance(res, Exception):
                logger.error("batch_failed", batch=idx, error=str(res))
                summaries.append(f"[BATCH {idx} FAILED]")
            else:
                summaries.append(res)

        concatenated = "".join(
            BATCH_SEPARATOR.format(idx=i) + s
            for i, s in enumerate(summaries)
        )

        logger.info("groq_pass2_start", batches=len(summaries))
        return await self._pass_2_groq(concatenated, subject_name, len(summaries))

    # ─────────────────────────────────────────
    # Gemini Pipeline (>= 75k tokens)
    # ─────────────────────────────────────────
    async def run_gemini_large_pipeline(
        self, parts: List[Dict[str, Any]], subject_name: str
    ) -> Dict[str, Any]:
        logger.info("gemini_pipeline_start", parts=len(parts))

        tasks = [
            self._extract_part_gemini(part, subject_name, idx, len(parts))
            for idx, part in enumerate(parts)
        ]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        all_nodes, all_edges, failed_parts = [], [], []
        for idx, res in enumerate(raw_results):
            if isinstance(res, Exception):
                logger.error("part_failed", part=idx, error=str(res))
                failed_parts.append(idx)
            else:
                all_nodes.extend(res.get("nodes", []))
                all_edges.extend(res.get("edges", []))

        if failed_parts:
            logger.warning("parts_failed", failed=failed_parts)

        if len(parts) > 1:
            logger.info("gemini_merge_start", raw_nodes=len(all_nodes))
            return await self._merge_parts_gemini(all_nodes, all_edges, subject_name)

        return {"nodes": all_nodes, "edges": all_edges}

    # ─────────────────────────────────────────
    # Pass 1 — Summarize batch (Groq)
    # ─────────────────────────────────────────
    async def _summarize_batch(
        self,
        batch: List[Dict[str, Any]],
        subject_name: str,
        batch_idx: int,
        total_batches: int,
    ) -> str:
        async with self.groq_semaphore:
            logger.info("summarizing_batch", current=batch_idx + 1, total=total_batches)
            chunks_text = "\n".join(
                f"--- [{chunk.get('source_ref', f'chunk {i}')}] ---\n{chunk['content']}"
                for i, chunk in enumerate(batch)
            )
            prompt = self._build_pass1_prompt(
                subject_name, chunks_text, batch_idx, total_batches
            )
            result = await self._call_with_retry(
                client=self.groq,
                prompt=prompt,
                is_json=True,
                label=f"pass1_batch_{batch_idx}",
            )
            await asyncio.sleep(1.5)
            return result

    # ─────────────────────────────────────────
    # Pass 2 — Build graph (Groq)
    # ─────────────────────────────────────────
    async def _pass_2_groq(
        self,
        concatenated: str,
        subject_name: str,
        total_batches: int,
    ) -> Dict[str, Any]:
        estimated = len(concatenated) // 2
        if estimated > 100_000:
            logger.warning("pass2_truncating", estimated_tokens=estimated)
            concatenated = concatenated[: 200_000]

        prompt  = self._build_pass2_prompt(subject_name, total_batches, concatenated)
        raw     = await self._call_with_retry(
            client=self.groq, prompt=prompt, is_json=True, label="pass2_graph"
        )
        result  = self._safe_parse_json(raw, label="pass2")

        # Tính stats bằng Python, không để LLM đếm
        nodes   = result.get("nodes", [])
        edges   = result.get("edges", [])
        logger.info(
            "graph_stats",
            total_nodes   = len(nodes),
            total_edges   = len(edges),
            by_type       = _count_field(nodes, "node_type"),
            by_importance = _count_field(nodes, "importance"),
            by_edge_type  = _count_field(edges, "type"),
        )
        return result

    # ─────────────────────────────────────────
    # Extract part (Gemini)
    # ─────────────────────────────────────────
    async def _extract_part_gemini(
        self,
        part: Dict[str, Any],
        subject_name: str,
        part_idx: int,
        total_parts: int,
    ) -> Dict[str, Any]:
        async with self.gemini_semaphore:
            logger.info("extracting_part", current=part_idx + 1, total=total_parts)
            prompt = self._build_gemini_part_prompt(subject_name, part)
            raw    = await self._call_with_retry(
                client=self.gemini, prompt=prompt, is_json=True,
                label=f"gemini_part_{part_idx}",
            )
            data = self._safe_parse_json(raw, label=f"gemini_part_{part_idx}")
            for node in data.get("nodes", []):
                node.setdefault("source_ref",  part["source_ref"])
                node.setdefault("chunk_index", part["part_index"])
            return data

    # ─────────────────────────────────────────
    # Merge parts (Gemini flow)
    # ─────────────────────────────────────────
    async def _merge_parts_gemini(
        self,
        all_nodes: List[Dict],
        all_edges: List[Dict],
        subject_name: str,
    ) -> Dict[str, Any]:
        deduped = self._prefilter_nodes(all_nodes)
        logger.info("merge_prefilter", before=len(all_nodes), after=len(deduped))
        prompt  = self._build_gemini_merge_prompt(subject_name, deduped, all_edges)
        raw     = await self._call_with_retry(
            client=self.gemini, prompt=prompt, is_json=True, label="gemini_merge"
        )
        return self._safe_parse_json(raw, label="merge")

    def _prefilter_nodes(self, nodes: List[Dict]) -> List[Dict]:
        """
        Dedup bằng English term (ổn định hơn label tiếng Việt).
        Fallback: id → label. Chỉ gộp khi exact match sau normalize.
        Không gộp theo ngữ nghĩa — để LLM merge xử lý phần đó.
        """
        seen: Dict[str, Dict] = {}
        for node in nodes:
            raw = (
                node.get("term")
                or node.get("id")
                or node.get("label", "")
            )
            key = re.sub(r"\s+", " ", raw.lower().strip())
            if not key:
                continue
            if key not in seen:
                seen[key] = node
            else:
                existing = seen[key]
                # Ưu tiên giữ importance cao hơn khi có conflict
                importance_rank = {"core": 3, "supporting": 2, "detail": 1}
                if importance_rank.get(node.get("importance", ""), 0) > \
                   importance_rank.get(existing.get("importance", ""), 0):
                    existing["importance"] = node["importance"]
                # Merge source_ref nếu node gốc chưa có
                if node.get("source_ref") and not existing.get("source_ref"):
                    existing["source_ref"] = node["source_ref"]
        return list(seen.values())

    # ─────────────────────────────────────────
    # Retry
    # ─────────────────────────────────────────
    async def _call_with_retry(
        self, client, prompt: str, is_json: bool, label: str
    ) -> str:
        last_error = None
        for attempt, delay in enumerate(RETRY_DELAYS):
            try:
                return await client.generate_content(prompt, is_json=is_json)
            except Exception as e:
                last_error  = e
                is_rate     = any(
                    kw in str(e).lower()
                    for kw in ["429", "rate limit", "quota", "too many", "resource exhausted"]
                )
                if is_rate and attempt < len(RETRY_DELAYS) - 1:
                    logger.warning("rate_limit_retry", label=label, attempt=attempt + 1, wait=delay)
                    await asyncio.sleep(delay)
                else:
                    logger.error("call_failed", label=label, error=str(e))
                    raise
        raise last_error

    # ─────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────
    def _safe_parse_json(self, raw: str, label: str = "") -> Dict[str, Any]:
        try:
            cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error("json_parse_failed", label=label, error=str(e), preview=raw[:200])
            return {"nodes": [], "edges": []}

    # ═════════════════════════════════════════
    # PROMPTS
    # ═════════════════════════════════════════

    def _build_pass1_prompt(
        self,
        subject_name: str,
        chunks_text: str,
        batch_index: int,
        total_batches: int,
    ) -> str:
        return f"""SYSTEM:
Chuyên gia nhận thức học. Trích xuất đơn vị kiến thức và quan hệ từ văn bản.
JSON only. Không thêm text.

NODE TYPE — cơ chế học cần thiết:
concept   = hiểu sâu, giải thích bằng analogy. VD: Backpropagation, Overfitting.
fact      = ghi nhớ/tra cứu, đúng/sai không cần suy luận. VD: Adam lr=0.001.
procedure = luyện tập bước đến tự động hóa. VD: Fine-tuning, viết SQL JOIN.

IMPORTANCE — chỉ dẫn (không ép tỉ lệ):
core       = không có → không hiểu chủ đề. Thường ≤ 30%, nhưng ưu tiên đúng hơn đủ tỉ lệ.
supporting = làm rõ core.
detail     = ví dụ, số liệu, edge case.

EDGE TYPE — chọn theo thứ tự ưu tiên:
requires   = "chưa biết target thì không học được term này." Không tạo cycle.
             ĐÚNG: gradient_descent requires calculus_derivative
             SAI:  neural_network requires activation_function (→ part_of)
             SAI:  deep_learning requires machine_learning (→ related_to)
             SAI:  relu requires activation_function (→ explains)

part_of    = "term là thành phần bên trong target."
             ĐÚNG: activation_function part_of neural_network
             SAI:  deep_learning part_of machine_learning (→ requires/related_to)

explains   = "term cụ thể hóa target trừu tượng." Chiều: cụ thể → trừu tượng.
             ĐÚNG: relu_function explains activation_function
             SAI:  activation_function explains relu_function (→ ngược chiều)

related_to = liên hệ ngang. Dùng khi không thể dùng 3 loại trên. 1 chiều.

RULE: Trích xuất TẤT CẢ term kỹ thuật trong đoạn. Không bịa term không có trong văn bản.

USER:
Môn: {subject_name} | Batch {batch_index + 1}/{total_batches}

{chunks_text}

Trả về JSON array:
[
  {{
    "term": "English term (giữ nguyên nếu là thuật ngữ quốc tế)",
    "label_vi": "Tên tiếng Việt ngắn",
    "definition": "Tối đa 3 câu. Không lặp từ trong term.",
    "node_type": "concept|fact|procedure",
    "importance": "core|supporting|detail",
    "relations": [
      {{
        "target_term": "term liên quan",
        "edge_type": "requires|part_of|explains|related_to",
        "reason": "một câu giải thích ngắn"
      }}
    ]
  }}
]"""

    def _build_pass2_prompt(
        self, subject_name: str, total_batches: int, summaries: str
    ) -> str:
        return f"""SYSTEM:
AI xây dựng Educational Knowledge Graph. Tổng hợp {total_batches} batch thành graph hoàn chỉnh.
JSON only. Không thêm text.

BƯỚC 1 — DEDUP & RECONCILE:
Gộp term cùng nghĩa → 1 node. "AI"="Artificial Intelligence"="Trí tuệ nhân tạo" → giữ English.
Merge tất cả relations của node bị gộp vào node được giữ.
Conflict node_type → chọn phù hợp định nghĩa hơn.
Conflict importance → chọn cao hơn (core > supporting > detail).

BƯỚC 2 — BUILD NODES & EDGES:
Node id: snake_case. "Gradient Descent" → gradient_descent. Unique.
Importance ≤ 30% core (chỉ dẫn — ưu tiên đúng hơn đủ tỉ lệ).

Kiểm tra edge trước khi thêm:
requires   → "Xóa target, source còn học được không?" Không → đúng. Có → related_to.
             Cycle (A→B và B→A) → giữ edge quan trọng hơn, đổi còn lại thành related_to.
part_of    → "Source là thành phần bên trong target?"
             SAI: deep_learning part_of machine_learning.
explains   → Chiều bắt buộc: source cụ thể hơn target. Sai chiều → đảo hoặc related_to.
related_to → 1 chiều. Dùng khi không thể dùng 3 loại trên.

Orphan node (không có edge): KHÔNG xóa. Giữ lại để validator xử lý.

BƯỚC 3 — VALIDATE:
[ ] Không có cycle trong requires
[ ] Không có self-loop (from == to)
[ ] Không có duplicate edge (from, to, type trùng nhau)
[ ] Tất cả node trong edges tồn tại trong nodes[]
[ ] explains: source cụ thể hơn target

USER:
Môn: {subject_name} | {total_batches} batches

════════════ PASS 1 OUTPUT ════════════
{summaries}
═══════════════════════════════════════

Trả về JSON:
{{
  "subject": "{subject_name}",
  "nodes": [
    {{
      "id": "snake_case_id",
      "term": "English term",
      "label": "Tiếng Việt (English)",
      "definition": "Tối đa 3 câu.",
      "node_type": "concept|fact|procedure",
      "importance": "core|supporting|detail",
      "chunk_index": 0,
      "source_ref": ""
    }}
  ],
  "edges": [
    {{
      "from": "node_id_nguon",
      "to": "node_id_dich",
      "type": "requires|part_of|explains|related_to",
      "reason": "một câu giải thích ngắn"
    }}
  ]
}}"""

    def _build_gemini_part_prompt(
        self, subject_name: str, part: Dict[str, Any]
    ) -> str:
        return f"""SYSTEM:
AI xây dựng Educational Knowledge Graph. Trích xuất từ phần tài liệu.
JSON only. Không markdown.

NODE TYPE:
concept   = hiểu sâu, analogy. VD: Backpropagation, Attention Mechanism.
fact      = ghi nhớ/tra cứu. VD: Adam lr=0.001, cú pháp list comprehension.
procedure = luyện bước đến tự động. VD: Fine-tuning, cài CUDA, viết SQL JOIN.

IMPORTANCE (chỉ dẫn, ưu tiên đúng hơn đủ tỉ lệ):
core ≤ 30% | supporting ≈ 40% | detail ≈ 30%

EDGE TYPE:
requires   = prerequisite cứng. Không cycle.
             ĐÚNG: gradient_descent requires calculus_derivative
             SAI:  neural_network requires activation_function (→ part_of)
             SAI:  relu requires activation_function (→ explains)
part_of    = source là thành phần bên trong target.
             ĐÚNG: activation_function part_of neural_network
             SAI:  deep_learning part_of machine_learning
explains   = source cụ thể hóa target. Chiều: cụ thể → trừu tượng.
             ĐÚNG: relu_function explains activation_function
related_to = liên hệ ngang. 1 chiều. Dùng sau cùng.

GIỚI HẠN: tối đa 80 nodes, 120 edges. Ưu tiên core > supporting > detail khi cắt.
Orphan node: KHÔNG xóa.

QUY TRÌNH: SCAN → DEDUP → CLASSIFY → EDGES → VALIDATE
VALIDATE:
[ ] nodes ≤ 80, edges ≤ 120
[ ] Không cycle trong requires
[ ] Không self-loop
[ ] explains: source cụ thể hơn target

USER:
Môn: {subject_name} | Nguồn: {part['source_ref']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{part['content']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Trả về JSON:
{{
  "subject": "{subject_name}",
  "source_ref": "{part['source_ref']}",
  "nodes": [
    {{
      "id": "snake_case_id",
      "term": "English term",
      "label": "Tiếng Việt (English)",
      "definition": "Tối đa 3 câu.",
      "node_type": "concept|fact|procedure",
      "importance": "core|supporting|detail",
      "chunk_index": {part['part_index']},
      "source_ref": "{part['source_ref']}"
    }}
  ],
  "edges": [
    {{
      "from": "node_id_nguon",
      "to": "node_id_dich",
      "type": "requires|part_of|explains|related_to",
      "reason": "một câu giải thích ngắn"
    }}
  ]
}}"""

    def _build_gemini_merge_prompt(
        self,
        subject_name: str,
        nodes: List[Dict],
        edges: List[Dict],
    ) -> str:
        return f"""SYSTEM:
AI hợp nhất Educational Knowledge Graph từ nhiều nguồn.
JSON only. Không markdown.

NGUYÊN TẮC DEDUP — ĐỌC KỸ TRƯỚC KHI GỘP:
CHỈ gộp 2 nodes khi chúng là CÙNG 1 khái niệm, chỉ khác cách viết:
  ĐƯỢC gộp: "ML" = "Machine Learning" = "Học máy" → cùng 1 khái niệm
  ĐƯỢC gộp: "Back Propagation" = "Backpropagation" → viết khác nhau
  KHÔNG gộp: MCAR, MAR, MNAR → 3 loại riêng biệt dù cùng thuộc "missing data"
  KHÔNG gộp: "Hồi quy tuyến tính" và "Hồi quy logistic" → 2 thuật toán khác nhau
  KHÔNG gộp: các node là instances/trường hợp cụ thể của cùng 1 khái niệm cha
  KHÔNG gộp: node có id khác nhau và đều có edges riêng

RULE: Khi nghi ngờ có nên gộp không → KHÔNG GỘP. Giữ nguyên 2 nodes.

QUY TRÌNH:

1. DEDUP NODES — chỉ gộp khi chắc chắn cùng khái niệm:
   Ưu tiên English term. Merge TẤT CẢ edges của node bị gộp vào node được giữ.
   Giữ chunk_index và source_ref của lần xuất hiện đầu tiên.
   Conflict importance → giữ importance cao hơn (core > supporting > detail).

2. RECONCILE EDGES — sau khi gộp nodes:
   Cập nhật from/to theo id mới.
   Xóa self-loop (from == to).
   Xóa duplicate (from, to, type trùng nhau).
   Cycle trong requires → giữ edge quan trọng hơn, đổi còn lại thành related_to.

3. TRIM — giới hạn {MAX_NODES_PER_DOC} nodes:
   Ưu tiên: core > supporting > detail.
   Xóa node detail → xóa cả edges liên quan.
   Không xóa node nếu có requires edge từ node được giữ trỏ vào nó.

4. VALIDATE:
   [ ] Không cycle trong requires
   [ ] Không self-loop
   [ ] Không duplicate edge
   [ ] Tất cả node trong edges tồn tại trong nodes[]

USER:
Môn: {subject_name}

Nodes ({len(nodes)}):
{json.dumps(nodes, ensure_ascii=False, indent=2)}

Edges ({len(edges)}):
{json.dumps(edges, ensure_ascii=False, indent=2)}

Trả về JSON:
{{
  "subject": "{subject_name}",
  "nodes": [
    {{
      "id": "snake_case_id",
      "term": "English term",
      "label": "Tiếng Việt (English)",
      "definition": "Tối đa 3 câu.",
      "node_type": "concept|fact|procedure",
      "importance": "core|supporting|detail",
      "chunk_index": 0,
      "source_ref": ""
    }}
  ],
  "edges": [
    {{
      "from": "node_id_nguon",
      "to": "node_id_dich",
      "type": "requires|part_of|explains|related_to",
      "reason": "một câu giải thích ngắn"
    }}
  ]
}}"""


# ─────────────────────────────────────────────
# Utility
# ─────────────────────────────────────────────
def _count_field(items: List[Dict], field: str) -> Dict[str, int]:
    result: Dict[str, int] = {}
    for item in items:
        v = item.get(field, "unknown")
        result[v] = result.get(v, 0) + 1
    return result