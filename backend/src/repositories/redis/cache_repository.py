import json
import logging
from typing import Any, Optional
from src.infrastructure.redis_cache import get_sync_redis_cache_client

logger = logging.getLogger("cache_repository")

class CacheRepository:
    """
    A synchronous repository for interacting with Redis cache.
    Handles serialization/deserialization of JSON data.
    """
    
    def __init__(self):
        self.client = get_sync_redis_cache_client()
        self.use_fallback = False
        if self.client is None:
            self.use_fallback = True

    def get(self, key: str) -> Optional[Any]:
        if self.use_fallback:
            return None
            
        try:
            cached_data = self.client.get(key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Cache get failed for key {key}: {e}")
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        if self.use_fallback:
            return False
            
        try:
            serialized_value = json.dumps(value)
            if ttl:
                self.client.setex(key, ttl, serialized_value)
            else:
                self.client.set(key, serialized_value)
            return True
        except Exception as e:
            logger.warning(f"Cache set failed for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        if self.use_fallback:
            return False
            
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete failed for key {key}: {e}")
            return False

    def delete_pattern(self, pattern: str) -> bool:
        if self.use_fallback:
            return False
            
        try:
            # Use SCAN instead of KEYS to avoid blocking Redis
            cursor = '0'
            while cursor != 0:
                cursor, keys = self.client.scan(cursor=cursor, match=pattern, count=100)
                if keys:
                    self.client.delete(*keys)
            return True
        except Exception as e:
            logger.warning(f"Cache delete_pattern failed for pattern {pattern}: {e}")
            return False
