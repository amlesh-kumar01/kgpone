import asyncio
from src.infrastructure.database import SessionLocal
from src.repositories.postgres.document_repository import DocumentRepository

db = SessionLocal()
repo = DocumentRepository(db)
docs = db.execute("SELECT id, title FROM documents WHERE title ILIKE '%Attention is All You Need%'").fetchall()
for d in docs:
    print(d)
