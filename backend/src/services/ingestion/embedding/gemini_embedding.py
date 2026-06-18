import asyncio
from typing import Optional
from google import genai
from google.genai import types
from src.config.settings import Settings
from src.services.ingestion.embedding.base import BaseEmbedder

class GeminiEmbedder(BaseEmbedder):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or Settings().GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-embedding-001"

    async def embed(self, chunks: list[str]) -> list[list[float]]:
        # The genai library handles batch embeddings natively if we pass a list of strings
        # We run it in a threadpool to not block the async event loop if it's synchronous
        result = await asyncio.to_thread(
            self.client.models.embed_content,
            model=self.model_name,
            contents=chunks,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=768
            )
        )
        if not result or not result.embeddings:
            return []
        return [embedding.values for embedding in result.embeddings]
