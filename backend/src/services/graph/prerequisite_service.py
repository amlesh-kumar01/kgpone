import logging
from typing import List, Dict, Any
from src.services.graph.graph_query_service import GraphQueryService
from src.config.neo4j import Neo4jRepo

logger = logging.getLogger("prerequisite_service")

class PrerequisiteService:
    def __init__(self):
        self.query_service = GraphQueryService()
        self.neo4j = Neo4jRepo()

    def diagnose_missing_prerequisites(self, query: str, active_course_code: str) -> Dict[str, Any]:
        """
        Scans a query for mention of known advanced concepts, walks the graph backwards,
        and returns missing prerequisite information along with a serialized node-link graph
        for frontend visualization.
        """
        # Retrieve all concept names in Neo4j (or local fallback graph)
        all_concepts = self._get_all_concept_names()
        
        detected_concepts = []
        query_lower = query.lower()
        
        # Match keywords in the query to concepts using smart word-overlap
        ignore_words = {"search", "algorithm", "basics", "theory", "representation", "techniques", "methods", "and", "the", "for", "with"}
        for concept in all_concepts:
            concept_lower = concept.lower()
            # 1. Direct substring check
            if concept_lower in query_lower:
                detected_concepts.append(concept)
                continue
                
            # 2. Key term overlap check
            words = [w for w in concept_lower.split() if w not in ignore_words and len(w) > 1]
            if words and any(w in query_lower for w in words):
                detected_concepts.append(concept)
                continue
                
        # Fallback if no specific keyword matches: look for fuzzy markers
        if not detected_concepts:
            if "heuristic" in query_lower or "pathfinding" in query_lower or "a*" in query_lower:
                detected_concepts.append("A* Heuristic")  # Example mock concept if not fully indexed
            elif "bellman" in query_lower or "dijkstra" in query_lower or "relaxation" in query_lower:
                detected_concepts.append("Bellman-Ford Algorithm")

        logger.info(f"Detected query concepts for traversal: {detected_concepts}")

        # Traverse prerequisites for each detected concept
        prereq_links = []
        for concept in detected_concepts:
            links = self.query_service.get_prerequisites_recursive(concept)
            prereq_links.extend(links)

        # Remove duplicate links
        seen = set()
        unique_links = []
        for link in prereq_links:
            key = (link["source_concept"], link["prereq_concept"])
            if key not in seen:
                seen.add(key)
                unique_links.append(link)

        # Build serialized visualization graph data (nodes & edges)
        nodes = []
        edges = []
        node_ids = set()

        # Add initial detected concepts as start nodes
        for concept in detected_concepts:
            if concept not in node_ids:
                node_ids.add(concept)
                nodes.append({
                    "id": concept,
                    "label": concept,
                    "course": active_course_code,
                    "type": "target"  # The subject the user asked about
                })

        # Add traversed relationships
        for link in unique_links:
            src = link["source_concept"]
            prereq = link["prereq_concept"]
            course = link["course_code"]
            desc = link.get("description", "")

            # Add source node if not present
            if src not in node_ids:
                node_ids.add(src)
                nodes.append({
                    "id": src,
                    "label": src,
                    "course": active_course_code,
                    "type": "intermediate"
                })

            # Add prerequisite node
            if prereq not in node_ids:
                node_ids.add(prereq)
                nodes.append({
                    "id": prereq,
                    "label": prereq,
                    "course": course,
                    "description": desc,
                    "type": "prerequisite"  # Missing foundational piece
                })

            # Add Edge
            edges.append({
                "id": f"edge_{src}_{prereq}",
                "source": src,
                "target": prereq,
                "label": "HAS_PREREQUISITE"
            })

        # Compile missing prerequisite concepts list
        missing_concepts = [n["id"] for n in nodes if n["type"] == "prerequisite"]

        return {
            "missing_prerequisites": missing_concepts,
            "has_missing_prerequisites": len(missing_concepts) > 0,
            "graph_visualization": {
                "nodes": nodes,
                "edges": edges
            },
            "prerequisite_links": unique_links
        }

    def _get_all_concept_names(self) -> List[str]:
        """Utility to get all stored concept names in Neo4j or local fallback graph."""
        if self.neo4j.use_fallback:
            return [
                node["id"] for key, node in self.neo4j._fallback_nodes.items()
                if node["label"] == "Concept"
            ]

        query = "MATCH (c:Concept) RETURN c.id AS name"
        try:
            records = self.neo4j.execute_query(query)
            return [r["name"] for r in records if r.get("name")]
        except Exception:
            return []
