from abc import ABC, abstractmethod

class IVectorRepo(ABC):
    @abstractmethod
    def search(self, collection_name: str, query_vector: list[float], filters: dict | None = None, limit: int = 5):
        pass
        
    @abstractmethod
    async def upsert(self, collection_name: str, vectors: list[list[float]], metadata: list[dict]):
        pass

    @abstractmethod
    def delete_by_filter(self, collection_name: str, filters: dict):
        pass

class IS3Storage(ABC):
    @abstractmethod
    def upload(self, file_key: str, file_content: bytes):
        pass

    @abstractmethod
    def generate_presigned_url(self, file_key: str, content_type: str, expiration: int = 3600) -> dict:
        pass
        
    @abstractmethod
    def download_file(self, file_key: str, download_path: str):
        pass

    @abstractmethod
    def delete_file(self, file_key: str):
        pass

class IGraphRepository(ABC):
    @abstractmethod
    def delete_document_nodes(self, document_id: str):
        pass

    @abstractmethod
    def delete_course_nodes(self, course_id: str):
        pass
