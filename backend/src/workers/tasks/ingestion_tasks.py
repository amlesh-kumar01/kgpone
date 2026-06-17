import asyncio
import os
import tempfile
import logging
from celery import shared_task
from sqlalchemy.orm import Session
from src.infrastructure.database import SessionLocal
from src.repositories.postgres.document_repository import DocumentRepository
from src.repositories.s3.storage_repository import S3Storage
from src.models.document_model import ProcessingStatus

from src.services.ingestion.parser.llama_parser import LlamaParserImpl
from src.services.ingestion.chunking.recursive_chunker import RecursiveChunker
from src.services.ingestion.embedding.gemini_embedding import GeminiEmbedder
from src.repositories.qdrant.vector_repository import QdrantRepository
from src.services.ingestion.pipeline import IngestionPipeline

logger = logging.getLogger("ingestion_tasks")

@shared_task(bind=True, max_retries=3)
def process_document_task(self, document_id: str):
    """
    Celery task that orchestrates the ingestion pipeline for a given document.
    """
    logger.info(f"Starting ingestion task for document {document_id}")
    
    db: Session = SessionLocal()
    try:
        # 1. Fetch document metadata
        repo = DocumentRepository(db)
        doc = repo.get_document(document_id)
        if not doc:
            logger.error(f"Document {document_id} not found in DB.")
            return

        # Update status to processing
        repo.update_status(doc.id, ProcessingStatus.PROCESSING, None)
        
        # We assume doc.s3_url holds the S3 object key (from Presigned URL response)
        file_key = doc.s3_url 
        
        # 2. Download from S3 to a temporary file
        s3_storage = S3Storage()
        ext = os.path.splitext(file_key)[1] or ".pdf"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            temp_path = tmp.name
        
        logger.info(f"Downloading {file_key} to {temp_path}")
        s3_storage.download_file(file_key, temp_path)
        
        # 3. Setup the pipeline
        parser = LlamaParserImpl()
        chunker = RecursiveChunker()
        embedder = GeminiEmbedder()
        vector_store = QdrantRepository()
        
        pipeline = IngestionPipeline(
            parser=parser,
            chunker=chunker,
            embedder=embedder,
            vector_store=vector_store,
            collection_name="documents" # Single collection for all documents
        )
        
        metadata_base = {
            "document_id": str(doc.id),
            "course_offering_id": str(doc.course_offering_id),
            "document_title": doc.title,
            "document_type": doc.doc_type,
            "format": doc.format.value,
            "course_code": doc.course_offering.course.code,
            "course_name": doc.course_offering.course.title
        }
        
        # Build dynamic course-aware parsing instructions
        course = doc.course_offering.course
        dynamic_instructions = (
            f"This document is titled '{doc.title}' and is classified as '{doc.doc_type}'. "
            f"It belongs to the university course '{course.code}: {course.title}' "
            f"offered in {doc.course_offering.semester.value} {doc.course_offering.year}. "
            "Use this specific course context to accurately extract and preserve domain-specific acronyms, "
            "formulas, variables, and technical tables."
        )
        if doc.parsing_instructions:
            dynamic_instructions += f"\n\nAdditional Uploader Instructions:\n{doc.parsing_instructions}"
        
        # 4. Execute pipeline asynchronously
        loop = asyncio.get_event_loop()
        loop.run_until_complete(pipeline.process_document(
            file_path=temp_path, 
            metadata_base=metadata_base,
            parsing_instructions=dynamic_instructions
        ))
        
        # 5. Cleanup temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        # 6. Update document status
        # Since we use a single collection, qdrant_collection_id is just 'documents'
        repo.update_status(doc.id, ProcessingStatus.COMPLETED, "documents")
        logger.info(f"Ingestion completed for document {document_id}")

    except Exception as e:
        logger.exception(f"Ingestion pipeline failed for {document_id}")
        repo.update_status(document_id, ProcessingStatus.FAILED, None)
        # Re-raise to trigger celery retry logic
        raise self.retry(exc=e, countdown=60)
    finally:
        db.close()
