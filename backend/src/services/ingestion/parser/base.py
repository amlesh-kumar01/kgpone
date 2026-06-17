from abc import ABC, abstractmethod

from typing import Optional

class BaseParser(ABC):
    @abstractmethod
    async def parse(self, file_path: str, parsing_instructions: Optional[str] = None) -> str:
        """
        Parses a document from the given file path and returns its extracted markdown content.
        """
        pass
