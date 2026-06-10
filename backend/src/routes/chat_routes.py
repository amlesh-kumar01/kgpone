from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Any

from src.middleware.auth_middleware import get_current_user
from src.models.user_model import User
from src.services.rag.retrieval_service import RetrievalService
from src.services.rag.rerank_service import RerankService
from src.services.rag.citation_service import CitationService
from src.services.rag.answer_service import AnswerService

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    course_code: str

class CitationResponse(BaseModel):
    citation_id: str
    source_title: str
    course_code: str
    academic_year: str
    page_number: int
    section: str
    confidence: str
    score: float
    is_prerequisite: bool
    prerequisite_concept: str | None = None
    text_snippet: str

class GraphNode(BaseModel):
    id: str
    label: str
    course: str
    description: str | None = None
    type: str

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str

class GraphVisualization(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

class QueryResponse(BaseModel):
    answer: str
    citations: List[CitationResponse]
    graph_visualization: GraphVisualization
    has_missing_prerequisites: bool

@router.post("/query", response_model=QueryResponse)
def query_rag(
    req: QueryRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Executes a hybrid GraphRAG query:
    1. Retrieves direct and prerequisite context chunks.
    2. Reranks chunks using vector and keyword features.
    3. Formats citations/provenance records.
    4. Generates grounded tutor response.
    5. Returns answer, citations, and prerequisite visual graph.
    """
    try:
        retrieval_service = RetrievalService()
        rerank_service = RerankService()
        citation_service = CitationService()
        answer_service = AnswerService()

        # 1. Retrieve raw contexts
        retrieval_result = retrieval_service.retrieve_context(req.query, req.course_code)
        
        # 2. Rerank
        ranked_chunks = rerank_service.rerank_chunks(
            query=req.query,
            chunks=retrieval_result["retrieved_chunks"],
            top_n=5
        )

        # 3. Formulate provenance citations
        citations = citation_service.format_citations(ranked_chunks)

        # 4. Generate Answer
        answer = answer_service.generate_answer(req.query, ranked_chunks, citations)

        return QueryResponse(
            answer=answer,
            citations=citations,
            graph_visualization=retrieval_result["graph_visualization"],
            has_missing_prerequisites=retrieval_result["has_missing_prerequisites"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}"
        )
