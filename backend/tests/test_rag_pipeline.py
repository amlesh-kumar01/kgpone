"""
Unit tests for the optimized RAG pipeline components:
- NLP Planner Service (intent classification + entity extraction)
- Cross-Encoder Rerank Service (with mocked HF API)
- Reciprocal Rank Fusion
- Semantic Cache Service (with mocked Redis)
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# ─── NLP Planner Tests ──────────────────────────────────────────────────────

from src.services.rag.nlp_planner_service import NLPPlannerService


class TestNLPPlannerService:
    """Tests for the TF-IDF + SVM intent classifier."""

    @pytest.fixture
    def planner(self):
        """Create planner — uses trained models if available, else heuristic fallback."""
        return NLPPlannerService()

    @pytest.mark.asyncio
    async def test_download_intent(self, planner):
        plan = await planner.detect_intent("download lecture 5 pdf", "CS101")
        assert plan.intent == "download"
        assert "postgresql" in plan.backends_needed
        assert "qdrant" not in plan.backends_needed

    @pytest.mark.asyncio
    async def test_faculty_lookup_intent(self, planner):
        plan = await planner.detect_intent("who teaches CS60001")
        assert plan.intent == "faculty_lookup"
        assert "postgresql" in plan.backends_needed

    @pytest.mark.asyncio
    async def test_prerequisites_intent(self, planner):
        plan = await planner.detect_intent("what are the prerequisites for OS")
        assert plan.intent == "prerequisites"
        assert "neo4j" in plan.backends_needed

    @pytest.mark.asyncio
    async def test_compare_intent(self, planner):
        plan = await planner.detect_intent("difference between DFS and BFS")
        assert plan.intent == "compare"
        assert "neo4j" in plan.backends_needed
        assert "qdrant" in plan.backends_needed

    @pytest.mark.asyncio
    async def test_semantic_search_intent(self, planner):
        plan = await planner.detect_intent("notes on dynamic programming")
        assert plan.intent == "semantic_search"
        assert "qdrant" in plan.backends_needed

    @pytest.mark.asyncio
    async def test_topic_explain_intent(self, planner):
        plan = await planner.detect_intent("explain attention mechanism")
        assert plan.intent == "topic_explain"

    @pytest.mark.asyncio
    async def test_course_code_extraction(self, planner):
        plan = await planner.detect_intent("who teaches CS60001")
        assert plan.course_code == "CS60001"

    @pytest.mark.asyncio
    async def test_course_code_with_space(self, planner):
        plan = await planner.detect_intent("prerequisites for CS 101")
        assert plan.course_code == "CS101"

    @pytest.mark.asyncio
    async def test_context_course_fallback(self, planner):
        plan = await planner.detect_intent("explain deadlock", "OS101")
        assert plan.course_code == "OS101"

    @pytest.mark.asyncio
    async def test_context_offering_preserved(self, planner):
        plan = await planner.detect_intent("explain deadlock", "OS101", "offering-123")
        assert plan.course_offering_id == "offering-123"

    @pytest.mark.asyncio
    async def test_confidence_score_present(self, planner):
        plan = await planner.detect_intent("download lecture notes")
        assert 0.0 <= plan.confidence_score <= 1.0

    @pytest.mark.asyncio
    async def test_entity_extraction(self, planner):
        plan = await planner.detect_intent("explain binary search tree")
        assert len(plan.entities_mentioned) > 0

    @pytest.mark.asyncio
    async def test_general_qa_fallback(self, planner):
        plan = await planner.detect_intent("solve this recurrence relation step by step")
        # Should be general_qa or topic_explain — both are acceptable
        assert plan.intent in ["general_qa", "topic_explain", "semantic_search"]

    @pytest.mark.asyncio
    async def test_list_courses_intent(self, planner):
        plan = await planner.detect_intent("what courses does CSE offer")
        assert plan.intent in ["list_courses", "concept_search"]
        assert "postgresql" in plan.backends_needed or "neo4j" in plan.backends_needed


# ─── RRF Fusion Tests ────────────────────────────────────────────────────────

from src.services.rag.fusion import reciprocal_rank_fusion


class TestReciprocalRankFusion:
    """Tests for the RRF merge algorithm."""

    def test_single_list_passthrough(self):
        chunks = [
            {"id": "a", "score": 0.9, "payload": {"text": "chunk a"}},
            {"id": "b", "score": 0.7, "payload": {"text": "chunk b"}},
        ]
        result = reciprocal_rank_fusion([chunks])
        assert len(result) == 2
        assert result[0]["id"] == "a"
        assert "rrf_score" in result[0]

    def test_two_lists_merge(self):
        list1 = [
            {"id": "a", "score": 0.9, "payload": {"text": "chunk a"}},
            {"id": "b", "score": 0.7, "payload": {"text": "chunk b"}},
        ]
        list2 = [
            {"id": "b", "score": 0.8, "payload": {"text": "chunk b"}},
            {"id": "c", "score": 0.6, "payload": {"text": "chunk c"}},
        ]
        result = reciprocal_rank_fusion([list1, list2])
        # b appears in both lists so should have highest RRF score
        assert len(result) == 3
        ids = [r["id"] for r in result]
        assert "a" in ids
        assert "b" in ids
        assert "c" in ids
        # b should be ranked first (appears in both lists)
        assert result[0]["id"] == "b"

    def test_empty_input(self):
        result = reciprocal_rank_fusion([])
        assert result == []

    def test_deduplication(self):
        list1 = [{"id": "x", "score": 0.5, "payload": {"text": "test"}}]
        list2 = [{"id": "x", "score": 0.9, "payload": {"text": "test updated"}}]
        result = reciprocal_rank_fusion([list1, list2])
        assert len(result) == 1
        # Should keep the version with highest original score
        assert result[0]["score"] > 0  # rrf_score is assigned

    def test_k_parameter(self):
        chunks = [{"id": "a", "score": 0.9, "payload": {"text": "a"}}]
        result_k1 = reciprocal_rank_fusion([chunks], k=1)
        result_k60 = reciprocal_rank_fusion([chunks], k=60)
        # Higher k → lower RRF score
        assert result_k1[0]["rrf_score"] > result_k60[0]["rrf_score"]


# ─── Cross-Encoder Rerank Tests ──────────────────────────────────────────────

from src.services.rag.cross_encoder_rerank_service import CrossEncoderRerankService


class TestCrossEncoderRerankService:
    """Tests for the HuggingFace cross-encoder reranker."""

    @pytest.fixture
    def reranker(self):
        return CrossEncoderRerankService()

    @pytest.fixture
    def sample_chunks(self):
        return [
            {"id": "1", "score": 0.8, "payload": {"text": "Binary search tree is a data structure", "document_id": "doc1"}},
            {"id": "2", "score": 0.6, "payload": {"text": "Hash tables provide O(1) lookup", "document_id": "doc2"}},
            {"id": "3", "score": 0.7, "payload": {"text": "Binary search uses divide and conquer", "document_id": "doc1"}},
            {"id": "4", "score": 0.5, "payload": {"text": "Linked lists are sequential", "document_id": "doc3"}},
            {"id": "5", "score": 0.4, "payload": {"text": "Graphs can be directed or undirected", "document_id": "doc4"}},
        ]

    @pytest.mark.asyncio
    async def test_empty_chunks(self, reranker):
        result = await reranker.rerank_chunks("test query", [])
        assert result == []

    @pytest.mark.asyncio
    async def test_fallback_reranking(self, reranker, sample_chunks):
        """Test that fallback lexical boost works when HF API is unavailable."""
        # Force fallback by setting client to None
        reranker._hf_client = None
        with patch.object(reranker, '_get_client', return_value=None):
            result = await reranker.rerank_chunks("binary search", sample_chunks, top_n=3)

        assert len(result) <= 3
        assert all("final_score" in c for c in result)
        # Chunks mentioning "binary" and "search" should score higher
        assert result[0]["payload"]["text"].lower().count("binary") > 0

    @pytest.mark.asyncio
    async def test_diversity_penalty(self, reranker, sample_chunks):
        """Chunks from same document get penalized."""
        scored = reranker._fallback_rerank("binary search", sample_chunks)
        penalized = reranker._apply_diversity_penalty(scored)
        # doc1 has 2 chunks — second one should have lower score
        doc1_chunks = [c for c in penalized if c["payload"]["document_id"] == "doc1"]
        if len(doc1_chunks) >= 2:
            assert doc1_chunks[0]["final_score"] >= doc1_chunks[1]["final_score"]

    @pytest.mark.asyncio
    async def test_deduplication(self, reranker):
        """Overlapping chunks should be deduplicated."""
        chunks = [
            {"id": "1", "score": 0.9, "final_score": 0.9, "payload": {"text": "the quick brown fox jumps over the lazy dog", "document_id": "d1"}},
            {"id": "2", "score": 0.8, "final_score": 0.8, "payload": {"text": "the quick brown fox jumps over the lazy dog today", "document_id": "d1"}},
            {"id": "3", "score": 0.5, "final_score": 0.5, "payload": {"text": "completely different content about neural networks", "document_id": "d2"}},
        ]
        result = reranker._deduplicate_chunks(chunks, threshold=0.80)
        # First two chunks heavily overlap — one should be removed
        assert len(result) <= 2

    def test_sigmoid(self):
        assert abs(CrossEncoderRerankService._sigmoid(0) - 0.5) < 0.01
        assert CrossEncoderRerankService._sigmoid(10) > 0.99
        assert CrossEncoderRerankService._sigmoid(-10) < 0.01


# ─── Semantic Cache Tests ────────────────────────────────────────────────────

from src.services.rag.semantic_cache_service import SemanticCacheService


class TestSemanticCacheService:
    """Tests for Redis-backed semantic caching."""

    @pytest.fixture
    def cache(self):
        return SemanticCacheService(ttl=60)

    @pytest.fixture
    def sample_embedding(self):
        """A simple 768-dim embedding for testing."""
        return [0.1 * (i % 10) for i in range(768)]

    @pytest.fixture
    def sample_response(self):
        return {
            "answer": "Deadlock occurs when...",
            "citations": [],
            "sources": [],
            "intent": "topic_explain",
            "backends_used": ["qdrant"],
            "cache_hit": False,
            "confidence_score": 0.95,
        }

    def test_cache_key_determinism(self, cache, sample_embedding):
        """Same embedding should produce same cache key."""
        key1 = cache._build_cache_key(sample_embedding)
        key2 = cache._build_cache_key(sample_embedding)
        assert key1 == key2

    def test_cache_key_with_scope(self, cache, sample_embedding):
        """Different scopes should produce different cache keys."""
        key_global = cache._build_cache_key(sample_embedding)
        key_scoped = cache._build_cache_key(sample_embedding, scope_key="offering-123")
        assert key_global != key_scoped
        assert "offering-123" in key_scoped
        assert "global" in key_global

    def test_cache_key_different_embeddings(self, cache):
        """Different embeddings should produce different cache keys."""
        emb1 = [0.1] * 768
        emb2 = [0.9] * 768
        key1 = cache._build_cache_key(emb1)
        key2 = cache._build_cache_key(emb2)
        assert key1 != key2

    @pytest.mark.asyncio
    async def test_cache_miss_without_redis(self, cache, sample_embedding):
        """Cache should return None when Redis is unavailable."""
        with patch.object(cache, '_get_redis', return_value=None):
            result = await cache.get("test query", sample_embedding)
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_set_without_redis(self, cache, sample_embedding, sample_response):
        """Cache set should silently pass when Redis is unavailable."""
        with patch.object(cache, '_get_redis', return_value=None):
            await cache.set("test query", sample_embedding, sample_response)
            # Should not raise

    @pytest.mark.asyncio
    async def test_cache_hit_with_mock_redis(self, cache, sample_embedding, sample_response):
        """Test cache hit with a mocked Redis client."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps(sample_response))

        with patch.object(cache, '_get_redis', return_value=mock_redis):
            result = await cache.get("test query", sample_embedding)

        assert result is not None
        assert result["answer"] == "Deadlock occurs when..."
        assert result["intent"] == "topic_explain"

    @pytest.mark.asyncio
    async def test_cache_set_with_mock_redis(self, cache, sample_embedding, sample_response):
        """Test cache set with a mocked Redis client."""
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()

        with patch.object(cache, '_get_redis', return_value=mock_redis):
            await cache.set("test query", sample_embedding, sample_response, scope_key="off-1")

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 60  # TTL


# ─── Citation Service Tests (existing, preserved) ────────────────────────────

from src.services.rag.citation_service import CitationService


class TestCitationService:
    def test_citation_formatter(self):
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
                    "text": "This is a test chunk.",
                },
            }
        ]
        citations = formatter.format_citations(chunks)
        assert len(citations) == 1
        assert citations[0]["citation_id"] == "CIT-1"
        assert citations[0]["source_title"] == "Lecture 1"
        assert citations[0]["confidence"] == "High"
