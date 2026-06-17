import os
from dotenv import load_dotenv

# Ensure environment variables are loaded from the backend directory
load_dotenv()

class Settings:
    # Database Settings
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/kgpone")

    # Qdrant Settings
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

    # Neo4j Settings
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

    # S3 / AWS Settings
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "kgpone-assets")
    EXTERNAL_S3_ENDPOINT_URL = os.getenv("EXTERNAL_S3_ENDPOINT_URL", "")

    # Celery / Redis Settings
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    # Gemini Settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

    # Auth Settings
    SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-for-development")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
