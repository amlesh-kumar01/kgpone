from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from uuid import UUID
from datetime import datetime

class QueryPlan(BaseModel):
    intent: str
    study_unit_code: Optional[str] = None
    study_unit_id: Optional[str] = None
    entities_mentioned: List[str] = []
    backends_needed: List[str] = []
    confidence_score: float = 1.0
    execution_strategy: Literal["standard", "map_reduce"] = "standard"
    target_document_ids: List[str] = []

class AgentSummary(BaseModel):
    intent: str = Field(description="e.g., semantic_search, full_doc_exam_prep, faculty_lookup")
    entities: List[str] = Field(description="Key entities extracted from the query.")
    execution_strategy: Literal["standard", "map_reduce"] = Field(
        description="Use 'map_reduce' if the user wants comprehensive coverage of an entire document (e.g., generating exam/interview questions from everywhere). Otherwise use 'standard'."
    )
    target_document_ids: List[str] = Field(
        default_factory=list, 
        description="If map_reduce is selected, provide the specific document IDs found via tools."
    )
    tool_results_summary: str = Field(description="A concise summary of all tool findings.")
    direct_answer: str = Field(default="")

class QueryRequest(BaseModel):
    query: str
    conversation_id: Optional[UUID] = None
    study_unit_code: Optional[str] = None
    study_unit_id: Optional[str] = None
    use_citations: bool = True
    # Controls which pipeline is used: basic = fast NLP, advanced = tool-calling agent, general = direct LLM, deep_research = map_reduce
    analysis_mode: Literal["basic", "advanced", "general", "deep_research"] = "basic"
    # BYOK — user supplies own key per-request; never persisted server-side
    byok_provider: Optional[Literal["openai", "gemini", "groq", "anthropic"]] = None
    byok_api_key: Optional[str] = Field(default=None, exclude=True)  # excluded from logs/responses
    byok_model: Optional[str] = None

class CitationRead(BaseModel):
    citation_id: str
    document_id: Optional[str] = None
    source_title: str = "Lecture Notes"
    study_unit_code: str = "GEN101"
    academic_year: str = ""
    page_number: Optional[int] = None
    section: str = "General"
    section_number: Optional[str] = None
    confidence: str = "Supporting Evidence"
    score: float = 0.0
    is_prerequisite: bool = False
    prerequisite_concept: Optional[str] = None
    source_url: Optional[str] = None
    text_snippet: str = ""
    # Chunk-type enrichment for frontend rendering
    chunk_type: str = "text"
    equation_label: Optional[str] = None
    raw_latex: Optional[str] = None
    image_s3_key: Optional[str] = None
    image_url: Optional[str] = None

class SourceRead(BaseModel):
    document_id: str
    title: str
    study_unit_code: str
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
    study_unit_code: str
    doc_type: str
    snippet: str
    score: float
    s3_key: str
