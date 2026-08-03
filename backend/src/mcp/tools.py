"""
mcp/tools.py — MCP Tool registrations for the KgpOne Academic Knowledge Server.

All tool logic is delegated to src/services/rag/agent_tools.py to ensure
a single source of truth. Both the internal agent and external MCP clients
(Claude, ChatGPT, etc.) call identical implementations.
"""
import asyncio
import json
from fastmcp import FastMCP
from typing import Optional

from src.infrastructure.database import SessionLocal
from src.repositories.postgres.academic_repository import AcademicRepository

# Shared async tool implementations
from src.services.rag.agent_tools import (
    vector_semantic_search,
    graph_entity_lookup,
    list_course_documents,
    get_document_metadata,
    get_document_download_url,
    search_document_catalog,
    get_faculty_info,
    get_course_prerequisites,
)


def register_tools(mcp: FastMCP):
    """Register all KgpOne tools on the MCP server."""

    # ─── 1. Departments ───────────────────────────────────────────────────────

    @mcp.tool()
    def list_departments() -> list[dict]:
        """List all academic departments available on the platform."""
        db = SessionLocal()
        try:
            repo = AcademicRepository(db)
            depts = repo.get_departments()
            return [{"id": str(d.id), "code": d.code, "name": d.name} for d in depts]
        finally:
            db.close()

    # ─── 2. Course Search ─────────────────────────────────────────────────────

    @mcp.tool()
    def search_courses(query: str = "", department_code: Optional[str] = None) -> list[dict]:
        """
        Search for courses by keyword or filter by department code.
        Returns course codes, titles, and credit counts.
        """
        db = SessionLocal()
        try:
            repo = AcademicRepository(db)
            courses = repo.get_courses()
            if query:
                q = query.lower()
                courses = [c for c in courses if q in c.title.lower() or q in c.code.lower()]
            return [{"id": str(c.id), "code": c.code, "title": c.title, "credits": c.credits} for c in courses]
        finally:
            db.close()

    # ─── 3. Semantic Search (delegated to shared agent tool) ──────────────────

    @mcp.tool()
    def semantic_search(
        query: str,
        course_code: Optional[str] = None,
        course_offering_id: Optional[str] = None,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Perform a semantic similarity search across all indexed academic content.
        Returns the most relevant text chunks with source document info.
        Use this to answer conceptual questions or find explanations from lecture notes.
        """
        return asyncio.run(
            vector_semantic_search.ainvoke({
                "query": query,
                "course_code": course_code,
                "course_offering_id": course_offering_id,
                "top_k": top_k,
            })
        )

    # ─── 4. Document Catalog Search ───────────────────────────────────────────

    @mcp.tool()
    def find_documents(
        query: str,
        doc_type: Optional[str] = None,
        course_code: Optional[str] = None,
    ) -> list[dict]:
        """
        Search for documents by title or description across the entire catalog.
        Optionally filter by doc_type (NOTES, SLIDES, PYQ, SYLLABUS) or course_code.
        Returns document metadata including IDs that can be used for other tools.
        """
        return asyncio.run(
            search_document_catalog.ainvoke({
                "query": query,
                "doc_type": doc_type,
                "course_code": course_code,
            })
        )

    # ─── 5. List Course Documents ─────────────────────────────────────────────

    @mcp.tool()
    def get_course_documents(
        course_code: str,
        doc_type: Optional[str] = None,
    ) -> list[dict]:
        """
        List all documents uploaded for a specific course offering.
        Filter by doc_type: NOTES, SLIDES, PYQ, SYLLABUS.
        Returns document IDs, titles, formats, and processing status.
        """
        return asyncio.run(
            list_course_documents.ainvoke({
                "course_code": course_code,
                "doc_type": doc_type,
            })
        )

    # ─── 6. Document Metadata ─────────────────────────────────────────────────

    @mcp.tool()
    def fetch_document_metadata(document_id: str) -> dict:
        """
        Retrieve the full metadata for a specific document by its UUID.
        Returns title, description, type, format, size, status, and custom metadata entries.
        """
        return asyncio.run(
            get_document_metadata.ainvoke({"document_id": document_id})
        )

    # ─── 7. Presigned Download URL ────────────────────────────────────────────

    @mcp.tool()
    def get_download_url(document_id: str) -> dict:
        """
        Generate a secure, time-limited presigned URL to download a document file.
        The URL is valid for 1 hour. Use this when the user wants the actual file.
        Returns the download URL and document title.
        """
        return asyncio.run(
            get_document_download_url.ainvoke({"document_id": document_id})
        )

    # ─── 8. Faculty Info ──────────────────────────────────────────────────────

    @mcp.tool()
    def get_course_faculty(course_code: str) -> list[dict]:
        """
        Get the professors, TAs, and coordinators for a given course.
        Returns name, role, email, and office hours for each faculty member.
        """
        return asyncio.run(
            get_faculty_info.ainvoke({"course_code": course_code})
        )

    # ─── 9. Prerequisites ─────────────────────────────────────────────────────

    @mcp.tool()
    def get_prerequisites(course_code: str) -> dict:
        """
        Get the official prerequisite courses for a given course.
        Returns the course details plus a list of all prerequisite courses
        with their titles, credits, and descriptions.
        """
        return asyncio.run(
            get_course_prerequisites.ainvoke({"course_code": course_code})
        )

    # ─── 10. Graph Entity Lookup ──────────────────────────────────────────────

    @mcp.tool()
    def lookup_knowledge_graph(entity: str, course_code: Optional[str] = None) -> list[dict]:
        """
        Query the academic knowledge graph for a concept or entity.
        Returns (source, relation, target) triples showing how concepts connect.
        Useful for understanding relationships, concept maps, and topic coverage.
        """
        return asyncio.run(
            graph_entity_lookup.ainvoke({
                "entity": entity,
                "course_code": course_code,
            })
        )

    # ─── 11. Full RAG Answer (convenience tool) ───────────────────────────────

    @mcp.tool()
    def answer_question(question: str, course_code: Optional[str] = None) -> dict:
        """
        Full Hybrid RAG: answers a student's academic question using semantic search
        + knowledge graph context. Returns a grounded answer with source citations.
        Use this as the primary tool for answering content questions.
        """
        from src.services.rag.nlp_planner_service import NLPPlannerService
        from src.services.rag.retrieval_service import RetrievalService
        from src.services.rag.cross_encoder_rerank_service import CrossEncoderRerankService
        from src.services.rag.citation_service import CitationService
        from src.services.rag.answer_service import AnswerService
        from src.services.ingestion.embedding.llm_embedding import LLMEmbedder
        from src.repositories.qdrant.vector_repository import QdrantRepository

        async def _run():
            planner = NLPPlannerService()
            embedder = LLMEmbedder()
            vector_repo = QdrantRepository()
            retriever = RetrievalService(embedder=embedder, vector_store=vector_repo)
            reranker = CrossEncoderRerankService()
            citation_service = CitationService()
            answer_gen = AnswerService()

            plan = await planner.detect_intent(question, course_code)
            context = await retriever.retrieve_context(question, plan)
            reranked = await reranker.rerank_chunks(question, context["retrieved_chunks"], top_n=5)
            citations = citation_service.format_citations(reranked)
            answer = answer_gen.generate_answer(question, reranked, citations)
            return {
                "answer": answer,
                "citations": citations,
                "intent": plan.intent,
            }

        return asyncio.run(_run())
