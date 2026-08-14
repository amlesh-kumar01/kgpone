from uuid import UUID
from fastapi import HTTPException
from src.repositories.postgres.document_repository import DocumentRepository
from src.schemas.document_schema import DocumentCreate, DocumentUpdate, PresignedUrlResponse
from src.models.document_model import Document, ProcessingStatus
from src.models.system_model import CleanupJob, DeletionStatus
from src.repositories.s3.storage_repository import S3Storage
from src.workers.tasks.ingestion_tasks import process_document_task
from src.workers.tasks.cleanup_tasks import cleanup_document_task
from src.models.academic_model import Offering
from src.repositories.redis.cache_repository import CacheRepository
from src.schemas.document_schema import DocumentRead
import uuid

class DocumentService:
    def __init__(self, repository: DocumentRepository, cache_repo: CacheRepository, s3_storage: S3Storage = None):
        self.repository = repository
        self.cache_repo = cache_repo
        self.s3_storage = s3_storage or S3Storage()

    def generate_upload_url(self, user_id: UUID, filename: str, content_type: str, study_unit_id: UUID) -> PresignedUrlResponse:
        from src.models.academic_model import StudyUnit
        study_unit = self.repository.session.get(StudyUnit, study_unit_id)
        if not study_unit:
            raise HTTPException(status_code=404, detail="StudyUnit not found")
        
        doc_id = uuid.uuid4()
        s3_prefix = f"documents/{study_unit_id}/{doc_id}"
        original_s3_key = f"{s3_prefix}/original/{filename}"
        
        presigned_data = self.s3_storage.generate_presigned_url(
            file_key=original_s3_key,
            content_type=content_type
        )
        return PresignedUrlResponse(
            upload_url=presigned_data["url"],
            file_key=original_s3_key, # legacy support if needed
            document_id=doc_id,
            s3_prefix=s3_prefix,
            original_s3_key=original_s3_key
        )

    def generate_download_url(self, document_id: UUID) -> str:
        doc = self.get_document(document_id)
        if not doc.s3_key:
            raise HTTPException(status_code=400, detail="Document has no associated file")
            
        presigned_data = self.s3_storage.generate_presigned_url(
            file_key=doc.s3_key,
            action="get_object"
        )
        return presigned_data["url"]

    def upload_document(self, doc_in: DocumentCreate) -> Document:
        # Save the record with PENDING status.
        doc = self.repository.create_document(doc_in)
        
        # Trigger the asynchronous Celery pipeline
        process_document_task.delay(str(doc.id))
        
        self.cache_repo.delete("documents:all:v1")
        if doc.study_unit_id:
            self.cache_repo.delete(f"documents:study_unit:{doc.study_unit_id}:v1")
            
        return doc

    def get_document(self, document_id: UUID) -> Document:
        doc = self.repository.get_document(document_id)
        if not doc or doc.is_deleted:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc

    def get_all_documents(self):
        cache_key = "documents:all:v1"
        cached = self.cache_repo.get(cache_key)
        if cached is not None:
            return cached
            
        docs = self.repository.get_all_documents()
        serialized = [DocumentRead.model_validate(d).model_dump(mode="json") for d in docs]
        self.cache_repo.set(cache_key, serialized, ttl=3600)
        return docs

    def delete_document(self, document_id: UUID):
        doc = self.repository.get_document(document_id)
        if not doc or doc.is_deleted:
            raise HTTPException(status_code=404, detail="Document not found")
            
        # Soft delete
        doc.is_deleted = True
        doc.deletion_status = DeletionStatus.PENDING
        self.repository.session.commit()
        
        # Create cleanup job
        job = CleanupJob(resource_type="DOCUMENT", resource_id=document_id)
        self.repository.session.add(job)
        self.repository.session.commit()
        self.repository.session.refresh(job)
        
        # Dispatch Celery Task
        cleanup_document_task.delay(str(document_id), str(job.id))
        
        self.cache_repo.delete("documents:all:v1")
        if doc.study_unit_id:
            self.cache_repo.delete(f"documents:study_unit:{doc.study_unit_id}:v1")
            
        return doc

    def get_documents_for_study_unit(self, study_unit_id: UUID):
        cache_key = f"documents:study_unit:{study_unit_id}:v1"
        cached = self.cache_repo.get(cache_key)
        if cached is not None:
            return cached
            
        docs = self.repository.get_documents_by_study_unit(study_unit_id)
        serialized = [DocumentRead.model_validate(d).model_dump(mode="json") for d in docs]
        self.cache_repo.set(cache_key, serialized, ttl=3600)
        return docs

    def update_document(self, document_id: UUID, doc_update: DocumentUpdate) -> Document:
        doc = self.get_document(document_id)
        updated_doc = self.repository.update_document(doc, doc_update)
        self.cache_repo.delete("documents:all:v1")
        if updated_doc.study_unit_id:
            self.cache_repo.delete(f"documents:study_unit:{updated_doc.study_unit_id}:v1")
        return updated_doc

    def mark_processing_complete(self, document_id: UUID, qdrant_id: str) -> Document:
        doc = self.repository.update_status(document_id, ProcessingStatus.COMPLETED, qdrant_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        self.cache_repo.delete("documents:all:v1")
        if doc.study_unit_id:
            self.cache_repo.delete(f"documents:study_unit:{doc.study_unit_id}:v1")
        return doc
