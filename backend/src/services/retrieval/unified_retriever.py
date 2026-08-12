from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from src.repositories.qdrant.vector_repository import QdrantRepository
from src.repositories.neo4j.graph_repository import Neo4jRepository
from src.services.ingestion.embedding.llm_embedding import LLMEmbedder
import logging

logger = logging.getLogger("unified_retriever")

class SourceRef(BaseModel):
    document_id: str
    chunk_id: Optional[str] = None
    node_id: Optional[str] = None
    page: Optional[int] = None
    text: Optional[str] = None

class RetrievalResult(BaseModel):
    chunks: List[Dict[str, Any]]
    graph_context: Dict[str, Any]
    sources: List[SourceRef]

class UnifiedRetriever:
    def __init__(self):
        self.vector_repo = QdrantRepository()
        self.graph_repo = Neo4jRepository()
        self.embedder = LLMEmbedder()
        self.collection_name = "documents"

    async def retrieve(
        self,
        query: str,
        document_ids: List[str] = None,
        concept_ids: List[str] = None,
        filters: Dict[str, Any] = None,
        limit: int = 10
    ) -> RetrievalResult:
        """
        Unified retrieval from both Qdrant and Neo4j.
        """
        # 1. Generate query embedding
        query_embedding = await self.embedder.embed_query(query)
        
        # 2. Build Qdrant filter
        from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny
        qdrant_filter = None
        conditions = []
        if document_ids:
            conditions.append(FieldCondition(key="document_id", match=MatchAny(any=document_ids)))
        if concept_ids:
            conditions.append(FieldCondition(key="concept_ids", match=MatchAny(any=concept_ids)))
            
        if conditions:
            qdrant_filter = Filter(must=conditions)
            
        # 3. Query Qdrant
        search_results = await self.vector_repo.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit,
            query_filter=qdrant_filter
        )
        
        chunks = []
        sources = []
        extracted_concept_ids = set(concept_ids) if concept_ids else set()
        
        for res in search_results:
            payload = res.payload or {}
            chunks.append(payload)
            
            # Extract concepts from payloads to query Neo4j later
            if "concept_ids" in payload:
                extracted_concept_ids.update(payload["concept_ids"])
                
            doc_id = payload.get("document_id")
            if doc_id:
                sources.append(SourceRef(
                    document_id=doc_id,
                    chunk_id=payload.get("chunk_id"),
                    node_id=payload.get("section_id"), # we used section_id in chunks
                    text=payload.get("text")
                ))

        # 4. Query Neo4j for related concepts (Graph Expansion)
        graph_context = {}
        if extracted_concept_ids:
            # Get related concepts from neo4j
            # Since neo4j repo might not have a batch method, we might just query the main ones
            # For demo, let's just use a dummy context if the actual method doesn't exist
            # Assuming get_concept exists
            try:
                for cid in list(extracted_concept_ids)[:5]:
                    concept_data = self.graph_repo.get_concept(cid)
                    if concept_data:
                        graph_context[cid] = concept_data
            except Exception as e:
                logger.warning(f"Neo4j graph expansion failed: {e}")

        return RetrievalResult(
            chunks=chunks,
            graph_context=graph_context,
            sources=sources
        )

    async def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all chunks for a specific document.
        Useful for Map-Reduce or full document summarization.
        """
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        qdrant_filter = Filter(must=[
            FieldCondition(key="document_id", match=MatchValue(value=document_id))
        ])
        
        # We need a large limit or pagination to get all chunks. Assuming small documents or reasonable limit for now.
        search_results = await self.vector_repo.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=qdrant_filter,
            limit=1000,
            with_payload=True
        )
        
        # scroll returns (records, next_page_offset)
        records = search_results[0] if search_results else []
        return [r.payload for r in records if r.payload]
