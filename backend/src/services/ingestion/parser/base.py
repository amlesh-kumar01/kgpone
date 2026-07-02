from abc import ABC, abstractmethod
from typing import Optional
from src.schemas.dom_schema import DocumentDOM

class BaseParser(ABC):
    @abstractmethod
    async def parse(self, file_path: str, parsing_instructions: Optional[str] = None) -> DocumentDOM:
        """
        Parses a document from the given file path and returns its Document Object Model (DOM) hierarchy.
        """
        pass
