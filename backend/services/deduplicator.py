import re
import structlog
from typing import List, Dict, Any, Optional, Tuple, Set
import difflib

logger = structlog.get_logger()

# ÉP CHẾ ĐỘ SIÊU NHẸ: Không dùng ML để tiết kiệm RAM và CPU
HAS_ML = False

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
MULTILINGUAL_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# Nâng ngưỡng Semantic lên 0.95 (Chỉ gộp khi gần như là 1)
SEMANTIC_THRESHOLD = 0.95
STRING_THRESHOLD   = 0.92

class DeduplicatorService:
    def __init__(
        self,
        model_name: str = MULTILINGUAL_MODEL,
        threshold: float = SEMANTIC_THRESHOLD,
    ):
        self.model_name   = model_name
        self.threshold    = threshold
        self._model: Optional[Any] = None
        self.use_fallback = not HAS_ML

    @property
    def model(self):
        return None

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[-_/]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text

    @staticmethod
    def _dedup_key(node: Dict[str, Any]) -> str:
        raw = node.get("term") or node.get("id") or node.get("label", "")
        raw = re.sub(r"\(.*?\)", "", raw).strip()
        return DeduplicatorService._normalize(raw)

    # ─────────────────────────────────────────
    # KIỂM TRA ĐIỀU KIỆN GỘP AN TOÀN (SAFE MERGE)
    # ─────────────────────────────────────────
    def _is_safe_to_merge(self, node_a: Dict, node_b: Dict) -> bool:
        """Kiểm tra 2 node có ĐƯỢC PHÉP gộp bằng thuật toán nội suy không"""
        # 1. Khác loại (concept vs procedure) -> TUYỆT ĐỐI KHÔNG GỘP
        if node_a.get("node_type") != node_b.get("node_type"):
            return False
            
        term_a = (node_a.get("term") or "").strip()
        term_b = (node_b.get("term") or "").strip()
        
        # 2. ACRONYM PROTECTOR: Nếu 1 trong 2 là từ viết tắt ngắn (<= 5 ký tự)
        # VD: "MCAR", "PMM", "CCA". Các model rất dễ nhầm lẫn các từ này.
        # Chặn gộp nội suy, chỉ cho phép gộp bằng Exact Match ở Bước 1.
        if len(term_a) <= 5 or len(term_b) <= 5:
            return False
            
        return True

    def _merge_node_attributes(self, kept_node: Dict, removed_node: Dict):
        """Khi gộp, bảo tồn các thuộc tính quan trọng nhất của cả 2 node"""
        # 1. Nâng cấp importance (detail < supporting < core)
        rank = {"core": 3, "supporting": 2, "detail": 1}
        if rank.get(removed_node.get("importance", ""), 0) > rank.get(kept_node.get("importance", ""), 0):
            kept_node["importance"] = removed_node["importance"]
            
        # 2. Giữ definition dài hơn và chi tiết hơn
        def_kept = kept_node.get("definition", "")
        def_rem = removed_node.get("definition", "")
        if len(def_rem) > len(def_kept) + 20: # Nếu dài hơn hẳn 20 ký tự thì lấy
            kept_node["definition"] = def_rem

    # ─────────────────────────────────────────
    # Main Logic
    # ─────────────────────────────────────────
    def dedup_nodes(
        self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if not nodes:
            return {"nodes": nodes, "edges": edges}

        # Sort theo chunk_index ưu tiên node xuất hiện sớm
        sorted_nodes = sorted(nodes, key=lambda x: x.get("chunk_index", 0))

        # Bước 1: Exact match (An toàn tuyệt đối)
        sorted_nodes, node_id_map = self._exact_dedup(sorted_nodes)

        # Bước 2: Semantic similarity (Đã gắn khiên bảo vệ)
        merged_nodes, semantic_map = self._semantic_dedup(sorted_nodes)
        node_id_map.update(semantic_map)

        # Bước 3: Remap + clean edges
        clean_edges = self._remap_edges(edges, node_id_map)

        return {"nodes": merged_nodes, "edges": clean_edges}

    def _exact_dedup(
        self, nodes: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        seen: Dict[str, Dict] = {}
        id_map: Dict[str, str] = {}

        for node in nodes:
            key = self._dedup_key(node)
            if key in seen:
                kept = seen[key]
                id_map[node["id"]] = kept["id"]
                self._merge_node_attributes(kept, node)
            else:
                seen[key] = node
                id_map[node["id"]] = node["id"]

        return list(seen.values()), id_map

    def _semantic_dedup(
        self, nodes: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
        if len(nodes) <= 1:
            return nodes, {}

        id_map: Dict[str, str] = {}

        if not self.use_fallback and self.model:
            try:
                texts =[node.get("term") or node.get("label", "") for node in nodes]
                embeddings = self.model.encode(texts, batch_size=64, show_progress_bar=False)
                
                norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
                normalized = embeddings / (norms + 1e-10)
                sim_matrix = np.dot(normalized, normalized.T)
                
                n = len(nodes)
                merged = [False] * n

                for i in range(n):
                    if merged[i]: continue
                    for j in range(i + 1, n):
                        if merged[j]: continue
                        
                        if sim_matrix[i][j] >= self.threshold:
                            # ÁP DỤNG LUẬT BẢO VỆ TRƯỚC KHI GỘP
                            if self._is_safe_to_merge(nodes[i], nodes[j]):
                                id_map[nodes[j]["id"]] = nodes[i]["id"]
                                merged[j] = True
                                self._merge_node_attributes(nodes[i], nodes[j])

                final = [node for idx, node in enumerate(nodes) if not merged[idx]]
                return final, id_map
            except Exception as e:
                logger.error("semantic_encode_failed", error=str(e))

        return self._string_similarity_dedup(nodes, id_map)

    def _string_similarity_dedup(
        self, nodes: List[Dict], id_map: Dict[str, str]
    ) -> Tuple[List[Dict], Dict[str, str]]:
        merged: List[Dict] =[]
        for current in nodes:
            found = False
            current_key = self._dedup_key(current)
            for target in merged:
                # ÁP DỤNG LUẬT BẢO VỆ
                if not self._is_safe_to_merge(target, current):
                    continue
                    
                ratio = difflib.SequenceMatcher(None, current_key, self._dedup_key(target)).ratio()
                if ratio >= STRING_THRESHOLD:
                    id_map[current["id"]] = target["id"]
                    self._merge_node_attributes(target, current)
                    found = True
                    break
            if not found:
                merged.append(current)
                id_map[current["id"]] = current["id"]
        return merged, id_map

    def _remap_edges(
        self, edges: List[Dict], id_map: Dict[str, str]
    ) -> List[Dict]:
        seen_exact: Set[Tuple[str, str, str]] = set()
        seen_bidir: Set[Tuple[frozenset, str]] = set()
        clean: List[Dict] =[]

        for edge in edges:
            from_id  = id_map.get(edge["from"], edge["from"])
            to_id    = id_map.get(edge["to"],   edge["to"])
            etype    = edge.get("type", "related_to")

            if from_id == to_id: continue

            exact_key = (from_id, to_id, etype)
            if exact_key in seen_exact: continue

            bidir_key = (frozenset([from_id, to_id]), etype)
            if bidir_key in seen_bidir:
                continue

            seen_exact.add(exact_key)
            seen_bidir.add(bidir_key)
            clean.append({
                "from":   from_id,
                "to":     to_id,
                "type":   etype,
                "reason": edge.get("reason", ""),
            })

        return clean