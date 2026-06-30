"""
Redis-backed Semantic Cache for the RAG pipeline.

Caches full RAG responses (answer + citations + metadata) keyed by
a hash of the query embedding vector. Semantically identical queries
(e.g. "Explain deadlock" ≈ "What is a deadlock?") produce similar embeddings,
so they hit the same cache bucket.

Cache scope:
- If course_offering_id is present, the cache is scoped per offering
- Otherwise, the cache is global

Provides a placeholder interface for a future local sentence-transformer
fallback (not implemented to avoid GPU/CPU load).
"""

import hashlib
import json
import logging
from typing import Any, Optional

from src.config.settings import Settings
from src.infrastructure.redis_cache import get_redis_cache_client
from src.services.rag.base import BaseSemanticCache

logger = logging.getLogger("semantic_cache_service")

# Prefix for all cache keys to avoid collision with other Redis data
_CACHE_PREFIX = "rag_cache:"


class SemanticCacheService(BaseSemanticCache):
    """
    Redis-backed semantic cache using embedding hash keys.
    """

    def __init__(self, ttl: int | None = None):
        self.ttl = ttl or Settings.SEMANTIC_CACHE_TTL
        self._redis = None  # Lazy init

    async def _get_redis(self):
        """Lazy-initialize the Redis client."""
        if self._redis is None:
            self._redis = get_redis_cache_client()
        return self._redis

    async def get(
        self,
        query: str,
        query_embedding: list[float],
        scope_key: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Looks up a cached response for the query.
        Returns the cached dict if found, None otherwise.
        """
        redis = await self._get_redis()
        if redis is None:
            return None

        cache_key = self._build_cache_key(query_embedding, scope_key)

        try:
            cached = await redis.get(cache_key)
            if cached:
                logger.info(f"Semantic cache HIT for key: {cache_key[:40]}...")
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}")

        return None

    async def set(
        self,
        query: str,
        query_embedding: list[float],
        response: dict[str, Any],
        scope_key: Optional[str] = None,
    ) -> None:
        """Stores a response in the cache with TTL."""
        redis = await self._get_redis()
        if redis is None:
            return

        cache_key = self._build_cache_key(query_embedding, scope_key)

        try:
            serialized = json.dumps(response, default=str)
            await redis.setex(cache_key, self.ttl, serialized)
            logger.info(f"Semantic cache SET for key: {cache_key[:40]}... (TTL={self.ttl}s)")
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")

    async def invalidate(self, scope_key: Optional[str] = None) -> int:
        """
        Invalidates cached entries.
        If scope_key is provided, deletes only entries for that scope.
        Otherwise flushes all RAG cache entries.
        """
        redis = await self._get_redis()
        if redis is None:
            return 0

        try:
            if scope_key:
                pattern = f"{_CACHE_PREFIX}{scope_key}:*"
            else:
                pattern = f"{_CACHE_PREFIX}*"

            # Scan and delete matching keys
            count = 0
            async for key in redis.scan_iter(match=pattern, count=100):
                await redis.delete(key)
                count += 1

            logger.info(f"Invalidated {count} cache entries (pattern: {pattern})")
            return count
        except Exception as e:
            logger.warning(f"Cache invalidation failed: {e}")
            return 0

    def _build_cache_key(
        self,
        query_embedding: list[float],
        scope_key: Optional[str] = None,
    ) -> str:
        """
        Builds a deterministic cache key from the query embedding.

        Uses the first 64 dimensions, quantized to 2 decimal places,
        to create a stable hash. Similar queries produce similar embeddings,
        and the quantization ensures near-identical vectors hit the same bucket.
        """
        # Take first 64 floats and quantize to 2 decimal places
        truncated = [round(v, 2) for v in query_embedding[:64]]
        embedding_str = ",".join(str(v) for v in truncated)

        # SHA-256 hash for compact key
        hash_hex = hashlib.sha256(embedding_str.encode("utf-8")).hexdigest()[:16]

        if scope_key:
            return f"{_CACHE_PREFIX}{scope_key}:{hash_hex}"
        return f"{_CACHE_PREFIX}global:{hash_hex}"


# ─── Future Local Fallback Interface ─────────────────────────────────────────
# Placeholder for a local sentence-transformer based cache that could compute
# embeddings locally for cache key generation (without calling the embedding API).
# NOT implemented now to avoid GPU/CPU load overhead.
#
# class LocalEmbeddingCacheService(BaseSemanticCache):
#     """
#     Uses a local sentence-transformer model (e.g. all-MiniLM-L6-v2) to
#     compute cache-key embeddings without calling the external embedding API.
#     """
#     def __init__(self):
#         from sentence_transformers import SentenceTransformer
#         self.model = SentenceTransformer("all-MiniLM-L6-v2")
#         ...
