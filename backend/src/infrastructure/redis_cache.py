"""
Redis client singleton for the semantic query cache.
Uses a separate DB index from the Celery broker to prevent interference.
"""

import logging
from typing import Optional

import redis.asyncio as aioredis

from src.config.settings import Settings

logger = logging.getLogger("redis_cache")

_cache_client: Optional[aioredis.Redis] = None


def get_redis_cache_client() -> Optional[aioredis.Redis]:
    """Returns a singleton async Redis client for semantic caching."""
    global _cache_client
    if _cache_client is None:
        try:
            _cache_client = aioredis.from_url(
                Settings.REDIS_CACHE_URL,
                decode_responses=True,
                socket_connect_timeout=3.0,
            )
            logger.info(f"Redis cache client initialized at {Settings.REDIS_CACHE_URL}")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis cache client: {e}")
            _cache_client = None
    return _cache_client


async def close_redis_cache_client():
    """Closes the singleton Redis client gracefully."""
    global _cache_client
    if _cache_client is not None:
        await _cache_client.aclose()
        _cache_client = None
        logger.info("Redis cache client closed.")
