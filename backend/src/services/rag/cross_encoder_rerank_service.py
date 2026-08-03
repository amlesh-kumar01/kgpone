"""
Cross-Encoder Reranking via HuggingFace Inference API.

Replaces per-chunk LLM calls (20 calls × ~1s = 20s) with a single batched
cross-encoder request (~200ms total).

The cross-encoder evaluates true semantic relevance by processing
[CLS] Query [SEP] Chunk simultaneously, not just vector proximity.
"""

import logging
import math
import asyncio
from typing import Any, List

from src.config.settings import Settings
from src.infrastructure.huggingface import get_huggingface_client
from src.infrastructure.infinity import get_infinity_client
from src.services.rag.base import BaseReranker

logger = logging.getLogger("cross_encoder_rerank_service")


class CrossEncoderRerankService(BaseReranker):
    """
    Reranks chunks using a cross-encoder model via HuggingFace Inference API.
    Falls back to lexical boost scoring if the API is unavailable.
    """

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or Settings.RERANKER_MODEL
        self._hf_client = None  # Lazy init
        self._infinity_client = None # Lazy init

    async def _get_client(self):
        """Lazily initializes the HF client."""
        if self._hf_client is None:
            self._hf_client = get_huggingface_client()
        return self._hf_client

    async def _get_infinity_client(self):
        """Lazily initializes the Infinity client."""
        if self._infinity_client is None:
            self._infinity_client = get_infinity_client()
        return self._infinity_client

    async def rerank_chunks(
        self, query: str, chunks: list[dict[str, Any]], top_n: int = 5
    ) -> list[dict[str, Any]]:
        """
        Reranks chunks using cross-encoder via HuggingFace API.
        Falls back to lexical boost if API is unavailable.
        """
        if not chunks:
            return []

        # Cap at 30 candidates
        chunks = chunks[:30]

        client_infinity = await self._get_infinity_client()
        scored_chunks = None

        # 1. Try Local Infinity first
        try:
            scored_chunks = await asyncio.wait_for(
                self._rerank_via_infinity(query, chunks, client_infinity),
                timeout=10.0
            )
            logger.info("Successfully used local Infinity for reranking.")
        except asyncio.TimeoutError:
            logger.warning("Local Infinity reranking timed out (>10.0s). Falling back to HF API.")
        except Exception as e:
            logger.warning(f"Local Infinity reranking failed: {repr(e)}. Falling back to HF API.")

        # 2. Try HF API if Infinity fails
        if scored_chunks is None:
            client_hf = await self._get_client()
            if client_hf is not None:
                try:
                    scored_chunks = await asyncio.wait_for(
                        self._rerank_via_api(query, chunks, client_hf),
                        timeout=3.0
                    )
                    logger.info("Successfully used HF API for reranking.")
                except asyncio.TimeoutError:
                    logger.warning("HF API reranking timed out (>3.0s). Using lexical fallback.")
                except Exception as e:
                    logger.warning(f"HF API reranking failed: {repr(e)}. Using lexical fallback.")
            else:
                logger.warning("HF client not configured. Using lexical fallback.")

        # 3. Fallback to Lexical
        if scored_chunks is None:
            logger.info("Using lexical fallback for reranking.")
            scored_chunks = self._fallback_rerank(query, chunks)

        # Apply document diversity penalty
        scored_chunks = self._apply_diversity_penalty(scored_chunks)

        # Deduplicate overlapping chunks
        scored_chunks = self._deduplicate_chunks(scored_chunks)

        # Sort descending by final_score
        scored_chunks.sort(key=lambda x: x["final_score"], reverse=True)

        return scored_chunks[:top_n]

    async def _rerank_via_infinity(
        self,
        query: str,
        chunks: list[dict[str, Any]],
        client,
    ) -> list[dict[str, Any]]:
        """
        Calls local Infinity API with query and chunk texts.
        """
        texts = [
            chunk["payload"].get("text", chunk["payload"].get("content", ""))[:500] 
            for chunk in chunks
        ]

        response = await client.post(
            "/rerank",
            json={
                "model": self.model_name,
                "query": query, 
                "documents": texts
            },
        )

        if response.status_code != 200:
            raise RuntimeError(f"Infinity API returned {response.status_code}: {response.text[:200]}")

        scores_data = response.json()
        
        # Infinity returns a dict with "results" list: [{"index": 0, "relevance_score": 0.9}]
        # Sometimes standard Cohere response returns just a list depending on strictness, but usually "results".
        results = scores_data.get("results", []) if isinstance(scores_data, dict) else scores_data
        
        # Map original chunks by their index
        for chunk in chunks:
            chunk["final_score"] = 0.0
            
        for item in results:
            idx = item.get("index")
            # Infinity uses 'relevance_score', fallback to 'score' just in case.
            raw_score = item.get("relevance_score", item.get("score", 0.0))
            
            if idx is not None and 0 <= idx < len(chunks):
                # Sigmoid normalization if necessary, though rerankers typically output raw logits or probabilities.
                normalized_score = self._sigmoid(raw_score) if raw_score > 1 or raw_score < 0 else raw_score
                chunks[idx]["final_score"] = normalized_score
                
        # We return the original list, but with `final_score` populated.
        return chunks

    async def _rerank_via_api(
        self,
        query: str,
        chunks: list[dict[str, Any]],
        client,
    ) -> list[dict[str, Any]]:
        """
        Calls HuggingFace cross-encoder API with query-chunk pairs.
        Uses the /models/{model} endpoint with text-classification pipeline.
        """
        # Build input pairs for the cross-encoder
        pairs = []
        for chunk in chunks:
            text = chunk["payload"].get("text", chunk["payload"].get("content", ""))
            # Truncate to first 300 chars to speed up inference while retaining context
            pairs.append({"text": query, "text_pair": text[:300]})

        # Call HF API — the cross-encoder endpoint expects pairs
        response = await client.post(
            f"/models/{self.model_name}",
            json={"inputs": pairs, "options": {"wait_for_model": True}},
        )

        if response.status_code == 503:
            # Model is loading — retry with wait_for_model
            logger.info("HF model loading, retrying with wait...")
            response = await client.post(
                f"/models/{self.model_name}",
                json={"inputs": pairs, "options": {"wait_for_model": True}},
            )

        if response.status_code != 200:
            raise RuntimeError(
                f"HF API returned {response.status_code}: {response.text[:200]}"
            )

        scores_data = response.json()

        # Parse scores — HF returns different formats depending on the model
        scores = self._parse_hf_scores(scores_data)

        # Assign scores to chunks
        scored_chunks = []
        for i, chunk in enumerate(chunks):
            if i < len(scores):
                raw_score = scores[i]
                # Sigmoid normalization to [0, 1]
                normalized_score = self._sigmoid(raw_score) if raw_score > 1 or raw_score < 0 else raw_score
            else:
                normalized_score = chunk.get("score", 0.5)

            chunk["final_score"] = normalized_score
            scored_chunks.append(chunk)

        return scored_chunks

    def _parse_hf_scores(self, scores_data) -> List[float]:
        """
        Parses HuggingFace API response into a flat list of relevance scores.
        Handles various response formats from different models.
        """
        scores = []

        if isinstance(scores_data, list):
            for item in scores_data:
                if isinstance(item, (int, float)):
                    scores.append(float(item))
                elif isinstance(item, list):
                    # Some models return [[{label, score}, ...], ...]
                    # Take the score of the first/positive label
                    if item and isinstance(item[0], dict):
                        # Find the LABEL_1 or positive score
                        best_score = 0.0
                        for label_info in item:
                            if label_info.get("label") in ("LABEL_1", "entailment", "1"):
                                best_score = label_info["score"]
                                break
                        scores.append(best_score if best_score > 0 else item[0].get("score", 0.5))
                    else:
                        scores.append(float(item[0]) if item else 0.5)
                elif isinstance(item, dict):
                    scores.append(item.get("score", 0.5))
        elif isinstance(scores_data, dict):
            # Single result
            scores.append(scores_data.get("score", 0.5))

        return scores

    def _fallback_rerank(
        self, query: str, chunks: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Lexical boost fallback when cross-encoder API is unavailable."""
        query_words = [w.lower() for w in query.split() if len(w) > 3]
        scored_chunks = []

        for chunk in chunks:
            base_score = chunk.get("score", 0.5)
            text = chunk["payload"].get("text", chunk["payload"].get("content", "")).lower()

            # Count keyword matches
            matches = sum(1 for w in query_words if w in text)
            boost = 1.0 + (matches * 0.1)
            final_score = min(base_score * boost, 1.0)

            chunk["final_score"] = final_score
            scored_chunks.append(chunk)

        return scored_chunks

    def _apply_diversity_penalty(
        self, chunks: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Penalizes repeated chunks from the same document."""
        # Sort by score first
        chunks.sort(key=lambda x: x["final_score"], reverse=True)

        doc_counts: dict[str, int] = {}
        for chunk in chunks:
            doc_id = chunk["payload"].get("document_id")
            if doc_id:
                count = doc_counts.get(doc_id, 0)
                if count > 0:
                    chunk["final_score"] *= 0.95**count
                doc_counts[doc_id] = count + 1

        return chunks

    def _deduplicate_chunks(
        self, chunks: list[dict[str, Any]], threshold: float = 0.80
    ) -> list[dict[str, Any]]:
        """
        Removes chunks with >80% text overlap (context compression).
        Keeps the higher-scored chunk.
        """
        if len(chunks) <= 1:
            return chunks

        # Sort by score descending
        chunks.sort(key=lambda x: x["final_score"], reverse=True)
        kept = []
        kept_texts: list[set[str]] = []

        for chunk in chunks:
            text = chunk["payload"].get("text", chunk["payload"].get("content", ""))
            chunk_words = set(text.lower().split())

            is_duplicate = False
            for existing_words in kept_texts:
                if not chunk_words or not existing_words:
                    continue
                overlap = len(chunk_words & existing_words) / min(
                    len(chunk_words), len(existing_words)
                )
                if overlap > threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                kept.append(chunk)
                kept_texts.append(chunk_words)

        return kept

    @staticmethod
    def _sigmoid(x: float) -> float:
        """Sigmoid function to normalize raw logits to [0, 1]."""
        return 1.0 / (1.0 + math.exp(-x))
