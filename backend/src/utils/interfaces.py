from abc import ABC, abstractmethod

class IVectorRepo(ABC):
    @abstractmethod
    def search(self, query: str):
        pass
        
    @abstractmethod
    async def upsert(self, collection_name: str, vectors: list[list[float]], metadata: list[dict]):
        pass

class IS3Storage(ABC):
    @abstractmethod
    def upload(self, file_name: str, file_content: bytes):
        pass
