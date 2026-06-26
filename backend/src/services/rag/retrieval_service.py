import logging
from typing import Any, List, Dict
from src.services.rag.base import BaseRetriever
from src.services.ingestion.embedding.base import BaseEmbedder
from src.utils.interfaces import IVectorRepo
from src.repositories.neo4j.graph_repository import Neo4jRepo
from src.schemas.query_schema import QueryPlan

logger = logging.getLogger("retrieval_service")

class RetrievalService(BaseRetriever):
    def __init__(
        self,
        embedder: BaseEmbedder,
        vector_store: IVectorRepo,
        collection_name: str = "documents",
    ):
        self.embedder = embedder
        self.vector_store = vector_store
        self.collection_name = collection_name
        self.graph_repo = Neo4jRepo()

    async def retrieve_context(self, query: str, plan: QueryPlan) -> dict[str, Any]:
        """
        Coordinates hybrid vector + graph retrieval based on QueryPlan.
        """
        logger.info(f"Retrieving context for intent: '{plan.intent}' with backends: {plan.backends_needed}")

        all_retrieved_chunks = []
        graph_visualization = {"nodes": [], "edges": []}
        
        # 1. Gather Vector Context if Qdrant is needed
        if "qdrant" in plan.backends_needed:
            # Embed query
            query_vectors = await self.embedder.embed([query])
            if query_vectors:
                query_vector = query_vectors[0]
                filters = {}
                if plan.course_code:
                    filters["course_code"] = plan.course_code
                    
                # Search Qdrant
                search_results = self.vector_store.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    limit=10,
                    filters=filters if filters else None
                )
                
                for r in search_results:
                    all_retrieved_chunks.append({
                        "id": r.id,
                        "score": r.score,
                        "payload": r.payload or {}
                    })

        # 2. Gather Graph Context if Neo4j is needed
        if "neo4j" in plan.backends_needed and not self.graph_repo.use_fallback:
            if plan.intent == "prerequisites" and plan.course_code:
                # Fetch prerequisite chain
                cypher = """
                MATCH path = (c:Course {code: $code})-[:PREREQUISITE*]->(prereq:Course)
                RETURN path
                """
                results = self.graph_repo.execute_read_query(cypher, {"code": plan.course_code})
                # Build simple visualization from path
                # (A proper visualization builder would extract nodes/edges from 'path')
                # For now, we'll just return raw records in context.
                
                # We can also fetch concepts for these prerequisites to augment chunks
                cypher_concepts = """
                MATCH (c:Course {code: $code})-[:PREREQUISITE*]->(prereq:Course)
                MATCH (prereq)-[:HAS_OFFERING]->(o)-[:HAS_DOCUMENT]->(d)-[:COVERS|:MENTIONS]->(concept)
                RETURN prereq.code as course, concept.name as concept, concept.description as desc
                LIMIT 5
                """
                concept_results = self.graph_repo.execute_read_query(cypher_concepts, {"code": plan.course_code})
                
                # Add synthetic chunks for graph knowledge
                for r in concept_results:
                    all_retrieved_chunks.append({
                        "id": f"graph_prereq_{r['course']}_{r['concept']}",
                        "score": 0.8, # High confidence for explicit graph links
                        "payload": {
                            "text": f"Prerequisite Concept ({r['course']}): {r['concept']} - {r.get('desc', '')}",
                            "document_id": "GRAPH",
                            "course_code": r["course"],
                            "is_prerequisite": True,
                            "prerequisite_concept": r["concept"]
                        }
                    })
            
            elif plan.intent in ["topic_explain", "compare", "relationship"]:
                # Try to find related entities in the graph to boost context
                for entity in plan.entities_mentioned:
                    cypher = """
                    MATCH (n) WHERE toLower(n.name) CONTAINS toLower($entity)
                    MATCH (n)-[r]-(related)
                    RETURN n.name as source, type(r) as relation, labels(related)[0] as target_label, related.name as target, related.description as desc
                    LIMIT 10
                    """
                    results = self.graph_repo.execute_read_query(cypher, {"entity": entity})
                    for r in results:
                        text_fact = f"Graph Fact: {r['source']} {r['relation']} {r['target_label']} ({r['target']}). {r.get('desc', '')}"
                        all_retrieved_chunks.append({
                            "id": f"graph_fact_{r['source']}_{r['target']}",
                            "score": 0.7,
                            "payload": {
                                "text": text_fact,
                                "document_id": "GRAPH"
                            }
                        })

        # Remove exact duplicates by ID
        seen_ids = set()
        unique_chunks = []
        for c in all_retrieved_chunks:
            if c["id"] not in seen_ids:
                seen_ids.add(c["id"])
                unique_chunks.append(c)

        return {
            "query": query,
            "course_code": plan.course_code,
            "retrieved_chunks": unique_chunks,
            "graph_visualization": graph_visualization,
            "has_missing_prerequisites": plan.intent == "prerequisites"
        }
