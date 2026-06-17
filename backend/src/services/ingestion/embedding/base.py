from abc import ABC, abstractmethod

class BaseEmbedder(ABC):
    @abstractmethod
    async def embed(self, chunks: list[str]) -> list[list[float]]:
        """
        Takes a list of string chunks and returns a list of float vectors.
        """
        pass
