from abc import ABC, abstractmethod
from typing import Any, List, Dict
from src.schemas.dom_schema import DocumentDOM

class BaseChunker(ABC):
    @abstractmethod
    def chunk(self, dom: DocumentDOM) -> List[Dict[str, Any]]:
        """
        Splits the given DocumentDOM into chunks.
        Returns a list of dictionaries, where each dict contains 'content' and any 'metadata'.
        """
        pass
