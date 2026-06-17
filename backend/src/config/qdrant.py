import logging
from qdrant_client import QdrantClient
from src.config.settings import Settings

logger = logging.getLogger("qdrant_config")

_client = None

def get_qdrant_client():
    """Initializes and returns the Qdrant client singleton."""
    global _client
    if _client is None:
        try:
            _client = QdrantClient(
                url=Settings.QDRANT_URL,
                api_key=Settings.QDRANT_API_KEY or None,
                timeout=3.0
            )
            # Test connection
            _client.get_collections()
            logger.info(f"Successfully connected to Qdrant at {Settings.QDRANT_URL}")
        except Exception as e:
            logger.warning(f"Failed to connect to Qdrant at {Settings.QDRANT_URL}: {e}. Repo will fall back to offline mode.")
            _client = None
    return _client
