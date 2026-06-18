import asyncio
import sys
import os
import re
import logging

# Set up clean logging to console
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("playground")

# Ensure project root is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.infrastructure.database import SessionLocal, Base, engine
from src.models.user_model import User
from src.models.academic_model import Department, Course, CourseOffering, SemesterType
from src.models.document_model import Document, DocFormat, ProcessingStatus
from src.services.graph.graph_builder_service import GraphBuilderService
from src.services.rag.retrieval_service import RetrievalService
from src.services.rag.answer_service import AnswerService
from src.services.rag.rerank_service import RerankService
from src.services.rag.citation_service import CitationService
from src.repositories.qdrant.vector_repository import QdrantRepository
from src.services.ingestion.embedding.gemini_embedding import GeminiEmbedder

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def print_banner():
    print("=" * 60)
    print("             KgpOne Academic NEXUS RAG Playground")
    print("=" * 60)
    print(" Interactive CLI tool for trial-and-error testing and debugging")
    print("=" * 60)

def seed_academic_basics():
    """Ensures base departments, courses, and offerings exist in PostgreSQL."""
    db = SessionLocal()
    try:
        # Seed default users
        from pwdlib import PasswordHash
        password_hash = PasswordHash.recommended()
        
        # Admin
        admin = db.query(User).filter(User.email == "admin@kgpone.edu").first()
        if not admin:
            admin = User(
                email="admin@kgpone.edu",
                hashed_password=password_hash.hash("admin123"),
                full_name="System Administrator",
                role="ADMIN",
                is_active=True
            )
            db.add(admin)
            print("[+] Seeded Admin user (admin@kgpone.edu / admin123).")
        else:
            admin.hashed_password = password_hash.hash("admin123")
            print("[*] Force-updated Admin password to 'admin123'.")
            
        # Student
        student = db.query(User).filter(User.email == "student@kgpone.edu").first()
        if not student:
            student = User(
                email="student@kgpone.edu",
                hashed_password=password_hash.hash("student123"),
                full_name="Test Student",
                role="STUDENT",
                is_active=True
            )
            db.add(student)
            print("[+] Seeded Student user (student@kgpone.edu / student123).")
        else:
            student.hashed_password = password_hash.hash("student123")
            print("[*] Force-updated Student password to 'student123'.")
        db.commit()

        # 1. CSE Department
        dept = db.query(Department).filter(Department.code == "CSE").first()
        if not dept:
            dept = Department(code="CSE", name="Computer Science and Engineering")
            db.add(dept)
            db.commit()
            db.refresh(dept)
            print("[+] Seeded CSE Department.")

        # 2. Main course (Algorithms)
        course_alg = db.query(Course).filter(Course.code == "CS30002").first()
        if not course_alg:
            course_alg = Course(
                department_id=dept.id,
                code="CS30002",
                title="Algorithms - II",
                description="Advanced algorithmic design, graphs, heuristics, and optimization.",
                credits=4
            )
            db.add(course_alg)
            db.commit()
            db.refresh(course_alg)
            print("[+] Seeded Course CS30002 (Algorithms - II).")

        # 3. Prerequisite course (Discrete Structures)
        course_disc = db.query(Course).filter(Course.code == "CS20005").first()
        if not course_disc:
            course_disc = Course(
                department_id=dept.id,
                code="CS20005",
                title="Discrete Structures",
                description="Foundational discrete mathematics, sets, graphs, and logic.",
                credits=4
            )
            db.add(course_disc)
            db.commit()
            db.refresh(course_disc)
            print("[+] Seeded Course CS20005 (Discrete Structures).")

        # 4. Course Offerings
        offering_alg = db.query(CourseOffering).filter(
            CourseOffering.course_id == course_alg.id,
            CourseOffering.year == 2026
        ).first()
        if not offering_alg:
            offering_alg = CourseOffering(
                course_id=course_alg.id,
                year=2026,
                semester=SemesterType.AUTUMN
            )
            db.add(offering_alg)
            print("[+] Seeded 2026 Autumn offering for CS30002.")

        offering_disc = db.query(CourseOffering).filter(
            CourseOffering.course_id == course_disc.id,
            CourseOffering.year == 2025
        ).first()
        if not offering_disc:
            offering_disc = CourseOffering(
                course_id=course_disc.id,
                year=2025,
                semester=SemesterType.AUTUMN
            )
            db.add(offering_disc)
            print("[+] Seeded 2025 Autumn offering for CS20005.")

        db.commit()
        print("[*] Database basics successfully seeded!")
    except Exception as e:
        print(f"[-] Database seeding failed: {e}")
        db.rollback()
    finally:
        db.close()

def build_prerequisite_graph():
    """Sets up concepts and prerequisite chains in Neo4j / Fallback dicts."""
    builder = GraphBuilderService()
    print("[*] Building Concept Graph...")
    
    # 1. Add course nodes
    builder.add_course_node("CS30002", "Algorithms - II", "2026-2027")
    builder.add_course_node("CS20005", "Discrete Structures", "2025-2026")
    
    # 2. Add Concept nodes
    # Advanced concepts in Algorithms II
    builder.add_concept_node("A* Heuristic Search", "CS30002", "Pathfinding algorithm utilizing heuristics to find optimal paths.")
    builder.add_concept_node("Bellman-Ford Algorithm", "CS30002", "Single-source shortest path algorithm handling negative weight cycles.")
    
    # Foundational prerequisite concepts in Discrete Structures
    builder.add_concept_node("Graph Basics & Traversals", "CS20005", "Vertices, edges, degrees, and BFS/DFS search paths.")
    builder.add_concept_node("Mathematical Induction", "CS20005", "Proving mathematical properties over infinite discrete sets.")

    # 3. Create prerequisite links:
    # A* Search HAS_PREREQUISITE Graph Traversals
    builder.link_prerequisite("A* Heuristic Search", "Graph Basics & Traversals")
    # Bellman-Ford HAS_PREREQUISITE Graph Basics & Traversals
    builder.link_prerequisite("Bellman-Ford Algorithm", "Graph Basics & Traversals")
    
    print("[+] Concept graph structure registered successfully!")

async def ingest_test_documents():
    """Ingests mock notes into Qdrant/Fallback Vector database."""
    print("[*] Indexing study notes content...")
    db = SessionLocal()
    try:
        # Get offerings
        course_alg = db.query(Course).filter(Course.code == "CS30002").first()
        course_disc = db.query(Course).filter(Course.code == "CS20005").first()
        
        offering_alg = db.query(CourseOffering).filter(CourseOffering.course_id == course_alg.id).first()
        offering_disc = db.query(CourseOffering).filter(CourseOffering.course_id == course_disc.id).first()

        # Ingestion payload definitions
        materials = [
            {
                "offering": offering_alg,
                "title": "Algorithms II Lecture Note: Heuristics & A* Search",
                "text": (
                    "A* search evaluates nodes by combining g(n), the cost to reach the node, and h(n), "
                    "the cost from the node to the goal: f(n) = g(n) + h(n). Since h(n) represents an estimation, "
                    "it must be admissible, meaning it never overestimates the actual cost to reach the goal."
                ),
                "course_code": "CS30002",
                "section": "Heuristic Algorithms"
            },
            {
                "offering": offering_disc,
                "title": "Discrete Math Slide: Foundations of Graph Theory",
                "text": (
                    "Graph Basics: A graph G = (V, E) consists of a set of vertices V and edges E. "
                    "A search algorithm like BFS explores nodes in layer-by-layer radial waves, "
                    "guaranteeing the shortest path on unweighted graphs, while DFS explores branches deep first."
                ),
                "course_code": "CS20005",
                "section": "Graph Fundamentals"
            }
        ]

        embedder = GeminiEmbedder()
        qdrant = QdrantRepository()

        for idx, item in enumerate(materials):
            # Create Document row
            doc = Document(
                course_offering_id=item["offering"].id,
                title=item["title"],
                doc_type="NOTES",
                format=DocFormat.PDF,
                s3_key=f"s3://playground/{idx}.pdf",
                status=ProcessingStatus.COMPLETED
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)

            # Generate vectors & upsert
            vectors = await embedder.embed([item["text"]])
            metadata = [{
                "document_id": str(doc.id),
                "course_code": item["course_code"],
                "title": item["title"],
                "text": item["text"],
                "header": item["section"],
                "page_number": 1
            }]
            await qdrant.upsert("documents", vectors, metadata)
            print(f"[+] Ingested Document: '{item['title']}' for {item['course_code']}")
            
        print("[*] Vector database successfully primed!")
    except Exception as e:
        print(f"[-] Document Ingestion failed: {e}")
        db.rollback()
    finally:
        db.close()

async def execute_rag_pipeline(query: str, course_code: str):
    """Runs the full GraphRAG pipeline from Query to Response."""
    print("\n" + "=" * 50)
    print(f"[Query] Executing GraphRAG: '{query}' in {course_code}")
    print("=" * 50)

    retriever = RetrievalService()
    reranker = RerankService()
    citer = CitationService()
    generator = AnswerService()

    # 1. Retrieve Context
    print("[1/4] Retrieving semantic & prerequisite context...")
    retrieved_data = await retriever.retrieve_context(query, course_code)
    chunks = retrieved_data["retrieved_chunks"]
    print(f"      -> Retrieved {len(chunks)} candidate source chunks.")
    if retrieved_data["has_missing_prerequisites"]:
        print(f"      -> Diagnostic alert: Found missing prerequisite paths!")
        print(f"      -> Visual Graph Nodes: {[n['id'] for n in retrieved_data['graph_visualization']['nodes']]}")

    # 2. Rerank
    print("[2/4] Reranking matches with lexical similarity boosts...")
    ranked = reranker.rerank_chunks(query, chunks, top_n=4)
    for idx, c in enumerate(ranked):
        print(f"      [{idx+1}] Score: {c.get('final_score', c.get('score', 0.0)):.3f} | {c['payload']['title'][:40]}... (Prereq: {c['payload'].get('is_prerequisite', False)})")

    # 3. Cite
    print("[3/4] Structuring source provenance citations...")
    citations = citer.format_citations(ranked)

    # 4. Generate Answer
    print("[4/4] Synthesizing final grounded response...")
    response = generator.generate_answer(query, ranked, citations)

    print("\n[Response] GENERATED ANSWER:")
    print("-" * 65)
    print(response)
    print("-" * 65)
    
    print("\n[Provenance] SOURCE CITATIONS:")
    for cit in citations:
        print(f"  - [{cit['citation_id']}] {cit['source_title']} (Page {cit['page_number']})")
        print(f"    Confidence: {cit['confidence']} | Relevance Score: {cit['score']}")
        if cit["is_prerequisite"]:
            print(f"    [!] Curriculum Time Travel: Found in prerequisite course: {cit['course_code']} for concept: {cit['prerequisite_concept']}")
        print(f"    Snippet: {cit['text_snippet'][:100]}...\n")

def list_workspace_db_contents():
    """Prints out all documents, courses, and offerings currently in Postgres."""
    db = SessionLocal()
    try:
        courses = db.query(Course).all()
        print("\n=== Relational DB Content ===")
        print(f"Registered Courses: {len(courses)}")
        for c in courses:
            print(f" - {c.code}: {c.title} (Credits: {c.credits})")
            for offering in c.offerings:
                print(f"    Offering ID: {offering.id} | Year: {offering.year} | Semester: {offering.semester.value}")
                for doc in offering.documents:
                    print(f"      Document: [{doc.status.value}] {doc.title} (S3 Key: {doc.s3_key})")
        print("=============================")
    finally:
        db.close()

async def main():
    # Make sure tables exist
    Base.metadata.create_all(bind=engine)
    
    while True:
        print_banner()
        print(" 1. Seed PostgreSQL Database (Base Courses & Offerings)")
        print(" 2. Seed Concept & Prerequisite Graph (Neo4j / Local Fallback)")
        print(" 3. Ingest Mock Study Notes into Vector DB (Qdrant / Local Fallback)")
        print(" 4. Seed Everything (1 + 2 + 3 in sequence)")
        print(" 5. Run Grounded GraphRAG Search Query")
        print(" 6. Display Current Relational DB State")
        print(" 7. Clear Screen")
        print(" 8. Exit")
        print("-" * 60)
        
        choice = input("Enter choice (1-8): ").strip()
        
        if choice == "1":
            seed_academic_basics()
        elif choice == "2":
            build_prerequisite_graph()
        elif choice == "3":
            await ingest_test_documents()
        elif choice == "4":
            seed_academic_basics()
            build_prerequisite_graph()
            await ingest_test_documents()
        elif choice == "5":
            print("\nActive Courses indexed: CS30002 (Algorithms II)")
            query = input("Enter search query (e.g. 'How does A* heuristic work?'): ").strip()
            if not query:
                query = "How does A* heuristic work?"
            await execute_rag_pipeline(query, "CS30002")
        elif choice == "6":
            list_workspace_db_contents()
        elif choice == "7":
            clear_screen()
        elif choice == "8":
            print("Goodbye!")
            break
        else:
            print("[-] Invalid choice. Enter 1-8.")
        
        print("\n")
        input("Press Enter to continue...")
        clear_screen()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExited.")
