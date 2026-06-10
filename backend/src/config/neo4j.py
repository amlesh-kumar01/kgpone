import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("neo4j_config")

class Neo4jRepo:
    _driver = None
    # Local fallback graph: nodes are dicts by unique ID, relationships are lists of connections
    # Node keys: { "id": str, "labels": List[str], "properties": Dict[str, Any] }
    # Relationship keys: { "start_node_id": str, "end_node_id": str, "type": str }
    _fallback_nodes: Dict[str, Dict[str, Any]] = {}
    _fallback_relationships: List[Dict[str, Any]] = []

    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self.use_fallback = False

        if Neo4jRepo._driver is None:
            try:
                from neo4j import GraphDatabase
                # Connection with short connection timeout
                Neo4jRepo._driver = GraphDatabase.driver(
                    self.uri, 
                    auth=(self.user, self.password),
                    connection_timeout=3.0
                )
                # Verify connectivity
                Neo4jRepo._driver.verify_connectivity()
                logger.info(f"Successfully connected to Neo4j at {self.uri}")
            except Exception as e:
                logger.warning(f"Failed to connect to Neo4j at {self.uri}: {e}. Enabling offline graph fallback.")
                self.use_fallback = True
                Neo4jRepo._driver = None
        
        if Neo4jRepo._driver is None:
            self.use_fallback = True

    def execute_query(self, query: str, parameters: Optional[dict] = None) -> List[Dict[str, Any]]:
        """
        Runs a Cypher query. Returns a list of dict records.
        """
        if self.use_fallback:
            logger.debug(f"[Fallback Graph] Query not run directly: {query}")
            return []

        try:
            parameters = parameters or {}
            with Neo4jRepo._driver.session() as session:
                result = session.run(query, parameters)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Neo4j query execution failed: {e}. Enabling fallback mode.")
            self.use_fallback = True
            return []

    # Safe CRUD operations with automatic fallbacks:
    def upsert_node(self, label: str, node_id: str, properties: Dict[str, Any]):
        """
        Upserts a node uniquely by label and node_id key property.
        """
        if self.use_fallback:
            unique_key = f"{label}:{node_id}"
            Neo4jRepo._fallback_nodes[unique_key] = {
                "id": node_id,
                "label": label,
                "properties": properties
            }
            logger.info(f"[Fallback Graph] Upserted node: {unique_key}")
            return True

        query = f"""
        MERGE (n:{label} {{id: $node_id}})
        SET n += $properties
        RETURN n
        """
        try:
            self.execute_query(query, {"node_id": node_id, "properties": properties})
            return True
        except Exception as e:
            logger.warning(f"Neo4j upsert node failed: {e}. Writing to fallback.")
            self.use_fallback = True
            return self.upsert_node(label, node_id, properties)

    def create_relationship(self, from_label: str, from_id: str, to_label: str, to_id: str, rel_type: str):
        """
        Creates a directed relationship from node A to node B.
        """
        if self.use_fallback:
            from_key = f"{from_label}:{from_id}"
            to_key = f"{to_label}:{to_id}"
            
            # Check if relationship already exists
            exists = any(
                r["start"] == from_key and r["end"] == to_key and r["type"] == rel_type
                for r in Neo4jRepo._fallback_relationships
            )
            if not exists:
                Neo4jRepo._fallback_relationships.append({
                    "start": from_key,
                    "end": to_key,
                    "type": rel_type
                })
                logger.info(f"[Fallback Graph] Created relationship: {from_key} -[{rel_type}]-> {to_key}")
            return True

        query = f"""
        MATCH (a:{from_label} {{id: $from_id}})
        MATCH (b:{to_label} {{id: $to_id}})
        MERGE (a)-[r:{rel_type}]->(b)
        RETURN r
        """
        try:
            self.execute_query(query, {"from_id": from_id, "to_id": to_id})
            return True
        except Exception as e:
            logger.warning(f"Neo4j relationship failed: {e}. Writing to fallback.")
            self.use_fallback = True
            return self.create_relationship(from_label, from_id, to_label, to_id, rel_type)

    def find_prerequisites_recursive_local(self, concept_name: str) -> List[Dict[str, Any]]:
        """
        Helper for recursive graph traversal in local fallback memory store.
        Returns missing concept information in a traversal path.
        """
        visited = set()
        path = []
        
        def traverse(current_concept):
            current_key = f"Concept:{current_concept}"
            if current_key in visited:
                return
            visited.add(current_key)
            
            # Find relationships where this concept has a prerequisite
            # Node -[HAS_PREREQUISITE]-> Prerequisite
            for rel in Neo4jRepo._fallback_relationships:
                if rel["start"] == current_key and rel["type"] == "HAS_PREREQUISITE":
                    target_key = rel["end"]
                    prereq_node = Neo4jRepo._fallback_nodes.get(target_key)
                    if prereq_node:
                        prereq_concept = prereq_node["id"]
                        path.append({
                            "source_concept": current_concept,
                            "prereq_concept": prereq_concept,
                            "course_code": prereq_node["properties"].get("course_code", ""),
                            "description": prereq_node["properties"].get("description", "")
                        })
                        traverse(prereq_concept)

        traverse(concept_name)
        return path

    def close(self):
        if Neo4jRepo._driver:
            Neo4jRepo._driver.close()
            Neo4jRepo._driver = None
