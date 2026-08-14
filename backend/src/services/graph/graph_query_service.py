import logging
from typing import List, Dict, Any
from src.repositories.neo4j.graph_repository import Neo4jRepo

logger = logging.getLogger("graph_query_service")

class GraphQueryService:
    def __init__(self):
        self.neo4j = Neo4jRepo()

    def get_prerequisites_recursive(self, concept_name: str) -> List[Dict[str, Any]]:
        """
        Recursively retrieves all prerequisites for a given concept.
        Returns a list of dicts:
        [
            {
                "source_concept": str,
                "prereq_concept": str,
                "study_unit_code": str,
                "description": str
            }
        ]
        """
        if self.neo4j.use_fallback:
            return self.neo4j.find_prerequisites_recursive_local(concept_name)

        query = """
        MATCH (c:Concept {id: $concept_name})
        MATCH path = (c)-[:HAS_PREREQUISITE*]->(p:Concept)
        UNWIND relationships(path) as r
        RETURN 
            startNode(r).id AS source_concept, 
            endNode(r).id AS prereq_concept, 
            endNode(r).study_unit_code AS study_unit_code, 
            endNode(r).description AS description
        """
        try:
            records = self.neo4j.execute_query(query, {"concept_name": concept_name})
            
            # Neo4j might return duplicate relationships across paths; deduplicate them
            seen = set()
            deduped = []
            for r in records:
                key = (r["source_concept"], r["prereq_concept"])
                if key not in seen:
                    seen.add(key)
                    deduped.append(r)
            return deduped
        except Exception as e:
            logger.error(f"Error querying Neo4j prerequisites recursively: {e}")
            return self.neo4j.find_prerequisites_recursive_local(concept_name)
            
    def get_concept_details(self, concept_name: str) -> Dict[str, Any]:
        """Fetches details for a single concept node."""
        if self.neo4j.use_fallback:
            node = self.neo4j._fallback_nodes.get(f"Concept:{concept_name}")
            return node["properties"] if node else {}

        query = "MATCH (c:Concept {id: $concept_name}) RETURN c LIMIT 1"
        try:
            res = self.neo4j.execute_query(query, {"concept_name": concept_name})
            if res:
                # Neo4j return node object
                node_props = dict(res[0]["c"])
                return node_props
            return {}
        except Exception:
            return {}
