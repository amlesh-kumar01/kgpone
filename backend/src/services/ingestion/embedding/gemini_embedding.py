import asyncio
import google.generativeai as genai
from typing import Optional
from src.config.settings import Settings
from src.services.ingestion.embedding.base import BaseEmbedder

class GeminiEmbedder(BaseEmbedder):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or Settings().GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")
        
        genai.configure(api_key=self.api_key)
        self.model_name = "models/text-embedding-004"

    async def embed(self, chunks: list[str]) -> list[list[float]]:
        # The genai library handles batch embeddings natively if we pass a list of strings
        # We run it in a threadpool to not block the async event loop if it's synchronous
        result = await asyncio.to_thread(
            genai.embed_content,
            model=self.model_name,
            content=chunks,
            task_type="retrieval_document"
        )
        # The result is a dictionary-like object that has 'embedding'
        # If passed a list of chunks, it returns a list of embeddings
        embeddings = result.get('embedding', [])
        return embeddings
