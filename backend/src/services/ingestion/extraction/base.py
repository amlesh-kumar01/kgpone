from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseEntityExtractor(ABC):
    @abstractmethod
    async def extract(self, chunks: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts structured entities from document chunks.
        Args:
            chunks: List of text chunks from the document
            context: Dictionary containing document context (title, course_code, etc)
        Returns:
            A dictionary containing the extracted entities.
        """
        pass
