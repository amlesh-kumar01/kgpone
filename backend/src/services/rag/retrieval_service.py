import logging
from typing import List, Dict, Any
from src.services.ingestion.embedding_service import EmbeddingService
from src.config.qdrant import QdrantRepo
from src.services.graph.prerequisite_service import PrerequisiteService

logger = logging.getLogger("retrieval_service")

class RetrievalService:
    def __init__(self):
        self.embedder = EmbeddingService()
        self.qdrant = QdrantRepo()
        self.prereq_service = PrerequisiteService()
        self.collection_name = "kgpone_course_chunks"

    def retrieve_context(self, query: str, course_code: str) -> Dict[str, Any]:
        """
        Coordinates hybrid vector + graph retrieval:
        1. Embeds query.
        2. Retrieves semantic chunks from active course.
        3. Scans graph database for missing prerequisites (Discrete Math, etc.).
        4. If missing prerequisites exist, retrieves semantic chunks from the prerequisite courses.
        5. Returns aggregated matches and traversal path.
        """
        logger.info(f"Retrieving context for query: '{query}' in course: {course_code}")

        # 1. Embed query
        query_vector = self.embedder.get_embedding(query)

        # 2. Query Qdrant for active course chunks
        active_chunks = self.qdrant.search_chunks(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=5,
            filter_course=course_code
        )

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
                chunks = self.qdrant.search_chunks(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    limit=3,
                    filter_course=prereq_course
                )
                
                # Label these chunks explicitly as prerequisite grounding sources
                for c in chunks:
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
