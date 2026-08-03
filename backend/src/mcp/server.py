"""
mcp/server.py — FastMCP server for the KgpOne Academic Knowledge Platform.

Exposes tools and resources for external MCP clients (Claude Desktop,
ChatGPT plugin, MCP Inspector, etc.) via an SSE endpoint at /mcp/sse.

To connect from an external client:
  SSE URL: https://your-domain.com/mcp/sse

Available capabilities:
  - 11 tools covering semantic search, document catalog, graph lookup, downloads
  - 3 MCP Resources for browsing the catalog
  - 4 Prompts for common academic workflows
"""
import asyncio
import json
import logging

from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("mcp_server")

mcp = FastMCP(
    "KgpOne Academic Knowledge Server",
    instructions=(
        "You are connected to KgpOne, a university knowledge platform. "
        "Use the available tools to search course content, list documents, "
        "get download links, look up faculty, and answer academic questions. "
        "Always start with 'answer_question' for content questions. "
        "Use 'find_documents' followed by 'get_download_url' for file requests."
    ),
)

# ── Register tools ────────────────────────────────────────────────────────────
from src.mcp.tools import register_tools
register_tools(mcp)

# ── Register prompts ──────────────────────────────────────────────────────────
from src.mcp.prompts import register_prompts
register_prompts(mcp)

# ── MCP Resources ─────────────────────────────────────────────────────────────

@mcp.resource("kgpone://courses")
def resource_list_courses() -> str:
    """Browse all available courses on the KgpOne platform."""
    from src.infrastructure.database import SessionLocal
    from src.repositories.postgres.academic_repository import AcademicRepository
    db = SessionLocal()
    try:
        repo = AcademicRepository(db)
        courses = repo.get_courses()
        data = [
            {
                "code": c.code,
                "title": c.title,
                "credits": c.credits,
                "department": c.department.name if c.department else None,
            }
            for c in courses
        ]
        return json.dumps(data, indent=2)
    finally:
        db.close()


@mcp.resource("kgpone://documents/{document_id}")
def resource_document(document_id: str) -> str:
    """Get full metadata for a specific document by its UUID."""
    from src.infrastructure.database import SessionLocal
    from src.repositories.postgres.document_repository import DocumentRepository
    from uuid import UUID
    db = SessionLocal()
    try:
        repo = DocumentRepository(db)
        doc = repo.get_document(UUID(document_id))
        if not doc:
            return json.dumps({"error": f"Document '{document_id}' not found."})
        return json.dumps({
            "id": str(doc.id),
            "title": doc.title,
            "description": doc.description,
            "doc_type": doc.doc_type,
            "format": doc.format.value if hasattr(doc.format, "value") else doc.format,
            "file_size_bytes": doc.file_size_bytes,
            "status": doc.status.value if hasattr(doc.status, "value") else str(doc.status),
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "custom_metadata": {m.key: m.value for m in doc.metadata_entries},
        }, indent=2)
    finally:
        db.close()


@mcp.resource("kgpone://course/{course_code}/documents")
def resource_course_documents(course_code: str) -> str:
    """List all documents available for a given course code."""
    from src.infrastructure.database import SessionLocal
    from src.repositories.postgres.academic_repository import AcademicRepository
    db = SessionLocal()
    try:
        repo = AcademicRepository(db)
        courses = repo.get_courses()
        course = next((c for c in courses if c.code.upper() == course_code.upper()), None)
        if not course:
            return json.dumps({"error": f"Course '{course_code}' not found."})
        documents = []
        for offering in course.offerings:
            for doc in offering.documents:
                if not doc.is_deleted:
                    documents.append({
                        "id": str(doc.id),
                        "title": doc.title,
                        "doc_type": doc.doc_type,
                        "format": doc.format.value if hasattr(doc.format, "value") else doc.format,
                        "created_at": doc.created_at.isoformat() if doc.created_at else None,
                    })
        return json.dumps({"course": course_code, "documents": documents}, indent=2)
    finally:
        db.close()
