import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from src.services.rag.planner_service import PlannerService, QueryPlan
from src.services.rag.rerank_service import RerankService
from src.services.rag.citation_service import CitationService
from src.services.rag.answer_service import AnswerService

@pytest.mark.asyncio
async def test_planner_detects_download_intent():
    planner = PlannerService(model_name="gemini-2.5-flash")
    # Mocking the model to avoid hitting real API in unit tests
    planner.model.generate_content_async = AsyncMock()
    planner.model.generate_content_async.return_value.text = '{"intent": "download", "backends_needed": ["postgresql"], "entities_mentioned": []}'
    
    plan = await planner.detect_intent("download lecture 5 pdf", "CS101")
    
    assert plan.intent == "download"
    assert "postgresql" in plan.backends_needed
    assert "qdrant" not in plan.backends_needed

@pytest.mark.asyncio
async def test_planner_detects_compare_intent():
    planner = PlannerService(model_name="gemini-2.5-flash")
    planner.model.generate_content_async = AsyncMock()
    planner.model.generate_content_async.return_value.text = '{"intent": "compare", "backends_needed": ["neo4j", "qdrant"], "entities_mentioned": ["DFS", "BFS"]}'
    
    plan = await planner.detect_intent("Compare DFS and BFS", "CS101")
    
    assert plan.intent == "compare"
    assert "qdrant" in plan.backends_needed
    assert "neo4j" in plan.backends_needed
    assert "DFS" in plan.entities_mentioned

def test_citation_formatter():
    formatter = CitationService()
    chunks = [
        {
            "id": "c1",
            "score": 0.9,
            "final_score": 0.95,
            "payload": {
                "document_id": "doc1",
                "title": "Lecture 1",
                "course_code": "CS101",
                "academic_year": "2026",
                "text": "This is a test chunk."
            }
        }
    ]
    citations = formatter.format_citations(chunks)
    assert len(citations) == 1
    assert citations[0]["citation_id"] == "CIT-1"
    assert citations[0]["source_title"] == "Lecture 1"
    assert citations[0]["confidence"] == "High"
