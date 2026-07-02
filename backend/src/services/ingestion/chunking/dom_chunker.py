import logging
from typing import Any, List, Dict, Optional
from src.services.ingestion.chunking.base import BaseChunker
from src.schemas.dom_schema import DocumentDOM, DOMNode

logger = logging.getLogger("dom_chunker")


class DOMChunker(BaseChunker):
    """
    Splits a DocumentDOM into retrieval-ready chunks.

    Strategy:
    - **equation** nodes  → own dedicated chunk (never merged), with LaTeX and label.
    - **figure** nodes    → own dedicated chunk with S3 key in metadata.
    - **table** nodes     → row-as-a-chunk (one chunk per data row).
    - **text/heading/list** → aggregated into sliding-window chunks within the
                               same context_path section, with a context breadcrumb
                               prepended to each chunk content.

    Page-number carry-forward: the last seen page number is propagated into the
    next buffer so page context is never lost across a section boundary flush.
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chunk(self, dom: DocumentDOM) -> List[Dict[str, Any]]:
        chunks: List[Dict[str, Any]] = []

        text_buffer: List[str] = []
        token_count: int = 0
        current_context = None
        current_page: Optional[int] = None   # carries forward across flushes

        def _breadcrumb(ctx_path: List[str], page: Optional[int]) -> str:
            """Builds a context prefix for chunk content."""
            parts = []
            if page is not None:
                parts.append(f"Page {page}")
            if ctx_path:
                parts.append(f"Section: {ctx_path[-1]}")
            return f"[{' | '.join(parts)}]\n" if parts else ""

        def flush_text() -> None:
            nonlocal text_buffer, token_count, current_context
            if not text_buffer:
                return
            ctx_path = current_context.context_path if current_context else []
            metadata = current_context.model_dump() if current_context else {}
            if current_page is not None:
                metadata["page_number"] = current_page

            breadcrumb = _breadcrumb(ctx_path, current_page)
            content = breadcrumb + "\n".join(text_buffer)

            chunks.append({
                "content": content,
                "metadata": metadata,
                "chunk_type": "text",
            })
            text_buffer.clear()
            token_count = 0
            # NOTE: current_page intentionally NOT reset — it carries forward

        for node in dom.nodes:

            # ── Equation: always its own chunk ─────────────────────────
            if node.node_type == "equation":
                flush_text()
                ctx_path = node.metadata.context_path
                page = node.page_number or current_page

                label_str = f"Eq. ({node.equation_label})" if node.equation_label else "Equation"
                breadcrumb = _breadcrumb(ctx_path, page)
                content = f"{breadcrumb}[{label_str}]\n{node.text_content}"

                meta = node.metadata.model_dump()
                if page is not None:
                    meta["page_number"] = page
                if node.equation_label:
                    meta["equation_label"] = node.equation_label
                if node.raw_latex:
                    meta["raw_latex"] = node.raw_latex

                chunks.append({
                    "content": content,
                    "metadata": meta,
                    "chunk_type": "equation",
                })
                if node.page_number:
                    current_page = node.page_number
                continue

            # ── Figure: always its own chunk ───────────────────────────
            if node.node_type == "figure":
                flush_text()
                ctx_path = node.metadata.context_path
                page = node.page_number or current_page

                breadcrumb = _breadcrumb(ctx_path, page)
                content = f"{breadcrumb}[Figure]\n{node.text_content}"

                meta = node.metadata.model_dump()
                if page is not None:
                    meta["page_number"] = page

                chunks.append({
                    "content": content,
                    "metadata": meta,
                    "chunk_type": "figure",
                })
                if node.page_number:
                    current_page = node.page_number
                continue

            # ── Table: row-as-a-chunk ──────────────────────────────────
            if node.node_type == "table":
                flush_text()
                page = node.page_number or current_page

                rows = node.text_content.strip().split("\n")
                headers: List[str] = []
                data_rows: List[str] = []

                if len(rows) >= 3 and "|" in rows[0] and "-" in rows[1]:
                    headers = [h.strip() for h in rows[0].split("|") if h.strip()]
                    data_rows = rows[2:]
                else:
                    data_rows = rows

                for row in data_rows:
                    if not row.strip():
                        continue
                    row_meta = node.metadata.model_copy()
                    row_meta.headers = headers
                    if node.metadata.context_path:
                        row_meta.parent_table_title = node.metadata.context_path[-1]

                    row_meta_dict = row_meta.model_dump()
                    if page is not None:
                        row_meta_dict["page_number"] = page

                    breadcrumb = _breadcrumb(node.metadata.context_path, page)
                    content = f"{breadcrumb}{row.strip()}"

                    chunks.append({
                        "content": content,
                        "metadata": row_meta_dict,
                        "chunk_type": "table_row",
                    })

                if node.page_number:
                    current_page = node.page_number
                continue

            # ── Text / Heading / List: aggregated window ───────────────
            node_tokens = len(node.text_content.split())

            # Flush on section boundary
            if (
                current_context is not None
                and current_context.context_path != node.metadata.context_path
            ):
                flush_text()

            # Flush when chunk size exceeded
            if current_token_count_would_exceed(token_count, node_tokens, self.chunk_size):
                flush_text()

            text_buffer.append(node.text_content)
            token_count += node_tokens
            current_context = node.metadata
            if node.page_number is not None:
                current_page = node.page_number

        flush_text()
        return chunks


def current_token_count_would_exceed(current: int, incoming: int, limit: int) -> bool:
    return current > 0 and (current + incoming) > limit
