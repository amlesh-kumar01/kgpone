import uuid
import asyncio
from qdrant_client.models import VectorParams, Distance, PointStruct
from src.infrastructure.qdrant import get_qdrant_client
from src.utils.interfaces import IVectorRepo

class QdrantRepository(IVectorRepo):
    def __init__(self, vector_size: int = 768):
        self.client = get_qdrant_client()
        self.vector_size = vector_size
        if self.client is None:
            raise RuntimeError("Qdrant client could not be initialized.")

    def search(self, query: str):
        # Implementation to be added later
        pass

    def _ensure_collection_exists(self, collection_name: str):
        collections_response = self.client.get_collections()
        collection_names = [col.name for col in collections_response.collections]
        
        if collection_name not in collection_names:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
            )

    async def upsert(self, collection_name: str, vectors: list[list[float]], metadata: list[dict]):
        if len(vectors) != len(metadata):
            raise ValueError("The number of vectors must match the number of metadata entries.")
            
        # Ensure the collection exists before inserting (blocking call wrapped in thread)
        await asyncio.to_thread(self._ensure_collection_exists, collection_name)

        points = []
        for vec, meta in zip(vectors, metadata):
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vec,
                    payload=meta
                )
            )

        # Upsert in batches of 100 to avoid request size limits
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            await asyncio.to_thread(
                self.client.upsert,
                collection_name=collection_name,
                points=batch
            )
