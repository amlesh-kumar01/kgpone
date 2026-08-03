"""
agent_tools.py — Shared async tool definitions for KgpOne.

These tools are designed as pure async functions and are used in two places:
  1. The internal AgenticPlannerService (LangChain tool-calling agent).
  2. The external MCP server (src/mcp/tools.py wrappers).

Each tool is self-contained and returns structured dicts that can be
serialised directly to JSON for streaming or MCP responses.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional
from uuid import UUID

from langchain_core.tools import tool

from src.infrastructure.database import SessionLocal
from src.repositories.postgres.document_repository import DocumentRepository
from src.repositories.postgres.academic_repository import AcademicRepository
from src.repositories.neo4j.graph_repository import Neo4jRepo
from src.repositories.s3.storage_repository import S3Storage

logger = logging.getLogger("agent_tools")


# ─────────────────────────────────────────────────────────────────────────────
# 1. Vector Semantic Search
# ─────────────────────────────────────────────────────────────────────────────

@tool
async def vector_semantic_search(
    query: str,
    course_code: Optional[str] = None,
    course_offering_id: Optional[str] = None,
    top_k: int = 8,
) -> list[dict[str, Any]]:
    """
    Perform a semantic similarity search across all indexed document chunks.
    Use this tool when the user asks a conceptual question, wants an explanation,
    or is looking for information that is contained inside lecture notes, slides,
    or past papers — and the exact document is not known.

    Returns a list of relevant text chunks with their source document info.
    """
    from src.services.rag.retrieval_service import RetrievalService
    from src.services.ingestion.embedding.llm_embedding import LLMEmbedder
    from src.repositories.qdrant.vector_repository import QdrantRepository
    from src.schemas.query_schema import QueryPlan

    embedder = LLMEmbedder()
    vector_repo = QdrantRepository()
    retriever = RetrievalService(embedder=embedder, vector_store=vector_repo)

    plan = QueryPlan(
        intent="semantic_search",
        course_code=course_code,
        course_offering_id=course_offering_id,
        backends_needed=["qdrant"],
    )

    context = await retriever.retrieve_context(query, plan)
    chunks = context.get("retrieved_chunks", [])[:top_k]

    results = []
    for chunk in chunks:
        payload = chunk.get("payload", {})
        results.append({
            "document_id": payload.get("document_id"),
            "document_title": payload.get("document_title") or payload.get("title"),
            "course_code": payload.get("course_code"),
            "doc_type": payload.get("document_type"),
            "page": payload.get("page_number"),
            "text_snippet": payload.get("text", "")[:500],
            "score": round(chunk.get("score", 0.0), 4),
        })

    return results

# ─────────────────────────────────────────────────────────────────────────────
# 1.5. Chat History Search
# ─────────────────────────────────────────────────────────────────────────────

@tool
async def search_chat_history(
    query: str,
    conversation_id: str,
) -> str:
    """
    Search through the user's complete past chat history for the specified conversation.
    Use this tool ONLY when the user explicitly asks about something discussed previously in the conversation
    and the context is not present in your truncated short-term memory (which only holds the last 5 messages).
    
    Returns a summarized string of matching past messages.
    """
    try:
        conv_uuid = UUID(conversation_id)
    except ValueError:
        return "Invalid conversation ID."

    with SessionLocal() as session:
        from src.repositories.postgres.chat_repository import ChatRepository
        repo = ChatRepository(session)
        conversation = repo.get_conversation(conv_uuid, load_messages=True)
        if not conversation:
            return "Conversation not found."

        # Simple keyword/substring search across all past messages
        query_terms = [t.lower() for t in query.split() if len(t) > 3]
        if not query_terms:
            query_terms = [query.lower()]
            
        results = []
        for msg in conversation.messages:
            content_lower = msg.content.lower()
            if any(term in content_lower for term in query_terms):
                results.append(f"{msg.role.name}: {msg.content}")

        if not results:
            return "No previous messages matched your query."
            
        return "\n\n".join(results[-10:]) # Return max 10 matching messages

# ─────────────────────────────────────────────────────────────────────────────
# 2. Graph Entity Lookup
# ─────────────────────────────────────────────────────────────────────────────

@tool
async def graph_entity_lookup(entity: str, course_code: Optional[str] = None) -> list[dict[str, Any]]:
    """
    Look up relationships, connections, and concept definitions for an entity
    (topic, concept, or term) in the academic knowledge graph (Neo4j).
    Use this to answer questions like "How is X related to Y?",
    "What are the prerequisites for X?", or "What topics does X cover?".

    Returns a list of graph relationships as (source, relation, target) triples.
    """
    cypher = """
        MATCH (n) WHERE toLower(n.name) CONTAINS toLower($entity)
        OPTIONAL MATCH (n)-[r]-(related)
        RETURN labels(n)[0] as source_label, n.name as source,
               type(r) as relation,
               labels(related)[0] as target_label, related.name as target,
               related.description as description
        LIMIT 15
    """

    graph_repo = Neo4jRepo()
    results = await asyncio.to_thread(
        graph_repo.execute_read_query, cypher, {"entity": entity}
    )

    triples = []
    for r in results:
        if r.get("source"):
            triples.append({
                "source": r["source"],
                "source_type": r.get("source_label"),
                "relation": r.get("relation"),
                "target": r.get("target"),
                "target_type": r.get("target_label"),
                "description": r.get("description"),
            })

    return triples


# ─────────────────────────────────────────────────────────────────────────────
# 3. List Course Documents
# ─────────────────────────────────────────────────────────────────────────────

@tool
async def list_course_documents(
    course_code: str,
    doc_type: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    List all documents uploaded for a specific course.
    Optionally filter by document type (e.g. 'NOTES', 'SLIDES', 'PYQ', 'SYLLABUS').
    Use this when the user asks: "What materials are available for CS101?",
    "Show me all past year papers for EE20005", or "What notes are uploaded?".

    Returns a list of document metadata objects including title, type, format, and ID.
    """
    def _fetch():
        db = SessionLocal()
        try:
            academic_repo = AcademicRepository(db)
            all_courses = academic_repo.get_courses()
            course = next((c for c in all_courses if c.code.upper() == course_code.upper()), None)
            if not course:
                return {"error": f"Course '{course_code}' not found."}

            documents = []
            for offering in course.offerings:
                for doc in offering.documents:
                    if doc.is_deleted:
                        continue
                    if doc_type and doc.doc_type.upper() != doc_type.upper():
                        continue
                    documents.append({
                        "id": str(doc.id),
                        "title": doc.title,
                        "description": doc.description,
                        "doc_type": doc.doc_type,
                        "format": doc.format.value if hasattr(doc.format, "value") else doc.format,
                        "file_size_bytes": doc.file_size_bytes,
                        "status": doc.status.value if hasattr(doc.status, "value") else str(doc.status),
                        "created_at": doc.created_at.isoformat() if doc.created_at else None,
                        "semester": offering.semester.value if hasattr(offering.semester, "value") else str(offering.semester),
                        "year": offering.year,
                    })
            return documents
        finally:
            db.close()

    return await asyncio.to_thread(_fetch)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Get Document Metadata
# ─────────────────────────────────────────────────────────────────────────────

@tool
async def get_document_metadata(document_id: str) -> dict[str, Any]:
    """
    Retrieve the full metadata for a specific document by its UUID.
    Use this when you already know the document ID (e.g. from a search result)
    and want to fetch its complete details including custom metadata key-value pairs,
    uploader info, processing status, and creation timestamp.

    Returns a rich metadata object for the document.
    """
    def _fetch():
        db = SessionLocal()
        try:
            doc_repo = DocumentRepository(db)
            doc = doc_repo.get_document(UUID(document_id))
            if not doc:
                return {"error": f"Document '{document_id}' not found."}

            custom_meta = {m.key: m.value for m in doc.metadata_entries}

            return {
                "id": str(doc.id),
                "title": doc.title,
                "description": doc.description,
                "doc_type": doc.doc_type,
                "format": doc.format.value if hasattr(doc.format, "value") else doc.format,
                "file_size_bytes": doc.file_size_bytes,
                "s3_key": doc.s3_key,
                "status": doc.status.value if hasattr(doc.status, "value") else str(doc.status),
                "version": doc.version,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
                "course_offering_id": str(doc.course_offering_id),
                "uploader_id": str(doc.uploader_id) if doc.uploader_id else None,
                "custom_metadata": custom_meta,
            }
        finally:
            db.close()

    return await asyncio.to_thread(_fetch)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Get Document Download URL
# ─────────────────────────────────────────────────────────────────────────────

@tool
async def get_document_download_url(document_id: str) -> dict[str, Any]:
    """
    Generate a secure, time-limited presigned download URL for a specific document.
    Use this when the user explicitly asks to download or access a document file,
    e.g. "Give me the PDF for CS101 notes" or "Download the past year paper".
    The returned URL is valid for 1 hour.

    Returns the presigned URL and document title.
    """
    def _fetch():
        db = SessionLocal()
        try:
            doc_repo = DocumentRepository(db)
            doc = doc_repo.get_document(UUID(document_id))
            if not doc:
                return {"error": f"Document '{document_id}' not found."}
            if not doc.s3_key:
                return {"error": "This document does not have an associated file."}

            storage = S3Storage()
            url = storage.generate_presigned_get_url(doc.s3_key, expiration=3600)
            return {
                "document_id": document_id,
                "title": doc.title,
                "doc_type": doc.doc_type,
                "download_url": url,
                "expires_in_seconds": 3600,
            }
        finally:
            db.close()

    return await asyncio.to_thread(_fetch)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Search Document Catalog
# ─────────────────────────────────────────────────────────────────────────────

@tool
async def search_document_catalog(
    query: str,
    doc_type: Optional[str] = None,
    course_code: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Fuzzy search across all documents in the catalog by title and description.
    Optionally filter by document type or course code.
    Use this when the user is looking for a specific named document,
    e.g. "Find the Attention is All You Need paper" or "Search for OS notes".

    Returns a list of matching documents with metadata.
    """
    def _fetch():
        db = SessionLocal()
        try:
            from sqlalchemy import select, or_
            from src.models.document_model import Document
            from src.models.academic_model import Course, CourseOffering

            stmt = (
                select(Document, CourseOffering, Course)
                .join(CourseOffering, Document.course_offering_id == CourseOffering.id)
                .join(Course, CourseOffering.course_id == Course.id)
                .where(Document.is_deleted == False)
            )

            if doc_type:
                stmt = stmt.where(Document.doc_type.ilike(doc_type))
            if course_code:
                stmt = stmt.where(Course.code.ilike(course_code))

            stmt = stmt.where(
                or_(
                    Document.title.ilike(f"%{query}%"),
                    Document.description.ilike(f"%{query}%"),
                )
            )
            stmt = stmt.limit(10)

            results = []
            for doc, offering, course in db.execute(stmt).fetchall():
                results.append({
                    "id": str(doc.id),
                    "title": doc.title,
                    "description": doc.description,
                    "doc_type": doc.doc_type,
                    "format": doc.format.value if hasattr(doc.format, "value") else doc.format,
                    "course_code": course.code,
                    "course_title": course.title,
                    "semester": offering.semester.value if hasattr(offering.semester, "value") else str(offering.semester),
                    "year": offering.year,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None,
                })
            return results
        finally:
            db.close()

    return await asyncio.to_thread(_fetch)


# ─────────────────────────────────────────────────────────────────────────────
# 7. Get Faculty Info
# ─────────────────────────────────────────────────────────────────────────────

@tool
async def get_faculty_info(course_code: str) -> list[dict[str, Any]]:
    """
    Retrieve professor, TA, and coordinator information for a given course.
    Use this when the user asks "Who teaches CS101?", "Who is the professor for this course?",
    "What are the office hours?", or "Who is the TA for EE20005?".

    Returns a list of faculty members with their role, email, and office hours.
    """
    def _fetch():
        db = SessionLocal()
        try:
            academic_repo = AcademicRepository(db)
            all_courses = academic_repo.get_courses()
            course = next((c for c in all_courses if c.code.upper() == course_code.upper()), None)
            if not course:
                return {"error": f"Course '{course_code}' not found."}

            faculty_list = []
            for offering in course.offerings:
                for f in offering.faculty:
                    faculty_list.append({
                        "name": f.name,
                        "role": f.role,
                        "email": f.email,
                        "office_hours": f.office_hours,
                        "semester": offering.semester.value if hasattr(offering.semester, "value") else str(offering.semester),
                        "year": offering.year,
                    })
            return faculty_list
        finally:
            db.close()

    return await asyncio.to_thread(_fetch)


# ─────────────────────────────────────────────────────────────────────────────
# 8. Get Course Prerequisites
# ─────────────────────────────────────────────────────────────────────────────

@tool
async def get_course_prerequisites(course_code: str) -> dict[str, Any]:
    """
    Retrieve the official prerequisite graph for a course from the academic database.
    Use this when the user asks "What do I need to know before taking CS101?",
    "What are the prerequisites for Machine Learning?", or "What should I study first?".

    Returns the course details and a list of prerequisite courses with their own details.
    """
    def _fetch():
        db = SessionLocal()
        try:
            academic_repo = AcademicRepository(db)
            all_courses = academic_repo.get_courses()
            course = next((c for c in all_courses if c.code.upper() == course_code.upper()), None)
            if not course:
                return {"error": f"Course '{course_code}' not found."}

            return {
                "code": course.code,
                "title": course.title,
                "description": course.description,
                "credits": course.credits,
                "prerequisites": [
                    {
                        "code": p.code,
                        "title": p.title,
                        "credits": p.credits,
                        "description": p.description,
                    }
                    for p in course.prerequisites
                ],
            }
        finally:
            db.close()

    return await asyncio.to_thread(_fetch)


# ─────────────────────────────────────────────────────────────────────────────
# Registry — easy access for MCP and agent bindings
# ─────────────────────────────────────────────────────────────────────────────

ALL_TOOLS = [
    vector_semantic_search,
    search_chat_history,
    graph_entity_lookup,
    list_course_documents,
    get_document_metadata,
    get_document_download_url,
    search_document_catalog,
    get_faculty_info,
    get_course_prerequisites,
]
