import logging
from typing import List, Dict, Any, Optional
from src.infrastructure.neo4j import get_neo4j_driver

logger = logging.getLogger("neo4j_repository")
_schema_initialized = False

class Neo4jRepo:
    def __init__(self):
        self.use_fallback = False
        driver = get_neo4j_driver()
        if driver is None:
            self.use_fallback = True
            
        global _schema_initialized
        if not _schema_initialized:
            self.initialize_schema()
            _schema_initialized = True

    def _get_driver(self):
        driver = get_neo4j_driver()
        if driver is None:
            self.use_fallback = True
        return driver

    def initialize_schema(self):
        """Creates constraints and indexes for production."""
        driver = self._get_driver()
        if not driver:
            return
            
        queries = [
            "CREATE CONSTRAINT dept_code IF NOT EXISTS FOR (d:OrganizationalUnit) REQUIRE d.code IS UNIQUE",
            "CREATE CONSTRAINT study_unit_code IF NOT EXISTS FOR (c:StudyUnit) REQUIRE c.code IS UNIQUE",
            "CREATE CONSTRAINT offering_id IF NOT EXISTS FOR (o:Offering) REQUIRE o.offering_id IS UNIQUE",
            "CREATE CONSTRAINT doc_id IF NOT EXISTS FOR (d:Document) REQUIRE d.doc_id IS UNIQUE",
            "CREATE CONSTRAINT section_id IF NOT EXISTS FOR (s:Section) REQUIRE s.section_id IS UNIQUE",
            "CREATE CONSTRAINT formula_id IF NOT EXISTS FOR (f:Formula) REQUIRE f.formula_id IS UNIQUE",
            "CREATE CONSTRAINT question_id IF NOT EXISTS FOR (q:Question) REQUIRE q.question_id IS UNIQUE",
            "CREATE INDEX topic_name IF NOT EXISTS FOR (t:Topic) ON (t.name)",
            "CREATE INDEX concept_name IF NOT EXISTS FOR (c:Concept) ON (c.name)",
            "CREATE INDEX algo_name IF NOT EXISTS FOR (a:Algorithm) ON (a.name)",
            "CREATE INDEX tech_name IF NOT EXISTS FOR (t:Technology) ON (t.name)"
        ]
        
        try:
            with driver.session() as session:
                for q in queries:
                    session.run(q)
            logger.info("Successfully initialized Neo4j constraints and indexes.")
        except Exception as e:
            logger.warning(f"Failed to initialize Neo4j schema (it may already exist): {e}")

    def execute_read_query(self, query: str, parameters: Optional[dict] = None) -> List[Dict[str, Any]]:
        """Executes a read transaction."""
        driver = self._get_driver()
        if not driver:
            return []
            
        try:
            parameters = parameters or {}
            with driver.session() as session:
                result = session.execute_read(lambda tx: list(tx.run(query, parameters)))
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Neo4j read query failed: {e}")
            return []

    def execute_write_query(self, query: str, parameters: Optional[dict] = None) -> bool:
        """Executes a write transaction."""
        driver = self._get_driver()
        if not driver:
            return False
            
        try:
            parameters = parameters or {}
            with driver.session() as session:
                session.execute_write(lambda tx: tx.run(query, parameters))
                return True
        except Exception as e:
            logger.error(f"Neo4j write query failed: {e}")
            return False
            
    # --- Node Merging Methods ---
    
    def merge_node(self, label: str, unique_key: str, unique_value: str, properties: dict) -> bool:
        """Generic method to merge a node by a unique key."""
        query = f"""
        MERGE (n:{label} {{{unique_key}: $unique_value}})
        SET n += $properties
        RETURN n
        """
        return self.execute_write_query(query, {"unique_value": unique_value, "properties": properties})

    def merge_org_unit(self, code: str, properties: dict):
        return self.merge_node("OrganizationalUnit", "code", code, properties)

    def merge_course(self, code: str, properties: dict):
        return self.merge_node("StudyUnit", "code", code, properties)

    def merge_course_offering(self, offering_id: str, properties: dict):
        return self.merge_node("Offering", "offering_id", offering_id, properties)

    def merge_faculty(self, name: str, properties: dict):
        return self.merge_node("Faculty", "name", name, properties)

    def merge_document(self, doc_id: str, properties: dict):
        return self.merge_node("Document", "doc_id", doc_id, properties)

    def merge_topic(self, name: str, properties: dict):
        return self.merge_node("Topic", "name", name, properties)

    def merge_concept(self, name: str, properties: dict):
        return self.merge_node("Concept", "name", name, properties)

    def merge_algorithm(self, name: str, properties: dict):
        return self.merge_node("Algorithm", "name", name, properties)

    def merge_formula(self, formula_id: str, properties: dict):
        return self.merge_node("Formula", "formula_id", formula_id, properties)

    def merge_section(self, section_id: str, properties: dict):
        return self.merge_node("Section", "section_id", section_id, properties)

    def merge_question(self, question_id: str, properties: dict):
        return self.merge_node("Question", "question_id", question_id, properties)

    def merge_technology(self, name: str, properties: dict):
        return self.merge_node("Technology", "name", name, properties)

    def merge_book(self, title: str, properties: dict):
        return self.merge_node("Book", "title", title, properties)

    def merge_research_paper(self, title: str, properties: dict):
        return self.merge_node("ResearchPaper", "title", title, properties)
        
    # --- Relationship Merging Methods ---

    def merge_relationship(self, from_label: str, from_key: str, from_val: str, 
                           to_label: str, to_key: str, to_val: str, rel_type: str) -> bool:
        """Generic method to merge a relationship."""
        # Sanitize rel_type for Cypher (replace spaces and hyphens with underscores, uppercase)
        clean_rel = rel_type.strip().replace(' ', '_').replace('-', '_').upper()
        
        query = f"""
        MATCH (a:{from_label} {{{from_key}: $from_val}})
        MATCH (b:{to_label} {{{to_key}: $to_val}})
        MERGE (a)-[r:`{clean_rel}`]->(b)
        RETURN r
        """
        return self.execute_write_query(query, {"from_val": from_val, "to_val": to_val})
        
    # --- Queries ---
    
    def get_document_entities(self, doc_id: str):
        query = """
        MATCH (d:Document {doc_id: $doc_id})-[r]->(e)
        RETURN type(r) as rel_type, labels(e)[0] as entity_type, e as entity
        """
        return self.execute_read_query(query, {"doc_id": doc_id})

    # --- Deletion ---
        
    def delete_document_entities(self, document_id: str) -> bool:
        """Deletes the document node and any dangling entities (including Topics and Tables) that only this document links to"""
        query = """
        MATCH (d:Document {doc_id: $doc_id})
        OPTIONAL MATCH (d)-[:COVERS|MENTIONS|HAS_FORMULA|REFERENCES|COVERS_TOPIC|CONTAINS_TABLE]->(e)
        DETACH DELETE d
        WITH e
        WHERE e IS NOT NULL AND NOT ()-->(e)
        DETACH DELETE e
        """
        return self.execute_write_query(query, {"doc_id": document_id})
        
    def delete_course_subgraph(self, study_unit_code: str) -> bool:
        """Delete StudyUnit and cascading offerings and documents."""
        query = """
        MATCH (c:StudyUnit {code: $study_unit_code})
        OPTIONAL MATCH (c)-[:HAS_OFFERING]->(o:Offering)
        OPTIONAL MATCH (o)-[:HAS_DOCUMENT]->(d:Document)
        DETACH DELETE c, o, d
        """
        return self.execute_write_query(query, {"study_unit_code": study_unit_code})

    def build_document_skeleton(self, doc_id: str, document_dom: Any) -> bool:
        """Stores the structural skeleton (ToC, Tables) of a document in Neo4j without raw text."""
        # 1. Ensure Document node exists
        self.merge_document(doc_id, {"title": document_dom.title})
        
        # 2. Iterate through ToC to create structural Heading/Topic nodes
        for item in document_dom.toc:
            title = item.get("title")
            if title:
                # Store as a Topic node
                self.merge_topic(title, {"level": item.get("level")})
                self.merge_relationship("Document", "doc_id", doc_id, "Topic", "name", title, "COVERS_TOPIC")
                
        # 3. Tables can be added as structural nodes too
        for node in document_dom.nodes:
            if node.node_type == "table":
                # Only store table metadata, not the full text
                table_title = node.metadata.parent_table_title or f"Table_in_{doc_id}"
                props = {"page": node.page_number}
                if node.metadata.headers:
                    props["headers"] = ",".join(node.metadata.headers)
                self.merge_node("Table", "name", table_title, props)
                self.merge_relationship("Document", "doc_id", doc_id, "Table", "name", table_title, "CONTAINS_TABLE")
                
        return True

    def close(self):
        pass

    # Aliases for older methods to prevent breaking changes during refactor
    def execute_query(self, query: str, parameters: Optional[dict] = None) -> List[Dict[str, Any]]:
        return self.execute_read_query(query, parameters)
        
    def upsert_node(self, label: str, node_id: str, properties: Dict[str, Any]) -> bool:
        # Fallback for previous code
        unique_key = "id" if label in ["StudyUnit", "Concept"] else "name"
        return self.merge_node(label, unique_key, node_id, properties)

    def create_relationship(self, from_label: str, from_id: str, to_label: str, to_id: str, rel_type: str) -> bool:
        # Fallback for previous code
        from_key = "id" if from_label in ["StudyUnit", "Concept"] else "name"
        to_key = "id" if to_label in ["StudyUnit", "Concept"] else "name"
        return self.merge_relationship(from_label, from_key, from_id, to_label, to_key, to_id, rel_type)
