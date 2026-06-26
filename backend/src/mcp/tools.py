import json
from fastmcp import FastMCP
from typing import List, Dict, Any, Optional

from src.infrastructure.database import SessionLocal
from src.repositories.postgres.academic_repository import AcademicRepository
from src.repositories.neo4j.graph_repository import Neo4jRepo
from src.schemas.query_schema import QueryRequest
from src.api.routes.query_routes import get_rag_services

def register_tools(mcp: FastMCP):

    @mcp.tool()
    def list_departments() -> list[dict]:
        """List all academic departments."""
        db = SessionLocal()
        try:
            repo = AcademicRepository(db)
            depts = repo.get_departments()
            return [{"id": str(d.id), "code": d.code, "name": d.name} for d in depts]
        finally:
            db.close()

    @mcp.tool()
    def search_courses(query: str = "", department_code: Optional[str] = None) -> list[dict]:
        """Search for courses by keyword or department."""
        db = SessionLocal()
        try:
            repo = AcademicRepository(db)
            courses = repo.get_courses(department_code=department_code)
            if query:
                q = query.lower()
                courses = [c for c in courses if q in c.title.lower() or q in c.code.lower()]
            return [{"id": str(c.id), "code": c.code, "title": c.title, "credits": c.credits} for c in courses]
        finally:
            db.close()

    @mcp.tool()
    def get_course_details(course_code: str) -> dict:
        """Get full details for a specific course including prerequisites."""
        db = SessionLocal()
        try:
            repo = AcademicRepository(db)
            courses = repo.get_courses()
            course = next((c for c in courses if c.code.lower() == course_code.lower()), None)
            if not course:
                return {"error": f"Course {course_code} not found."}
                
            return {
                "code": course.code,
                "title": course.title,
                "credits": course.credits,
                "department": course.department.name if course.department else None,
                "prerequisites": [p.code for p in course.prerequisites]
            }
        finally:
            db.close()

    @mcp.tool()
    def search_documents(query: str, course_code: Optional[str] = None) -> dict:
        """Semantic search for documents based on a query."""
        import asyncio
        services = get_rag_services()
        
        async def run_search():
            req = QueryRequest(query=query, course_code=course_code)
            plan = await services["planner"].detect_intent(req.query, req.course_code)
            plan.backends_needed = ["qdrant"] # force semantic search
            context = await services["retriever"].retrieve_context(req.query, plan)
            reranked_chunks = await services["reranker"].rerank_chunks(req.query, context["retrieved_chunks"], top_n=5)
            
            results = []
            for chunk in reranked_chunks:
                payload = chunk.get("payload", {})
                if payload.get("document_id") != "GRAPH":
                    results.append({
                        "title": payload.get("title"),
                        "doc_type": payload.get("document_type"),
                        "snippet": payload.get("text", "")[:250],
                        "score": chunk.get("final_score")
                    })
            return {"results": results}
            
        return asyncio.run(run_search())

    @mcp.tool()
    def answer_course_question(question: str, course_code: Optional[str] = None) -> dict:
        """Full Hybrid RAG: answers a student's question using all available context (vector + graph)."""
        import asyncio
        services = get_rag_services()
        
        async def run_qa():
            plan = await services["planner"].detect_intent(question, course_code)
            context = await services["retriever"].retrieve_context(question, plan)
            reranked = await services["reranker"].rerank_chunks(question, context["retrieved_chunks"], top_n=5)
            citations = services["citation_formatter"].format_citations(reranked)
            answer = services["answer_generator"].generate_answer(question, reranked, citations)
            return {
                "answer": answer,
                "citations": citations
            }
            
        return asyncio.run(run_qa())

    @mcp.tool()
    def get_course_topics(course_code: str) -> list[dict]:
        """Gets all topics extracted from course documents in the Neo4j Knowledge Graph."""
        graph_repo = Neo4jRepo()
        cypher = """
        MATCH (c:Course {code: $code})-[:HAS_OFFERING]->(o)-[:HAS_DOCUMENT]->(d)-[:COVERS]->(t:Topic)
        RETURN DISTINCT t.name as topic, t.description as description
        LIMIT 20
        """
        results = graph_repo.execute_read_query(cypher, {"code": course_code.upper()})
        return results
