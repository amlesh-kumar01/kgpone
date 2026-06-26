import logging
from typing import Any
from pydantic import BaseModel
from src.infrastructure.llm_factory import LLMFactory
from src.services.rag.base import BaseReranker
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger("rerank_service")

class ChunkScore(BaseModel):
    relevance_score: float

class RerankService(BaseReranker):
    def __init__(self, model_name: str | None = None):
        self.factory = LLMFactory()
        try:
            llm = self.factory.get_llm(model_name)
            self.structured_llm = llm.with_structured_output(ChunkScore)
        except Exception as e:
            logger.error(f"Failed to initialize Rerank LLM: {e}")
            self.structured_llm = None
            
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """Evaluate the relevance of the text chunk to the user's query.
Score the relevance from 0.0 (completely irrelevant) to 1.0 (highly relevant).
Return ONLY the structured output with relevance_score."""),
            ("user", "Query: '{query}'\nText Chunk: '{text}'")
        ])

    async def rerank_chunks(self, query: str, chunks: list[dict[str, Any]], top_n: int = 5) -> list[dict[str, Any]]:
        """
        Reranks chunks by evaluating relevance to the query using Langchain LLM.
        If LLM fails, falls back to lexical boost.
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
            
            if not self.structured_llm:
                final_score = self._fallback_score(query, text, base_score)
            else:
                try:
                    # LLM Scoring
                    chain = self.prompt_template | self.structured_llm
                    result: ChunkScore = await chain.ainvoke({
                        "query": query,
                        "text": text[:1000]
                    })
                    
                    relevance = float(result.relevance_score)
                    # Combine vector score and LLM relevance
                    final_score = (base_score * 0.3) + (relevance * 0.7)
                except Exception as e:
                    logger.warning(f"LLM reranking failed for chunk {i}, falling back: {e}")
                    final_score = self._fallback_score(query, text, base_score)
                
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
        
    def _fallback_score(self, query: str, text: str, base_score: float) -> float:
        query_words = [w.lower() for w in query.split() if len(w) > 3]
        matches = sum(1 for w in query_words if w in text.lower())
        boost = 1.0 + (matches * 0.1)
        return min(base_score * boost, 1.0)
