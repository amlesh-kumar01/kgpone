import logging
from typing import Dict, Any
from src.repositories.neo4j.graph_repository import Neo4jRepo

logger = logging.getLogger("graph_builder_service")

class GraphBuilderService:
    def __init__(self):
        self.neo4j = Neo4jRepo()

    def add_course_node(self, course_code: str, title: str, academic_year: str):
        """Adds or updates a Course node."""
        properties = {
            "title": title,
            "academic_year": academic_year
        }
        return self.neo4j.upsert_node("Course", course_code, properties)

    def add_concept_node(self, name: str, course_code: str, description: str = ""):
        """Adds or updates a Concept node and links it to its parent Course."""
        properties = {
            "name": name,
            "course_code": course_code,
            "description": description
        }
        success = self.neo4j.upsert_node("Concept", name, properties)
        if success:
            self.neo4j.create_relationship("Concept", name, "Course", course_code, "BELONGS_TO")
        return success

    def link_prerequisite(self, concept_name: str, prerequisite_concept_name: str):
        """Creates a prerequisite link indicating concept_name HAS_PREREQUISITE prerequisite_concept_name."""
        return self.neo4j.create_relationship("Concept", concept_name, "Concept", prerequisite_concept_name, "HAS_PREREQUISITE")
