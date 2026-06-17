from abc import ABC, abstractmethod

class IVectorRepo(ABC):
    @abstractmethod
    def search(self, collection_name: str, query_vector: list[float], filters: dict | None = None, limit: int = 5):
        pass
        
    @abstractmethod
    async def upsert(self, collection_name: str, vectors: list[list[float]], metadata: list[dict]):
        pass

class IS3Storage(ABC):
    @abstractmethod
    def upload(self, file_name: str, file_content: bytes):
        pass
