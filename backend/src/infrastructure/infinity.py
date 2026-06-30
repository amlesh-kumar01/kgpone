"""
Singleton async HTTP client factory for the local Infinity Server.
Used for local cross-encoder reranking.
"""

import logging
from typing import Optional

import httpx

from src.config.settings import Settings

logger = logging.getLogger("infinity_infra")

_client: Optional[httpx.AsyncClient] = None


def get_infinity_client() -> httpx.AsyncClient:
    """Returns a singleton async HTTP client for the local Infinity server."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=Settings.INFINITY_URL,
            timeout=httpx.Timeout(120.0, connect=10.0),
        )
        logger.info(f"Local Infinity client initialized with URL: {Settings.INFINITY_URL}")

    return _client


async def close_infinity_client():
    """Closes the singleton client gracefully (call on app shutdown)."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
        logger.info("Local Infinity client closed.")
