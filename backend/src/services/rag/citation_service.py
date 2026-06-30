import logging
from typing import Any

from src.services.rag.base import BaseCitationFormatter

logger = logging.getLogger("citation_service")


class CitationService(BaseCitationFormatter):
    def format_citations(self, ranked_chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Builds transparent provenance metadata for every document source chunk.
        """
        citations = []
        for idx, chunk in enumerate(ranked_chunks):
            payload = chunk["payload"]
            
            # Estimate confidence based on final similarity score
            score = chunk.get("final_score", chunk.get("score", 0.5))
            if score > 0.8:
                confidence = "High"
            elif score > 0.6:
                confidence = "Medium"
            else:
                confidence = "Supporting Evidence"

            citations.append({
                "citation_id": f"CIT-{idx + 1}",
                "source_title": payload.get("title", "Lecture Notes"),
                "course_code": payload.get("course_code", "GEN101"),
                "academic_year": payload.get("academic_year", "1st Year"),
                "page_number": payload.get("page_number", 1),
                "section": payload.get("header", "General"),
                "confidence": confidence,
                "score": float(f"{score:.3f}"),
                "is_prerequisite": payload.get("is_prerequisite", False),
                "prerequisite_concept": payload.get("prerequisite_concept", None),
                "source_url": payload.get("url", payload.get("s3_key", None)),
                "text_snippet": payload.get("content", payload.get("text", ""))[:250] + "..."
            })
            
        return citations
