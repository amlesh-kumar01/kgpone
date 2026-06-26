import logging
from typing import Any
import google.generativeai as genai
from pydantic import BaseModel
from src.config.settings import Settings
from src.services.rag.base import BaseReranker

logger = logging.getLogger("rerank_service")

class ChunkScore(BaseModel):
    relevance_score: float

class RerankService(BaseReranker):
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name
        genai.configure(api_key=Settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(self.model_name)

    async def rerank_chunks(self, query: str, chunks: list[dict[str, Any]], top_n: int = 5) -> list[dict[str, Any]]:
        """
        Reranks chunks by evaluating relevance to the query using Gemini.
        If Gemini fails, falls back to lexical boost.
        """
        if not chunks:
            return []

        # Optimization: Only rerank top 20 max to save tokens/time
        chunks = chunks[:20]

        scored_chunks = []
        for i, chunk in enumerate(chunks):
            # Fallback score is original vector score + lexical boost
            base_score = chunk.get("score", 0.5)
            text = chunk["payload"].get("text", "")
            
            try:
                # LLM Scoring
                prompt = f"""
                Evaluate the relevance of the following text chunk to the user's query.
                Query: "{query}"
                Text Chunk: "{text[:1000]}"
                
                Score the relevance from 0.0 (completely irrelevant) to 1.0 (highly relevant).
                Return ONLY a JSON object with 'relevance_score'.
                """
                response = await self.model.generate_content_async(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        response_mime_type="application/json",
                        response_schema=ChunkScore,
                        temperature=0.0
                    )
                )
                import json
                result = json.loads(response.text)
                relevance = float(result.get("relevance_score", base_score))
                
                # Combine vector score and LLM relevance
                final_score = (base_score * 0.3) + (relevance * 0.7)
            except Exception as e:
                logger.warning(f"LLM reranking failed for chunk {i}, falling back: {e}")
                query_words = [w.lower() for w in query.split() if len(w) > 3]
                matches = sum(1 for w in query_words if w in text.lower())
                boost = 1.0 + (matches * 0.1)
                final_score = min(base_score * boost, 1.0)
                
            chunk["final_score"] = final_score
            scored_chunks.append(chunk)

        # Apply simple diversity penalty
        doc_counts = {}
        # Sort initially by raw final_score
        scored_chunks.sort(key=lambda x: x["final_score"], reverse=True)
        
        for chunk in scored_chunks:
            doc_id = chunk["payload"].get("document_id")
            if doc_id:
                count = doc_counts.get(doc_id, 0)
                if count > 0:
                    chunk["final_score"] *= (0.95 ** count) # 5% penalty for each subsequent chunk
                doc_counts[doc_id] = count + 1

        # Re-sort descending after penalty
        scored_chunks.sort(key=lambda x: x["final_score"], reverse=True)
        return scored_chunks[:top_n]
