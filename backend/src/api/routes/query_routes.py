from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from typing import List
import json
import time
import logging
from src.utils.logger import setup_logger

logger = setup_logger("query_routes")
from src.schemas.query_schema import QueryRequest, QueryResponse, SearchResult
from src.schemas.response_schema import StandardResponse
from src.services.rag.nlp_planner_service import NLPPlannerService
from src.services.rag.retrieval_service import RetrievalService
from src.services.rag.cross_encoder_rerank_service import CrossEncoderRerankService
from src.services.rag.citation_service import CitationService
from src.services.rag.answer_service import AnswerService
from src.services.rag.semantic_cache_service import SemanticCacheService
from src.services.ingestion.embedding.llm_embedding import LLMEmbedder
from src.repositories.qdrant.vector_repository import QdrantRepository
from src.infrastructure.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/query", tags=["Query & RAG"])

def get_rag_services(db: Session = Depends(get_db)):
    planner = NLPPlannerService()
    embedder = LLMEmbedder()
    vector_repo = QdrantRepository()
    retriever = RetrievalService(embedder=embedder, vector_store=vector_repo, db=db)
    reranker = CrossEncoderRerankService()
    citation_formatter = CitationService()
    answer_generator = AnswerService()
    semantic_cache = SemanticCacheService()
    
    return {
        "planner": planner,
        "retriever": retriever,
        "reranker": reranker,
        "citation_formatter": citation_formatter,
        "answer_generator": answer_generator,
        "embedder": embedder,
        "semantic_cache": semantic_cache,
    }

@router.post("/ask", response_model=StandardResponse[QueryResponse])
async def ask_question(req: QueryRequest, services: dict = Depends(get_rag_services)):
    """Full hybrid RAG pipeline: Cache Check -> Plan -> Retrieve -> Rerank -> Answer"""
    query = req.query
    course_code = req.course_code
    course_offering_id = req.course_offering_id
    
    # 0. Semantic Cache Check
    cache_hit = False
    semantic_cache = services["semantic_cache"]
    embedder = services["embedder"]
    
    # Generate embedding for cache lookup (reused later for retrieval)
    query_vectors = await embedder.embed([query])
    query_embedding = query_vectors[0] if query_vectors else []
    
    if query_embedding:
        scope_key = course_offering_id if course_offering_id else None
        cached = await semantic_cache.get(query, query_embedding, scope_key=scope_key)
        if cached:
            # Return cached response directly
            cached["cache_hit"] = True
            return StandardResponse(
                status="success",
                message="Query answered from cache",
                data=QueryResponse(**cached),
            )
    
    # 1. Plan
    plan = await services["planner"].detect_intent(query, course_code, course_offering_id)
    
    # 2. Retrieve
    context = await services["retriever"].retrieve_context(query, plan)
    
    # 3. Rerank
    reranked_chunks = await services["reranker"].rerank_chunks(query, context["retrieved_chunks"], top_n=3)
    
    # 4. Format Citations if requested
    citations = []
    if req.use_citations:
        citations = services["citation_formatter"].format_citations(reranked_chunks)
    
    # 5. Generate Answer
    answer = services["answer_generator"].generate_answer(query, reranked_chunks, citations, use_citations=req.use_citations)
    
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
        backends_used=plan.backends_needed,
        cache_hit=False,
        confidence_score=plan.confidence_score,
    )
    
    # 6. Cache the response for future identical queries
    if query_embedding:
        scope_key = course_offering_id if course_offering_id else None
        try:
            await semantic_cache.set(
                query,
                query_embedding,
                response_data.model_dump(),
                scope_key=scope_key,
            )
        except Exception:
            pass  # Cache write failure is non-critical
    
    return StandardResponse(
        status="success",
        message="Query answered successfully",
        data=response_data
    )

@router.post("/ask_stream")
async def ask_question_stream(req: QueryRequest, services: dict = Depends(get_rag_services)):
    """SSE endpoint for streaming the RAG answer."""
    query = req.query
    course_code = req.course_code
    course_offering_id = req.course_offering_id
    t0 = time.time()
    plan = await services["planner"].detect_intent(query, course_code, course_offering_id)
    t1 = time.time()
    logger.info(f"[PERF] Planner took: {t1 - t0:.4f}s")
    
    context = await services["retriever"].retrieve_context(query, plan)
    t2 = time.time()
    logger.info(f"[PERF] Retriever took: {t2 - t1:.4f}s")
    
    reranked_chunks = await services["reranker"].rerank_chunks(query, context["retrieved_chunks"], top_n=3)
    t3 = time.time()
    logger.info(f"[PERF] Reranker took: {t3 - t2:.4f}s")
    
    citations = []
    if req.use_citations:
        citations = services["citation_formatter"].format_citations(reranked_chunks)
    t4 = time.time()
    logger.info(f"[PERF] Citations took: {t4 - t3:.4f}s")
        
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
            
    async def event_generator():
        # Stream the text chunks
        async for text_chunk in services["answer_generator"].generate_answer_stream(query, reranked_chunks, req.use_citations):
            yield f"data: {json.dumps({'type': 'chunk', 'content': text_chunk})}\n\n"
            
        # Stream the final metadata block
        metadata = {
            "type": "metadata",
            "citations": [c.model_dump() for c in citations] if citations and hasattr(citations[0], "model_dump") else citations,
            "sources": sources,
            "intent": plan.intent,
            "backends_used": plan.backends_needed,
            "graph_context": context.get("graph_visualization")
        }
        # handle pydantic dumping for citations if it returns dicts, format_citations actually returns a list of CitationRead models usually... Wait, format_citations returns dicts in python.
        yield f"data: {json.dumps(metadata)}\n\n"
        
    return StreamingResponse(event_generator(), media_type="text/event-stream")

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
