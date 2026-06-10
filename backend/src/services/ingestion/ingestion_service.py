import uuid
import logging
from typing import Dict, Any
from src.services.ingestion.chunking_service import ChunkingService
from src.services.ingestion.embedding_service import EmbeddingService
from src.config.qdrant import QdrantRepo
from src.config.neo4j import Neo4jRepo

logger = logging.getLogger("ingestion_service")

class IngestionService:
    def __init__(self):
        self.chunker = ChunkingService()
        self.embedder = EmbeddingService()
        self.qdrant = QdrantRepo()
        self.neo4j = Neo4jRepo()
        self.collection_name = "kgpone_course_chunks"

    def ingest_parsed_markdown(self, file_id: str, markdown_content: str, metadata: Dict[str, Any]) -> bool:
        """
        Ingests parsed markdown:
        1. Chunks the document.
        2. Embeds the chunks.
        3. Stores chunks & embeddings in Qdrant.
        4. Extracts concepts and indexes nodes and relationships in Neo4j.
        """
        course_code = metadata.get("course_code", "GEN101")
        academic_year = metadata.get("academic_year", "1st Year")
        title = metadata.get("title", "Lecture Notes")

        try:
            # 1. Chunk document
            chunks = self.chunker.chunk_markdown(markdown_content)
            if not chunks:
                logger.warning(f"No chunks generated for file_id {file_id}")
                return False
            
            logger.info(f"Generated {len(chunks)} chunks for document: {title}")

            # 2. Embed chunks and format Qdrant payloads
            qdrant_points = []
            extracted_concepts = set()

            for chunk in chunks:
                chunk_id = str(uuid.uuid4())
                chunk_text = chunk["text"]
                header = chunk["header"]
                page_num = chunk["page_number"]

                # Generate vector embedding
                vector = self.embedder.get_embedding(chunk_text)

                qdrant_points.append({
                    "id": chunk_id,
                    "vector": vector,
                    "payload": {
                        "file_id": file_id,
                        "text": chunk_text,
                        "header": header,
                        "page_number": page_num,
                        "course_code": course_code,
                        "academic_year": academic_year,
                        "title": title
                    }
                })

                if header and header != "Introduction":
                    extracted_concepts.add(header)

            # 3. Store in Qdrant
            self.qdrant.upsert_chunks(self.collection_name, qdrant_points)

            # 4. Store concept nodes and prerequisite graph structure in Neo4j
            # Upsert Course Node
            self.neo4j.upsert_node("Course", course_code, {
                "course_code": course_code,
                "academic_year": academic_year,
                "title": title
            })

            for concept in extracted_concepts:
                # Upsert Concept Node
                self.neo4j.upsert_node("Concept", concept, {
                    "name": concept,
                    "course_code": course_code,
                    "academic_year": academic_year
                })
                # Link Concept to Course
                self.neo4j.create_relationship("Concept", concept, "Course", course_code, "BELONGS_TO")

            # 5. Populate Prerequisite Bridges for Demo Scenario
            # To showcase the "Curriculum Time Travel" feature, we automatically create 
            # prerequisite bridges from advanced concepts to foundational math/algorithm concepts.
            self._setup_demo_prerequisite_bridges(course_code, extracted_concepts)

            return True

        except Exception as e:
            logger.error(f"Failed to ingest parsed notes {file_id}: {e}")
            return False

    def _setup_demo_prerequisite_bridges(self, active_course_code: str, active_concepts: set):
        """
        Establishes mock/demo prerequisite relationships between common courses.
        Example: If we upload advanced material with terms like 'A* Heuristic' or 'Bellman-Ford',
        we bind them to discrete math prerequisites.
        """
        for concept in active_concepts:
            concept_lower = concept.lower()
            
            # Prerequisite Bridge 1: "A* Pathfinding" or "Heuristics" requires "Discrete Graph Traversal"
            if "a*" in concept_lower or "heuristic" in concept_lower:
                prereq_concept = "Graph Theory Basics"
                prereq_course = "MTH201" # 2nd Year Discrete Mathematics
                
                # Create prerequisite concept node
                self.neo4j.upsert_node("Concept", prereq_concept, {
                    "name": prereq_concept,
                    "course_code": prereq_course,
                    "academic_year": "2nd Year",
                    "description": "Fundamental graph theory, nodes, edges, adjacency list, and basic path search."
                })
                self.neo4j.upsert_node("Course", prereq_course, {
                    "course_code": prereq_course,
                    "academic_year": "2nd Year",
                    "title": "Discrete Mathematics"
                })
                self.neo4j.create_relationship("Concept", prereq_concept, "Course", prereq_course, "BELONGS_TO")
                
                # Link active concept to prerequisite concept
                self.neo4j.create_relationship("Concept", concept, "Concept", prereq_concept, "HAS_PREREQUISITE")
                logger.info(f"Built prerequisite bridge: Concept '{concept}' -> Prereq '{prereq_concept}' in Course '{prereq_course}'")

            # Prerequisite Bridge 2: "Bellman-Ford" or "Dijkstra" requires "Relaxation Theorem"
            elif "bellman" in concept_lower or "dijkstra" in concept_lower or "shortest path" in concept_lower:
                prereq_concept = "Graph Matrix Representation"
                prereq_course = "MTH201"
                
                self.neo4j.upsert_node("Concept", prereq_concept, {
                    "name": prereq_concept,
                    "course_code": prereq_course,
                    "academic_year": "2nd Year",
                    "description": "Adjacency matrix representation and vector operations for vertex relaxation."
                })
                self.neo4j.upsert_node("Course", prereq_course, {
                    "course_code": prereq_course,
                    "academic_year": "2nd Year",
                    "title": "Discrete Mathematics"
                })
                self.neo4j.create_relationship("Concept", prereq_concept, "Course", prereq_course, "BELONGS_TO")
                
                self.neo4j.create_relationship("Concept", concept, "Concept", prereq_concept, "HAS_PREREQUISITE")
                logger.info(f"Built prerequisite bridge: Concept '{concept}' -> Prereq '{prereq_concept}' in Course '{prereq_course}'")
