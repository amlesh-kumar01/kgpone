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
    def initialize_schema(self):
        pass

    @abstractmethod
    def merge_node(self, label: str, unique_key: str, unique_value: str, properties: dict) -> bool:
        pass

    @abstractmethod
    def merge_relationship(self, from_label: str, from_key: str, from_val: str, 
                           to_label: str, to_key: str, to_val: str, rel_type: str) -> bool:
        pass

    @abstractmethod
    def delete_document_entities(self, document_id: str) -> bool:
        pass

    @abstractmethod
    def delete_course_subgraph(self, study_unit_code: str) -> bool:
        pass

    @abstractmethod
    def execute_read_query(self, query: str, parameters: dict | None = None) -> list[dict]:
        pass

    @abstractmethod
    def execute_write_query(self, query: str, parameters: dict | None = None) -> bool:
        pass

class IRetrievalService(ABC):
    @abstractmethod
    async def retrieve_context(self, query: str, study_unit_code: str) -> dict:
        """
        Coordinates context retrieval for the query.
        Returns a dictionary containing retrieved_chunks, graph_visualization, and metadata.
        """
        pass

class ILLMFactory(ABC):
    @abstractmethod
    def get_llm(self, model_name: str | None = None, **kwargs):
        """Returns a LangChain BaseChatModel instance based on configured AI_PROVIDER."""
        pass

    @abstractmethod
    def get_embeddings(self, model_name: str | None = None, **kwargs):
        """Returns a LangChain Embeddings instance based on configured EMBEDDING_PROVIDER."""
        pass
