from abc import ABC, abstractmethod
from typing import Any

class BaseChunker(ABC):
    @abstractmethod
    def chunk(self, text: str) -> list[dict[str, Any]]:
        """
        Splits the given text into chunks.
        Returns a list of dictionaries, where each dict contains 'content' and any 'metadata'.
        """
        pass
