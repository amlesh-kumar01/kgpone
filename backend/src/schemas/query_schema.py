from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class QueryPlan(BaseModel):
    intent: str
    course_code: Optional[str] = None
    course_offering_id: Optional[str] = None
    entities_mentioned: List[str] = []
    backends_needed: List[str] = []
    confidence_score: float = 1.0

class QueryRequest(BaseModel):
    query: str
    course_code: Optional[str] = None
    course_offering_id: Optional[str] = None

class CitationRead(BaseModel):
    citation_id: str
    source_title: str
    course_code: str
    academic_year: str
    page_number: int
    section: str
    confidence: str
    score: float
    is_prerequisite: bool
    prerequisite_concept: Optional[str] = None
    text_snippet: str

class SourceRead(BaseModel):
    document_id: str
    title: str
    course_code: str
    doc_type: str
    s3_key: str

class QueryResponse(BaseModel):
    answer: str
    citations: List[CitationRead]
    sources: List[SourceRead]
    graph_context: Optional[Dict[str, Any]] = None
    intent: str
    backends_used: List[str]
    cache_hit: bool = False
    confidence_score: float = 1.0

class SearchResult(BaseModel):
    document_id: str
    title: str
    course_code: str
    doc_type: str
    snippet: str
    score: float
    s3_key: str
