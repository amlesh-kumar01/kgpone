import logging
import asyncio
from typing import List, Dict, Any
from src.utils.interfaces import IRetrievalService
from src.services.ingestion.embedding.gemini_embedding import GeminiEmbedder
from src.repositories.qdrant.vector_repository import QdrantRepository
from src.services.graph.prerequisite_service import PrerequisiteService

logger = logging.getLogger("retrieval_service")

class RetrievalService(IRetrievalService):
    def __init__(self):
        self.embedder = GeminiEmbedder()
        self.qdrant = QdrantRepository()
        self.prereq_service = PrerequisiteService()
        self.collection_name = "documents" # Unified collection name matching ingestion pipeline

    async def retrieve_context(self, query: str, course_code: str) -> Dict[str, Any]:
        """
        Coordinates hybrid vector + graph retrieval:
        1. Embeds query asynchronously.
        2. Retrieves semantic chunks from active course.
        3. Scans graph database for missing prerequisites (Discrete Math, etc.).
        4. If missing prerequisites exist, retrieves semantic chunks from the prerequisite courses.
        5. Returns aggregated matches and traversal path.
        """
        logger.info(f"Retrieving context for query: '{query}' in course: {course_code}")

        # 1. Embed query (Gemini embedding returns a list of float vectors)
        query_vectors = await self.embedder.embed([query])
        if not query_vectors:
            logger.warning("Could not generate embedding for query.")
            return {
                "query": query,
                "course_code": course_code,
                "retrieved_chunks": [],
                "graph_visualization": {"nodes": [], "edges": []},
                "has_missing_prerequisites": False
            }
        query_vector = query_vectors[0]

        # 2. Query Qdrant for active course chunks
        active_search_results = self.qdrant.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=5,
            filters={"course_code": course_code}
        )
        
        # Convert Qdrant ScoredPoint objects to standard dictionaries
        active_chunks = []
        for r in active_search_results:
            active_chunks.append({
                "id": r.id,
                "score": r.score,
                "payload": r.payload or {}
            })

        # 3. Graph Diagnostic: Check for missing foundational prerequisite concepts
        prereq_diagnosis = self.prereq_service.diagnose_missing_prerequisites(query, course_code)
        
        prereq_chunks = []
        if prereq_diagnosis["has_missing_prerequisites"]:
            logger.info(f"Found missing prerequisites: {prereq_diagnosis['missing_prerequisites']}")
            
            # Fetch chunks from prerequisite courses matching the prerequisite concepts
            for link in prereq_diagnosis["prerequisite_links"]:
                prereq_course = link["course_code"]
                prereq_concept = link["prereq_concept"]
                
                # Retrieve chunks from Qdrant filtering by prerequisite course code
                prereq_search_results = self.qdrant.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    limit=3,
                    filters={"course_code": prereq_course}
                )
                
                # Convert ScoredPoints and label explicitly as prerequisite grounding sources
                for r in prereq_search_results:
                    c = {
                        "id": r.id,
                        "score": r.score,
                        "payload": r.payload or {}
                    }
                    c["payload"]["is_prerequisite"] = True
                    c["payload"]["prerequisite_for"] = link["source_concept"]
                    c["payload"]["prerequisite_concept"] = prereq_concept
                    prereq_chunks.append(c)

        # Merge active chunks and prerequisite chunks
        all_retrieved = []
        seen_ids = set()
        
        for c in active_chunks:
            if c["id"] not in seen_ids:
                seen_ids.add(c["id"])
                c["payload"]["is_prerequisite"] = False
                all_retrieved.append(c)
                
        for c in prereq_chunks:
            if c["id"] not in seen_ids:
                seen_ids.add(c["id"])
                all_retrieved.append(c)

        return {
            "query": query,
            "course_code": course_code,
            "retrieved_chunks": all_retrieved,
            "graph_visualization": prereq_diagnosis["graph_visualization"],
            "has_missing_prerequisites": prereq_diagnosis["has_missing_prerequisites"]
        }
