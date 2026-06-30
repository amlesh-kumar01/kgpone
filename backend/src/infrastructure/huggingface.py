"""
Singleton async HTTP client factory for the HuggingFace Serverless Inference API.
Used for cross-encoder reranking without running models locally.
"""

import logging
from typing import Optional

import httpx

from src.config.settings import Settings

logger = logging.getLogger("huggingface_infra")

_client: Optional[httpx.AsyncClient] = None


def get_huggingface_client() -> Optional[httpx.AsyncClient]:
    """Returns a singleton async HTTP client for HuggingFace Inference API."""
    global _client
    if _client is None:
        api_key = Settings.HUGGINGFACE_API_KEY
        if not api_key:
            logger.warning(
                "HUGGINGFACE_API_KEY not set. Cross-encoder reranking will use fallback."
            )
            return None

        _client = httpx.AsyncClient(
            base_url="https://api-inference.huggingface.co",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=httpx.Timeout(30.0, connect=10.0),
        )
        logger.info("HuggingFace Inference API client initialized.")

    return _client


async def close_huggingface_client():
    """Closes the singleton client gracefully (call on app shutdown)."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
        logger.info("HuggingFace client closed.")
