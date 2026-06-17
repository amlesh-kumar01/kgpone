from uuid import UUID
from fastapi import HTTPException
from src.repositories.postgres.document_repository import DocumentRepository
from src.schemas.document_schema import DocumentCreate, DocumentUpdate
from src.models.document_model import Document, ProcessingStatus

class DocumentService:
    def __init__(self, repository: DocumentRepository):
        self.repository = repository

    def upload_document(self, doc_in: DocumentCreate) -> Document:
        # In a real scenario, this service might also trigger the S3 upload
        # or a Celery background task to process the document in Qdrant.
        # For now, we simply save the record with PENDING status.
        return self.repository.create_document(doc_in)

    def get_document(self, document_id: UUID) -> Document:
        doc = self.repository.get_document(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc

    def get_documents_for_offering(self, offering_id: UUID) -> list[Document]:
        return self.repository.get_documents_by_offering(offering_id)

    def update_document(self, document_id: UUID, doc_update: DocumentUpdate) -> Document:
        doc = self.get_document(document_id)
        return self.repository.update_document(doc, doc_update)

    def mark_processing_complete(self, document_id: UUID, qdrant_id: str) -> Document:
        doc = self.repository.update_status(document_id, ProcessingStatus.COMPLETED, qdrant_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc
