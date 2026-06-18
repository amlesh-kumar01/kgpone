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
from src.services.ingestion.metadata_builder import MetadataBuilder
from src.workers.tasks.cleanup_tasks import delete_old_vectors_task

logger = logging.getLogger("ingestion_tasks")

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_document_task(self, document_id: str, old_version: int = None):
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
        
        # We assume doc.s3_key holds the S3 object key (from Presigned URL response)
        file_key = doc.s3_key 
        
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
        
        # Build flattened metadata payload using the builder
        metadata_base = MetadataBuilder.build(doc)
        
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
        doc.status = ProcessingStatus.COMPLETED
        db.commit()
        logger.info(f"Successfully processed Document: {document_id}")
        
        # If this was a re-ingestion, trigger deletion of the old vectors safely
        if old_version is not None:
            delete_old_vectors_task.delay(document_id, old_version)

    except Exception as e:
        logger.error(f"Failed to process Document {document_id}: {str(e)}")
        repo.update_status(document_id, ProcessingStatus.FAILED, None)
        # Re-raise to trigger celery retry logic
        raise self.retry(exc=e, countdown=60)
    finally:
        db.close()
