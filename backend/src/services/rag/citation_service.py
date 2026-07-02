import logging
from typing import Any

from src.services.rag.base import BaseCitationFormatter

logger = logging.getLogger("citation_service")


class CitationService(BaseCitationFormatter):
    def format_citations(self, ranked_chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Builds transparent provenance metadata for every document source chunk.
        Now chunk-type aware: exposes equation_label, image_s3_key, section breadcrumb.
        """
        citations = []
        for idx, chunk in enumerate(ranked_chunks):
            payload = chunk["payload"]

            # Confidence tier from final reranker score
            score = chunk.get("final_score", chunk.get("score", 0.5))
            if score > 0.8:
                confidence = "High"
            elif score > 0.6:
                confidence = "Medium"
            else:
                confidence = "Supporting Evidence"

            # Build section breadcrumb from context_path list
            context_path = payload.get("context_path", [])
            if isinstance(context_path, list) and context_path:
                section_breadcrumb = " › ".join(context_path)
            else:
                section_breadcrumb = payload.get("header", payload.get("section", "General"))

            # Chunk type enrichment
            chunk_type = payload.get("chunk_type", "text")
            equation_label = payload.get("equation_label")
            raw_latex = payload.get("raw_latex")
            image_s3_key = payload.get("image_s3_key")
            section_number = payload.get("section_number")

            # Source title: prefer document_title, fallback to title
            source_title = (
                payload.get("document_title")
                or payload.get("title")
                or "Lecture Notes"
            )

            # Text snippet from content (preferred) or text field
            raw_content = payload.get("content", payload.get("text", ""))
            # Strip breadcrumb prefix added by the chunker ([Page N | Section: X])
            if raw_content.startswith("[") and "]\n" in raw_content:
                snippet_text = raw_content.split("]\n", 1)[-1]
            else:
                snippet_text = raw_content
            text_snippet = snippet_text[:200].strip()
            if len(snippet_text) > 200:
                text_snippet += "..."

            citations.append({
                "citation_id": f"CIT-{idx + 1}",
                "document_id": payload.get("document_id"),
                "source_title": source_title,
                "course_code": payload.get("course_code", "GEN101"),
                "academic_year": payload.get("academic_year", ""),
                "page_number": payload.get("page_number"),
                "section": section_breadcrumb,
                "section_number": section_number,
                "confidence": confidence,
                "score": float(f"{score:.3f}"),
                "is_prerequisite": payload.get("is_prerequisite", False),
                "prerequisite_concept": payload.get("prerequisite_concept"),
                # Chunk type metadata — used by frontend for rich rendering
                "chunk_type": chunk_type,
                "equation_label": equation_label,
                "raw_latex": raw_latex,
                "image_s3_key": image_s3_key,
                # image_url will be populated by the route handler (presigned GET URL)
                "image_url": None,
                "source_url": payload.get("url", payload.get("s3_key")),
                "text_snippet": text_snippet,
            })

        return citations
