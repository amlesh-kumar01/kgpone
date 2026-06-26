from fastapi import APIRouter, Depends
from typing import List
from src.schemas.query_schema import QueryRequest, QueryResponse, SearchResult
from src.schemas.response_schema import StandardResponse
from src.services.rag.planner_service import PlannerService
from src.services.rag.retrieval_service import RetrievalService
from src.services.rag.rerank_service import RerankService
from src.services.rag.citation_service import CitationService
from src.services.rag.answer_service import AnswerService
from src.services.ingestion.embedding.llm_embedding import LLMEmbedder
from src.repositories.qdrant.vector_repository import QdrantRepository
from src.infrastructure.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/query", tags=["Query & RAG"])

def get_rag_services(db: Session = Depends(get_db)):
    planner = PlannerService()
    embedder = LLMEmbedder()
    vector_repo = QdrantRepository()
    retriever = RetrievalService(embedder=embedder, vector_store=vector_repo, db=db)
    reranker = RerankService()
    citation_formatter = CitationService()
    answer_generator = AnswerService()
    
    return {
        "planner": planner,
        "retriever": retriever,
        "reranker": reranker,
        "citation_formatter": citation_formatter,
        "answer_generator": answer_generator
    }

@router.post("/ask", response_model=StandardResponse[QueryResponse])
async def ask_question(req: QueryRequest, services: dict = Depends(get_rag_services)):
    """Full hybrid RAG pipeline: Plan -> Retrieve -> Rerank -> Answer"""
    query = req.query
    course_code = req.course_code
    course_offering_id = req.course_offering_id
    
    # 1. Plan
    plan = await services["planner"].detect_intent(query, course_code, course_offering_id)
    
    # 2. Retrieve
    context = await services["retriever"].retrieve_context(query, plan)
    
    # 3. Rerank
    reranked_chunks = await services["reranker"].rerank_chunks(query, context["retrieved_chunks"], top_n=5)
    
    # 4. Format Citations
    citations = services["citation_formatter"].format_citations(reranked_chunks)
    
    # 5. Generate Answer
    answer = services["answer_generator"].generate_answer(query, reranked_chunks, citations)
    
    # Build Sources (unique documents)
    sources = []
    seen_docs = set()
    for chunk in reranked_chunks:
        payload = chunk.get("payload", {})
        doc_id = payload.get("document_id")
        if doc_id and doc_id != "GRAPH" and doc_id not in seen_docs:
            seen_docs.add(doc_id)
            sources.append({
                "document_id": doc_id,
                "title": payload.get("document_title", payload.get("title", "Unknown")),
                "course_code": payload.get("course_code", ""),
                "doc_type": payload.get("document_type", "Notes"),
                "s3_key": payload.get("s3_key", "")
            })
            
    response_data = QueryResponse(
        answer=answer,
        citations=citations,
        sources=sources,
        graph_context=context.get("graph_visualization"),
        intent=plan.intent,
        backends_used=plan.backends_needed
    )
    
    return StandardResponse(
        status="success",
        message="Query answered successfully",
        data=response_data
    )

@router.post("/search", response_model=StandardResponse[List[SearchResult]])
async def semantic_search(req: QueryRequest, services: dict = Depends(get_rag_services)):
    """Vector-only search returning ranked document chunks"""
    query = req.query
    course_code = req.course_code
    course_offering_id = req.course_offering_id
    
    plan = await services["planner"].detect_intent(query, course_code, course_offering_id)
    # Force semantic search
    plan.backends_needed = ["qdrant"]
    
    context = await services["retriever"].retrieve_context(query, plan)
    reranked_chunks = await services["reranker"].rerank_chunks(query, context["retrieved_chunks"], top_n=10)
    
    results = []
    for chunk in reranked_chunks:
        payload = chunk.get("payload", {})
        if payload.get("document_id") and payload.get("document_id") != "GRAPH":
            results.append(SearchResult(
                document_id=payload.get("document_id"),
                title=payload.get("document_title", payload.get("title", "Unknown")),
                course_code=payload.get("course_code", ""),
                doc_type=payload.get("document_type", "Notes"),
                snippet=payload.get("content", payload.get("text", ""))[:300],
                score=chunk.get("final_score", chunk.get("score", 0.0)),
                s3_key=payload.get("s3_key", "")
            ))
            
    return StandardResponse(
        status="success",
        message="Search completed successfully",
        data=results
    )
