import logging
from typing import Any

from src.services.rag.base import BaseReranker

logger = logging.getLogger("rerank_service")


class RerankService(BaseReranker):
    def rerank_chunks(self, query: str, chunks: list[dict[str, Any]], top_n: int = 5) -> list[dict[str, Any]]:
        """
        Reranks chunks by blending vector scores with simple term matches.
        Boosts scores of chunks containing direct keyword matches.
        """
        query_words = [w.lower() for w in query.split() if len(w) > 3]
        
        scored_chunks = []
        for chunk in chunks:
            base_score = chunk.get("score", 0.5)
            text_lower = chunk["payload"].get("text", "").lower()
            
            # Simple lexical boost
            matches = 0
            for word in query_words:
                if word in text_lower:
                    matches += 1
            
            # Boost score by 10% for each matching term
            boost = 1.0 + (matches * 0.1)
            final_score = base_score * boost
            
            chunk["final_score"] = min(final_score, 1.0)  # Keep capped at 1.0
            scored_chunks.append(chunk)

        # Sort descending by final score
        scored_chunks.sort(key=lambda x: x["final_score"], reverse=True)
        return scored_chunks[:top_n]
