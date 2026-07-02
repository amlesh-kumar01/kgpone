from abc import ABC, abstractmethod

class BaseEmbedder(ABC):
    @abstractmethod
    async def embed(self, chunks: list[str]) -> list[list[float]]:
        """
        Takes a list of string chunks and returns a list of float vectors.
        """
        pass

    @abstractmethod
    async def embed_query(self, query: str) -> list[float]:
        """
        Takes a single query string and returns a single float vector.
        """
        pass
