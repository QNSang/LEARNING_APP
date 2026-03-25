import os
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
import structlog
from models.graph import KnowledgeGraph, KnowledgeNode, KnowledgeEdge

logger = structlog.get_logger()

class SupabaseService:
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        url = url or os.environ.get("SUPABASE_URL")
        key = key or os.environ.get("SUPABASE_SERVICE_KEY")
        
        if not url or not key:
            logger.error("supabase_config_missing")
            raise ValueError("SUPABASE_URL or SUPABASE_SERVICE_KEY not found in environment")
            
        self.client: Client = create_client(url, key)

    async def create_document(self, title: str, subject: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Creates a new document entry and returns the document object.
        """
        data = {
            "title": title,
            "subject": subject,
            "user_id": user_id,
            "status": "processing"
        }
        response = self.client.table("documents").insert(data).execute()
        return response.data[0]

    async def update_document_status(self, doc_id: str, status: str, summaries: Optional[List[str]] = None):
        """
        Updates the processing status and caches summaries.
        """
        data = {"status": status}
        if summaries:
            data["summaries"] = summaries
        
        self.client.table("documents").update(data).eq("id", doc_id).execute()

    async def save_graph(self, doc_id: str, graph: Dict[str, Any]):
        """
        Saves all nodes and edges for a document.
        Input graph is a dict with 'nodes' and 'edges' lists.
        """
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        # Prepare node data
        node_inserts = []
        for node in nodes:
            node_inserts.append({
                "document_id": doc_id,
                "node_id": node.get("id", "unknown_node"),
                "term": node.get("term"),
                "label": node.get("label", node.get("term", "Unnamed node")),
                "definition": node.get("definition"),
                "type": node.get("node_type", node.get("type", "concept")),
                "chunk_index": node.get("chunk_index"),
                "source_ref": node.get("source_ref"),
                "importance": node.get("importance", "supporting")
            })

        # Prepare edge data
        edge_inserts = []
        for edge in edges:
            edge_inserts.append({
                "document_id": doc_id,
                "from_node": edge["from"],
                "to_node": edge["to"],
                "edge_type": edge.get("type", "related_to"),
                "reason": edge.get("reason")
            })

        try:
            # Insert nodes in bulk
            if node_inserts:
                self.client.table("graph_nodes").insert(node_inserts).execute()
            
            # Insert edges in bulk
            if edge_inserts:
                self.client.table("graph_edges").insert(edge_inserts).execute()
                
            logger.info("graph_saved_successfully", doc_id=doc_id, nodes=len(nodes), edges=len(edges))
        except Exception as e:
            logger.error("graph_save_failed", doc_id=doc_id, error=str(e))
            raise e

    async def get_graph(self, doc_id: str) -> Dict[str, Any]:
        """
        Retrieves the full graph for a document.
        """
        nodes_res = self.client.table("graph_nodes").select("*").eq("document_id", doc_id).execute()
        edges_res = self.client.table("graph_edges").select("*").eq("document_id", doc_id).execute()
        
        return {
            "nodes": nodes_res.data,
            "edges": edges_res.data
        }

    async def save_node_embedding(self, node_db_id: str, embedding: List[float]):
        """
        Updates a node with its vector embedding.
        """
        self.client.table("graph_nodes").update({"embedding": embedding}).eq("id", node_db_id).execute()

    async def cache_node_explanation(self, node_db_id: str, explanation: Dict[str, Any]):
        """
        Caches the AI-generated explanation for a node.
        """
        self.client.table("graph_nodes").update({"explanation": explanation}).eq("id", node_db_id).execute()

    async def delete_document(self, doc_id: str):
        """
        Deletes a document. Cascade delete handles nodes and edges.
        """
        self.client.table("documents").delete().eq("id", doc_id).execute()
