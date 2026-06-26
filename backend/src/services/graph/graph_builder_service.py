import logging
from typing import Dict, Any, List
from src.repositories.neo4j.graph_repository import Neo4jRepo
from sqlalchemy.orm import Session
from src.models.academic_model import Department, Course, CourseOffering, FacultyInfo
from src.models.document_model import Document

logger = logging.getLogger("graph_builder_service")

class GraphBuilderService:
    def __init__(self):
        self.neo4j = Neo4jRepo()

    def sync_academic_data(self, db: Session):
        """Syncs structural data from PostgreSQL to Neo4j."""
        logger.info("Starting sync of academic data to Neo4j...")
        
        # Sync Departments
        departments = db.query(Department).all()
        for dept in departments:
            self.neo4j.merge_department(dept.code, {"name": dept.name})
            
        # Sync Courses
        courses = db.query(Course).all()
        for course in courses:
            self.neo4j.merge_course(course.code, {
                "title": course.title,
                "credits": course.credits
            })
            if course.department:
                self.neo4j.merge_relationship("Department", "code", course.department.code, 
                                            "Course", "code", course.code, "OFFERS")
                                            
            # Sync Prerequisites
            for prereq in course.prerequisites:
                self.neo4j.merge_relationship("Course", "code", prereq.code,
                                            "Course", "code", course.code, "PREREQUISITE")
                                            
        # Sync Offerings
        offerings = db.query(CourseOffering).all()
        for offering in offerings:
            offering_id_str = str(offering.id)
            self.neo4j.merge_course_offering(offering_id_str, {
                "year": offering.year,
                "semester": offering.semester.value,
                "course_code": offering.course.code
            })
            self.neo4j.merge_relationship("Course", "code", offering.course.code,
                                        "CourseOffering", "offering_id", offering_id_str, "HAS_OFFERING")
                                        
            # Sync Faculty
            for faculty in offering.faculty:
                self.neo4j.merge_faculty(faculty.name, {
                    "email": faculty.email or "",
                    "role": faculty.role or ""
                })
                self.neo4j.merge_relationship("CourseOffering", "offering_id", offering_id_str,
                                            "Faculty", "name", faculty.name, "TAUGHT_BY")
                                            
        logger.info("Academic data sync complete.")

    def add_document_to_graph(self, document: Document):
        """Creates Document node and links to CourseOffering."""
        doc_id = str(document.id)
        self.neo4j.merge_document(doc_id, {
            "title": document.title,
            "doc_type": document.doc_type,
            "course_code": document.course_offering.course.code,
            "s3_key": document.s3_key
        })
        self.neo4j.merge_relationship("CourseOffering", "offering_id", str(document.course_offering_id),
                                    "Document", "doc_id", doc_id, "HAS_DOCUMENT")

    def add_extracted_entities(self, doc_id: str, entities: Dict[str, Any]):
        """
        Takes entity extraction output (dict) and creates all nodes + relationships.
        Links extracted entities to the Document.
        """
        logger.info(f"Adding extracted entities for document {doc_id} to graph...")
        
        # Topics
        for topic in entities.get("topics", []):
            name = topic.get("name", "").strip().lower()
            if not name: continue
            self.neo4j.merge_topic(name, {"description": topic.get("description", "")})
            self.neo4j.merge_relationship("Document", "doc_id", doc_id, "Topic", "name", name, "COVERS")

        # Concepts
        for concept in entities.get("concepts", []):
            name = concept.get("name", "").strip().lower()
            if not name: continue
            self.neo4j.merge_concept(name, {"description": concept.get("description", "")})
            self.neo4j.merge_relationship("Document", "doc_id", doc_id, "Concept", "name", name, "MENTIONS")
            
            for dep in concept.get("depends_on", []):
                dep_name = dep.strip().lower()
                if dep_name:
                    self.neo4j.merge_concept(dep_name, {}) # Ensure it exists
                    self.neo4j.merge_relationship("Concept", "name", name, "Concept", "name", dep_name, "DEPENDS_ON")

        # Algorithms
        for algo in entities.get("algorithms", []):
            name = algo.get("name", "").strip().lower()
            if not name: continue
            self.neo4j.merge_algorithm(name, {
                "description": algo.get("description", ""),
                "complexity": algo.get("complexity", "")
            })
            self.neo4j.merge_relationship("Document", "doc_id", doc_id, "Algorithm", "name", name, "MENTIONS")
            
            for formula_ref in algo.get("uses_formulas", []):
                fname = formula_ref.strip().lower()
                if fname:
                    self.neo4j.merge_formula(fname, {}) # Ensure it exists
                    self.neo4j.merge_relationship("Algorithm", "name", name, "Formula", "name", fname, "USES")

        # Formulas
        for formula in entities.get("formulas", []):
            name = formula.get("name", "").strip().lower()
            if not name: continue
            self.neo4j.merge_formula(name, {
                "description": formula.get("description", ""),
                "expression": formula.get("expression", "")
            })
            self.neo4j.merge_relationship("Document", "doc_id", doc_id, "Formula", "name", name, "HAS_FORMULA")

        # Technologies
        for tech in entities.get("technologies", []):
            name = tech.get("name", "").strip().lower()
            if not name: continue
            self.neo4j.merge_technology(name, {"description": tech.get("description", "")})
            self.neo4j.merge_relationship("Document", "doc_id", doc_id, "Technology", "name", name, "MENTIONS")

        # Books
        for book in entities.get("books", []):
            title = book.get("title", "").strip().lower()
            if not title: continue
            self.neo4j.merge_book(title, {"author": book.get("author", "")})
            self.neo4j.merge_relationship("Document", "doc_id", doc_id, "Book", "title", title, "REFERENCES")

        # Research Papers
        for paper in entities.get("papers", []):
            title = paper.get("title", "").strip().lower()
            if not title: continue
            self.neo4j.merge_research_paper(title, {
                "authors": paper.get("authors", ""),
                "year": paper.get("year", 0)
            })
            self.neo4j.merge_relationship("Document", "doc_id", doc_id, "ResearchPaper", "title", title, "REFERENCES")

        # Custom Relationships
        for rel in entities.get("relationships", []):
            from_entity = rel.get("from_entity", "").strip().lower()
            to_entity = rel.get("to_entity", "").strip().lower()
            relation = rel.get("relation", "").strip().upper()
            if from_entity and to_entity and relation:
                # We need to assume node type based on what exists, but since we don't know the exact type here easily,
                # we can use the generic merge for Concepts as a fallback for relations.
                self.neo4j.merge_concept(from_entity, {})
                self.neo4j.merge_concept(to_entity, {})
                self.neo4j.merge_relationship("Concept", "name", from_entity, "Concept", "name", to_entity, relation)

        logger.info(f"Finished adding entities for document {doc_id}.")

    # --- Legacy fallbacks for compatibility during refactor ---
    def add_course_node(self, course_code: str, title: str, academic_year: str):
        return self.neo4j.merge_course(course_code, {"title": title, "academic_year": academic_year})

    def add_concept_node(self, name: str, course_code: str, description: str = ""):
        self.neo4j.merge_concept(name.lower(), {"description": description, "course_code": course_code})
        return self.neo4j.merge_relationship("Course", "code", course_code, "Concept", "name", name.lower(), "BELONGS_TO")

    def link_prerequisite(self, concept_name: str, prerequisite_concept_name: str):
        return self.neo4j.merge_relationship("Concept", "name", concept_name.lower(), "Concept", "name", prerequisite_concept_name.lower(), "HAS_PREREQUISITE")
