import logging
from typing import List, Dict, Any, Optional
from qdrant_client.http import models
from src.config.qdrant import get_qdrant_client

logger = logging.getLogger("qdrant_repository")

class QdrantRepo:
    _fallback_db: Dict[str, List[Dict[str, Any]]] = {}  # collection_name -> list of points

    def __init__(self):
        self.use_fallback = False
        client = get_qdrant_client()
        if client is None:
            self.use_fallback = True

    def _get_client(self):
        client = get_qdrant_client()
        if client is None:
            self.use_fallback = True
        return client

    def init_collection(self, collection_name: str, vector_size: int = 768) -> bool:
        """Creates a collection if it doesn't exist."""
        client = self._get_client()
        if self.use_fallback or client is None:
            if collection_name not in self._fallback_db:
                self._fallback_db[collection_name] = []
            logger.info(f"[Fallback Store] Initialized collection: {collection_name}")
            return True

        try:
            collections_resp = client.get_collections()
            collection_names = [col.name for col in collections_resp.collections]
            
            if collection_name not in collection_names:
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=vector_size,
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error creating collection {collection_name} in Qdrant: {e}. Switching to fallback.")
            self.use_fallback = True
            if collection_name not in self._fallback_db:
                self._fallback_db[collection_name] = []
            return False

    def upsert_chunks(self, collection_name: str, chunks: List[Dict[str, Any]]) -> bool:
        """Upserts a list of document chunks into Qdrant."""
        self.init_collection(collection_name)
        client = self._get_client()

        if self.use_fallback or client is None:
            existing = self._fallback_db[collection_name]
            new_ids = {c["id"] for c in chunks}
            existing = [item for item in existing if item["id"] not in new_ids]
            existing.extend(chunks)
            self._fallback_db[collection_name] = existing
            logger.info(f"[Fallback Store] Upserted {len(chunks)} chunks into {collection_name}")
            return True

        try:
            points = [
                models.PointStruct(
                    id=chunk["id"],
                    vector=chunk["vector"],
                    payload=chunk["payload"]
                )
                for chunk in chunks
            ]
            client.upsert(
                collection_name=collection_name,
                points=points
            )
            logger.info(f"Upserted {len(chunks)} points to Qdrant collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to upsert points to Qdrant: {e}. Storing in fallback index.")
            self.use_fallback = True
            if collection_name not in self._fallback_db:
                self._fallback_db[collection_name] = []
            self._fallback_db[collection_name].extend(chunks)
            return False

    def search_chunks(self, collection_name: str, query_vector: List[float], limit: int = 5, filter_course: Optional[str] = None) -> List[Dict[str, Any]]:
        """Searches for the closest chunks."""
        self.init_collection(collection_name)
        client = self._get_client()

        if self.use_fallback or client is None:
            import math
            def dot_product(v1, v2):
                return sum(x * y for x, y in zip(v1, v2))
            
            def magnitude(v):
                return math.sqrt(sum(x * x for x in v))
            
            def cosine_similarity(v1, v2):
                mag1 = magnitude(v1)
                mag2 = magnitude(v2)
                if mag1 == 0 or mag2 == 0:
                    return 0.0
                return dot_product(v1, v2) / (mag1 * mag2)

            all_points = self._fallback_db.get(collection_name, [])
            
            if filter_course:
                filtered_points = [
                    p for p in all_points 
                    if p.get("payload", {}).get("course_code", "").lower() == filter_course.lower()
                ]
            else:
                filtered_points = all_points

            scored = []
            for p in filtered_points:
                similarity = cosine_similarity(query_vector, p["vector"])
                scored.append({
                    "id": p["id"],
                    "score": similarity,
                    "payload": p["payload"]
                })
            
            scored.sort(key=lambda x: x["score"], reverse=True)
            return scored[:limit]

        try:
            query_filter = None
            if filter_course:
                query_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key="course_code",
                            match=models.MatchValue(value=filter_course)
                        )
                    ]
                )

            results = client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit
            )
            
            return [
                {
                    "id": r.id,
                    "score": r.score,
                    "payload": r.payload
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Qdrant search failed: {e}. Running local fallback search.")
            self.use_fallback = True
            return self.search_chunks(collection_name, query_vector, limit, filter_course)
