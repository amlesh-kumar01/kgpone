import asyncio
import logging
from src.services.ingestion.embedding.base import BaseEmbedder
from src.infrastructure.llm_factory import LLMFactory

logger = logging.getLogger("llm_embedding")

class LLMEmbedder(BaseEmbedder):
    def __init__(self):
        self.factory = LLMFactory()
        try:
            self.embedder = self.factory.get_embeddings()
        except Exception as e:
            logger.error(f"Failed to initialize embeddings from LLMFactory: {e}. Falling back to offline text hashing.")
            self.embedder = None
            self.use_fallback = True
        else:
            self.use_fallback = False

    async def embed(self, chunks: list[str]) -> list[list[float]]:
        if self.use_fallback or not self.embedder:
            import hashlib
            vectors = []
            for chunk in chunks:
                h = hashlib.sha256(chunk.encode("utf-8")).digest()
                # Create a 768-dimensional float vector deterministically from the hash
                vec = []
                for i in range(768):
                    val = h[i % len(h)] / 255.0
                    vec.append(val)
                vectors.append(vec)
            return vectors

        # Langchain Embeddings has an aembed_documents method
        # which batches appropriately behind the scenes.
        return await self.embedder.aembed_documents(chunks)
