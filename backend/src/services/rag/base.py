from abc import ABC, abstractmethod
from typing import Any


class BaseRetriever(ABC):
    """
    Abstract contract for context retrieval services.
    Implementations coordinate embedding, vector search, and graph traversal
    to retrieve relevant document chunks for a student query.
    """

    @abstractmethod
    async def retrieve_context(self, query: str, course_code: str) -> dict[str, Any]:
        """
        Retrieves relevant chunks for a query within a course context.

        Returns a dictionary containing:
            - query: The original query string
            - course_code: The target course code
            - retrieved_chunks: List of scored chunk dicts with payloads
            - graph_visualization: Node-link graph data for frontend
            - has_missing_prerequisites: Whether prerequisite gaps were detected
        """
        pass


class BaseReranker(ABC):
    """
    Abstract contract for chunk reranking services.
    Implementations reorder retrieved chunks by relevance quality,
    optionally using cross-encoders, lexical boosting, or learned models.
    """

    @abstractmethod
    def rerank_chunks(
        self, query: str, chunks: list[dict[str, Any]], top_n: int = 5
    ) -> list[dict[str, Any]]:
        """
        Reranks chunks by relevance to the query.

        Args:
            query: The search query string.
            chunks: List of chunk dicts with 'score' and 'payload' keys.
            top_n: Maximum number of chunks to return.

        Returns:
            Reranked list of chunk dicts, each with a 'final_score' key added.
        """
        pass


class BaseCitationFormatter(ABC):
    """
    Abstract contract for citation formatting services.
    Implementations build provenance metadata linking answer segments
    back to their source documents and pages.
    """

    @abstractmethod
    def format_citations(
        self, ranked_chunks: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Builds transparent provenance citation metadata for ranked chunks.

        Args:
            ranked_chunks: Reranked chunks with payloads and scores.

        Returns:
            List of citation dicts with keys like citation_id, source_title,
            course_code, confidence, score, text_snippet, etc.
        """
        pass


class BaseAnswerGenerator(ABC):
    """
    Abstract contract for answer generation services.
    Implementations synthesize a grounded academic response from
    ranked context chunks and their citation metadata.
    """

    @abstractmethod
    def generate_answer(
        self,
        query: str,
        ranked_chunks: list[dict[str, Any]],
        citations: list[dict[str, Any]],
    ) -> str:
        """
        Generates a grounded answer from ranked context and citations.

        Args:
            query: The student's question.
            ranked_chunks: Reranked chunks with payloads.
            citations: Formatted citation metadata for each chunk.

        Returns:
            A string containing the synthesized academic answer with
            inline citation references (e.g. [CIT-1]).
        """
        pass
