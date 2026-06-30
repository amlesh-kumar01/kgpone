"""
Hybrid Retrieval Service with parallel execution and Reciprocal Rank Fusion.

Executes Qdrant vector search and Neo4j graph traversal concurrently via
asyncio.gather(), then merges results using RRF for a unified ranking.
"""

import asyncio
import logging
from typing import Any, List, Dict

from src.services.rag.base import BaseRetriever
from src.services.ingestion.embedding.base import BaseEmbedder
from src.utils.interfaces import IVectorRepo
from src.repositories.neo4j.graph_repository import Neo4jRepo
from src.schemas.query_schema import QueryPlan
from src.services.rag.fusion import reciprocal_rank_fusion

logger = logging.getLogger("retrieval_service")


class RetrievalService(BaseRetriever):
    def __init__(
        self,
        embedder: BaseEmbedder,
        vector_store: IVectorRepo,
        db=None,
        collection_name: str = "documents",
    ):
        self.embedder = embedder
        self.vector_store = vector_store
        self.db = db
        self.collection_name = collection_name
        self.graph_repo = Neo4jRepo()

    async def retrieve_context(self, query: str, plan: QueryPlan) -> dict[str, Any]:
        """
        Coordinates hybrid vector + graph retrieval based on QueryPlan.
        Uses asyncio.gather() for parallel execution and RRF for fusion.
        """
        logger.info(f"Retrieving context for intent: '{plan.intent}' with backends: {plan.backends_needed}")

        # Build retrieval tasks for parallel execution
        tasks = []
        task_labels = []

        if "qdrant" in plan.backends_needed:
            tasks.append(self._retrieve_vector(query, plan))
            task_labels.append("qdrant")

        if "neo4j" in plan.backends_needed:
            tasks.append(self._retrieve_graph(plan))
            task_labels.append("neo4j")

        if "postgresql" in plan.backends_needed:
            tasks.append(self._retrieve_postgres(plan))
            task_labels.append("postgresql")

        # Execute all retrievals in parallel
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            results = []

        # Collect successful results for RRF
        result_lists = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Retrieval from {task_labels[i]} failed: {result}")
                continue
            if result:
                result_lists.append(result)

        # Merge via Reciprocal Rank Fusion
        if len(result_lists) > 1:
            merged_chunks = reciprocal_rank_fusion(result_lists)
        elif len(result_lists) == 1:
            merged_chunks = result_lists[0]
        else:
            merged_chunks = []

        return {
            "query": query,
            "course_code": plan.course_code,
            "retrieved_chunks": merged_chunks,
            "graph_visualization": {"nodes": [], "edges": []},
            "has_missing_prerequisites": plan.intent == "prerequisites",
        }

    async def _retrieve_vector(self, query: str, plan: QueryPlan) -> List[Dict[str, Any]]:
        """Qdrant vector search — fetches top 30 chunks with metadata pre-filtering."""
        chunks = []
        try:
            query_vectors = await self.embedder.embed([query])
            if not query_vectors:
                return chunks

            query_vector = query_vectors[0]
            filters = {}
            if plan.course_code:
                filters["course_code"] = plan.course_code
            if getattr(plan, "course_offering_id", None):
                filters["course_offering_id"] = plan.course_offering_id

            # Fetch top 30 candidates (up from 10) to feed the cross-encoder
            search_results = await asyncio.to_thread(
                self.vector_store.search,
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=30,
                filters=filters if filters else None,
            )

            for r in search_results:
                chunks.append({
                    "id": r.id,
                    "score": r.score,
                    "payload": r.payload or {},
                })
        except Exception as e:
            logger.error(f"Vector retrieval failed: {e}")

        return chunks

    async def _retrieve_graph(self, plan: QueryPlan) -> List[Dict[str, Any]]:
        """Neo4j graph traversal — wrapped in asyncio.to_thread for async compat."""
        if self.graph_repo.use_fallback:
            return []

        chunks = []
        try:
            if plan.intent == "prerequisites" and plan.course_code:
                chunks.extend(await self._graph_prerequisites(plan.course_code))

            elif plan.intent in ["topic_explain", "compare", "relationship", "concept_search"]:
                for entity in plan.entities_mentioned:
                    chunks.extend(await self._graph_entity_search(entity))
        except Exception as e:
            logger.error(f"Graph retrieval failed: {e}")

        return chunks

    async def _graph_prerequisites(self, course_code: str) -> List[Dict[str, Any]]:
        """Fetches prerequisite chain from Neo4j."""
        cypher = """
        MATCH (c:Course {code: $code})-[:PREREQUISITE*]->(prereq:Course)
        MATCH (prereq)-[:HAS_OFFERING]->(o)-[:HAS_DOCUMENT]->(d)-[:COVERS|:MENTIONS]->(concept)
        RETURN prereq.code as course, concept.name as concept, concept.description as desc
        LIMIT 5
        """
        results = await asyncio.to_thread(
            self.graph_repo.execute_read_query, cypher, {"code": course_code}
        )

        chunks = []
        for r in results:
            chunks.append({
                "id": f"graph_prereq_{r['course']}_{r['concept']}",
                "score": 0.8,
                "payload": {
                    "text": f"Prerequisite Concept ({r['course']}): {r['concept']} - {r.get('desc', '')}",
                    "document_id": "GRAPH",
                    "course_code": r["course"],
                    "is_prerequisite": True,
                    "prerequisite_concept": r["concept"],
                },
            })
        return chunks

    async def _graph_entity_search(self, entity: str) -> List[Dict[str, Any]]:
        """Searches for related entities in the knowledge graph."""
        cypher = """
        MATCH (n) WHERE toLower(n.name) CONTAINS toLower($entity)
        MATCH (n)-[r]-(related)
        RETURN n.name as source, type(r) as relation, labels(related)[0] as target_label, related.name as target, related.description as desc
        LIMIT 10
        """
        results = await asyncio.to_thread(
            self.graph_repo.execute_read_query, cypher, {"entity": entity}
        )

        chunks = []
        for r in results:
            text_fact = f"Graph Fact: {r['source']} {r['relation']} {r['target_label']} ({r['target']}). {r.get('desc', '')}"
            chunks.append({
                "id": f"graph_fact_{r['source']}_{r['target']}",
                "score": 0.7,
                "payload": {
                    "text": text_fact,
                    "document_id": "GRAPH",
                },
            })
        return chunks

    async def _retrieve_postgres(self, plan: QueryPlan) -> List[Dict[str, Any]]:
        """PostgreSQL document listing for download/list_documents intents."""
        if not self.db:
            return []

        chunks = []
        try:
            if plan.intent in ["list_documents", "download"]:
                from src.repositories.postgres.document_repository import DocumentRepository
                doc_repo = DocumentRepository(self.db)

                if getattr(plan, "course_offering_id", None):
                    docs = await asyncio.to_thread(
                        doc_repo.get_documents_by_offering, plan.course_offering_id
                    )
                    for doc in docs:
                        if doc.status == "COMPLETED":
                            chunks.append({
                                "id": f"pg_doc_{doc.id}",
                                "score": 1.0,
                                "payload": {
                                    "text": f"Document available: {doc.title} (Type: {doc.doc_type}, Description: {doc.description or 'N/A'})",
                                    "document_id": str(doc.id),
                                    "title": doc.title,
                                    "course_code": plan.course_code or "Unknown",
                                    "document_type": doc.doc_type,
                                    "s3_key": doc.s3_key,
                                },
                            })
        except Exception as e:
            logger.error(f"PostgreSQL retrieval failed: {e}")

        return chunks
