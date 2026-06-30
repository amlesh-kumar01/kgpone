"""
Reciprocal Rank Fusion (RRF) — merges ranked lists from heterogeneous
retrieval backends (Qdrant, Neo4j, PostgreSQL) into a single unified ranking.

RRF normalizes scores across systems with different score semantics:
- Qdrant: cosine similarity [0, 1]
- Neo4j: fixed confidence scores [0.7, 0.8]
- PostgreSQL: exact match scores [1.0]

Formula: RRF(d) = Σ 1 / (k + rank_i(d))
Default k = 60 (standard constant from the original RRF paper).
"""

import logging
from typing import Any

logger = logging.getLogger("fusion")


def reciprocal_rank_fusion(
    result_lists: list[list[dict[str, Any]]],
    k: int = 60,
) -> list[dict[str, Any]]:
    """
    Merges multiple ranked lists using Reciprocal Rank Fusion.

    Args:
        result_lists: List of ranked chunk lists (each pre-sorted by score descending).
                      Each chunk must have an 'id' key and a 'score' key.
        k: Smoothing constant (default 60). Higher k reduces the impact
           of rank position differences.

    Returns:
        Merged list of unique chunks sorted by RRF score descending,
        each with an added 'rrf_score' key.
    """
    if not result_lists:
        return []

    # Accumulate RRF scores per unique chunk ID
    rrf_scores: dict[str, float] = {}
    chunk_map: dict[str, dict[str, Any]] = {}

    for result_list in result_lists:
        # Sort each list by score descending to establish ranking
        sorted_list = sorted(result_list, key=lambda x: x.get("score", 0), reverse=True)

        for rank, chunk in enumerate(sorted_list, start=1):
            chunk_id = str(chunk.get("id", id(chunk)))

            # RRF formula: 1 / (k + rank)
            rrf_contribution = 1.0 / (k + rank)
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + rrf_contribution

            # Keep the chunk data (prefer the version with highest original score)
            if chunk_id not in chunk_map or chunk.get("score", 0) > chunk_map[chunk_id].get("score", 0):
                chunk_map[chunk_id] = chunk

    # Build final list with RRF scores
    merged = []
    for chunk_id, rrf_score in rrf_scores.items():
        chunk = chunk_map[chunk_id].copy()
        chunk["rrf_score"] = rrf_score
        # Also set 'score' to rrf_score for downstream compatibility
        chunk["score"] = rrf_score
        merged.append(chunk)

    # Sort by RRF score descending
    merged.sort(key=lambda x: x["rrf_score"], reverse=True)

    logger.info(
        f"RRF merged {sum(len(rl) for rl in result_lists)} chunks "
        f"from {len(result_lists)} lists into {len(merged)} unique candidates."
    )

    return merged
