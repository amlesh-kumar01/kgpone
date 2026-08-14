import asyncio
from src.infrastructure.redis_cache import get_sync_redis_cache_client
from src.infrastructure.neo4j import get_neo4j_driver
from src.infrastructure.qdrant import get_qdrant_client

def clean_redis():
    print("Cleaning Redis...")
    r = get_sync_redis_cache_client()
    if r:
        r.flushall()
        print("Redis flushed successfully.")
    else:
        print("Redis client not available.")

def clean_qdrant():
    print("Cleaning Qdrant...")
    q = get_qdrant_client()
    if q:
        response = q.get_collections()
        for collection in response.collections:
            print(f"Dropping collection: {collection.name}")
            q.delete_collection(collection.name)
        print("Qdrant cleaned successfully.")
    else:
        print("Qdrant client not available.")

def clean_neo4j():
    print("Cleaning Neo4j...")
    driver = get_neo4j_driver()
    if driver:
        with driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n;")
        print("Neo4j cleaned successfully.")
    else:
        print("Neo4j driver not available.")

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    clean_redis()
    clean_qdrant()
    clean_neo4j()
