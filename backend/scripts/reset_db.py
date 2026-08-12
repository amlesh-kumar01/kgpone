import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.infrastructure.database import engine, Base
from src.infrastructure.qdrant import get_qdrant_client
from src.infrastructure.neo4j import get_neo4j_driver

# Import all models so they register with Base.metadata
from src.models import user_model, academic_model, document_model, system_model, knowledge_model, chat_model, analysis_job_model, ingestion_job_model

def reset_postgres():
    print("Resetting PostgreSQL database...")
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    # Also drop alembic_version
    with engine.connect() as conn:
        from sqlalchemy import text
        conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE;"))
        conn.commit()
    print("PostgreSQL reset complete.")

def reset_qdrant():
    print("Resetting Qdrant vector store...")
    client = get_qdrant_client()
    if client:
        try:
            collections = client.get_collections().collections
            for collection in collections:
                client.delete_collection(collection_name=collection.name)
                print(f"Deleted collection: {collection.name}")
        except Exception as e:
            print(f"Failed to reset Qdrant: {e}")
    else:
        print("Qdrant client not available.")

def reset_neo4j():
    print("Resetting Neo4j graph...")
    driver = get_neo4j_driver()
    if driver:
        try:
            with driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
            print("Neo4j reset complete.")
        except Exception as e:
            print(f"Failed to reset Neo4j: {e}")
    else:
        print("Neo4j driver not available.")

def reset_s3():
    print("Resetting S3 bucket...")
    import boto3
    from src.config.settings import Settings
    
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=Settings.EXTERNAL_S3_ENDPOINT_URL or None,
            aws_access_key_id=Settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Settings.AWS_SECRET_ACCESS_KEY,
            region_name=Settings.AWS_DEFAULT_REGION
        )
        bucket = Settings.S3_BUCKET_NAME
        
        # List all objects and delete them
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket):
            if 'Contents' in page:
                objects = [{'Key': obj['Key']} for obj in page['Contents']]
                s3.delete_objects(Bucket=bucket, Delete={'Objects': objects})
                print(f"Deleted {len(objects)} objects from S3 bucket {bucket}")
                
        print("S3 reset complete.")
    except Exception as e:
        print(f"Failed to reset S3: {e}")

if __name__ == "__main__":
    reset_postgres()
    reset_qdrant()
    reset_neo4j()
    reset_s3()
    print("Full reset completed successfully! You can now run seed.py.")
