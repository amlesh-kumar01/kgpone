import asyncio
import logging
from typing import Optional
from google import genai
from google.genai import types
from src.config.settings import Settings
from src.services.ingestion.embedding.base import BaseEmbedder

class GeminiEmbedder(BaseEmbedder):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or Settings.GEMINI_API_KEY
        self.use_fallback = False
        
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            logger = logging.getLogger("gemini_embedding")
            logger.warning("GEMINI_API_KEY is missing or placeholder. Using offline text hashing embedding fallback.")
            self.use_fallback = True
            self.client = None
            self.model_name = ""
        else:
            self.client = genai.Client(api_key=self.api_key)
            self.model_name = "gemini-embedding-001"

    async def embed(self, chunks: list[str]) -> list[list[float]]:
        if self.use_fallback:
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

        # Split chunks into batches of at most 100 to respect Gemini API batch limits
        batch_size = 100
        all_embeddings = []
        
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            result = await asyncio.to_thread(
                self.client.models.embed_content,
                model=self.model_name,
                contents=batch_chunks,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    output_dimensionality=768
                )
            )
            if not result or not result.embeddings:
                continue
            for embedding in result.embeddings:
                all_embeddings.append(embedding.values)
                
        return all_embeddings
