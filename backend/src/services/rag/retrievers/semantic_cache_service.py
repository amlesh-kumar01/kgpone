"""
Redis-backed Semantic Cache for the RAG pipeline.

Caches full RAG responses (answer + citations + metadata) keyed by
a hash of the query embedding vector. Semantically identical queries
(e.g. "Explain deadlock" ≈ "What is a deadlock?") produce similar embeddings,
so they hit the same cache bucket.

Cache scope:
- If study_unit_id is present, the cache is scoped per offering
- Otherwise, the cache is global

Provides a placeholder interface for a future local sentence-transformer
fallback (not implemented to avoid GPU/CPU load).
"""

import hashlib
import json
import logging
import math
from typing import Any, Optional
import uuid

from src.config.settings import Settings
from src.infrastructure.redis_cache import get_redis_cache_client
from src.services.rag.base import BaseSemanticCache

logger = logging.getLogger("semantic_cache_service")

# Prefix for all cache keys to avoid collision with other Redis data
_CACHE_PREFIX = "rag_cache:"

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Computes cosine similarity between two vectors."""
    if len(v1) != len(v2):
        return 0.0
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


class SemanticCacheService(BaseSemanticCache):
    """
    Redis-backed semantic cache using exact cosine similarity.
    Retrieves all cached embeddings for the given scope via MGET and calculates 
    similarity locally. Returns the best match if it exceeds the similarity threshold.
    """

    def __init__(self, ttl: int | None = None, similarity_threshold: float = 0.94):
        self.ttl = ttl or Settings.SEMANTIC_CACHE_TTL
        self.similarity_threshold = similarity_threshold
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
        Looks up a cached response for the query by evaluating cosine similarity
        against all cached queries in the current scope.
        """
        redis = await self._get_redis()
        if redis is None:
            return None

        # Determine the pattern and index set for the current scope
        scope = scope_key or 'global'
        index_key = f"{_CACHE_PREFIX}index:{scope}"

        try:
            # 1. Fetch all keys in this scope using O(1) SMEMBERS instead of slow SCAN
            keys = await redis.smembers(index_key)
            keys = list(keys)
            
            if not keys:
                return None

            # 2. Fetch all values (these contain both the embedding and the response payload)
            values = await redis.mget(keys)

            best_match = None
            highest_sim = -1.0

            # 3. Find the most semantically similar cached query
            for key, val in zip(keys, values):
                if not val:
                    continue
                data = json.loads(val)
                cached_embedding = data.get("query_embedding")
                if not cached_embedding:
                    continue

                sim = cosine_similarity(query_embedding, cached_embedding)
                if sim > highest_sim:
                    highest_sim = sim
                    best_match = data.get("response")
                    best_key = key

            # 4. Return if threshold is met
            if best_match and highest_sim >= self.similarity_threshold:
                logger.info(f"Semantic cache HIT (Sim={highest_sim:.3f}) for scope '{scope_key or 'global'}'")
                return best_match

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
        """Stores a response in the cache with its embedding and TTL."""
        redis = await self._get_redis()
        if redis is None:
            return

        # Generate a unique key for this entry
        unique_id = uuid.uuid4().hex[:12]
        cache_key = f"{_CACHE_PREFIX}{scope_key or 'global'}:{unique_id}"

        # Package the embedding alongside the response payload
        payload = {
            "query": query,
            "query_embedding": query_embedding,
            "response": response
        }

        scope = scope_key or 'global'
        index_key = f"{_CACHE_PREFIX}index:{scope}"

        try:
            serialized = json.dumps(payload, default=str)
            
            # Use a pipeline to set the key and add it to our O(1) index set atomically
            pipe = redis.pipeline()
            pipe.setex(cache_key, self.ttl, serialized)
            pipe.sadd(index_key, cache_key)
            # Set the TTL of the index set itself to match the longest-living key
            pipe.expire(index_key, self.ttl)
            await pipe.execute()
            
            logger.info(f"Semantic cache SET for scope '{scope}' (TTL={self.ttl}s)")
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
            scope = scope_key or 'global'
            index_key = f"{_CACHE_PREFIX}index:{scope}"
            
            keys = await redis.smembers(index_key)
            count = 0
            
            if keys:
                pipe = redis.pipeline()
                for key in keys:
                    pipe.delete(key)
                pipe.delete(index_key)
                await pipe.execute()
                count = len(keys)

            logger.info(f"Invalidated {count} cache entries for scope: {scope}")
            return count
        except Exception as e:
            logger.warning(f"Cache invalidation failed: {e}")
            return 0
