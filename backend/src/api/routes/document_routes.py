from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.infrastructure.database import get_db
from src.schemas.document_schema import DocumentCreate, DocumentRead, DocumentUpdate
from src.repositories.postgres.document_repository import DocumentRepository
from src.services.ingestion.document_service import DocumentService
from src.models.user_model import User, UserRole
from src.api.middleware.auth_middleware import get_current_user, require_role
from src.schemas.response_schema import StandardResponse

router = APIRouter(prefix="/documents", tags=["Documents"])

def get_document_service(db: Session = Depends(get_db)) -> DocumentService:
    repo = DocumentRepository(db)
    return DocumentService(repo)

@router.post("/", response_model=StandardResponse[DocumentRead], status_code=status.HTTP_201_CREATED)
def upload_document(doc_in: DocumentCreate, service: DocumentService = Depends(get_document_service), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    data = service.upload_document(doc_in)
    return StandardResponse(status="success", message="Document uploaded successfully", data=data)

@router.get("/offering/{offering_id}", response_model=StandardResponse[list[DocumentRead]])
def list_documents_for_offering(offering_id: UUID, service: DocumentService = Depends(get_document_service), user: User = Depends(get_current_user)):
    data = service.get_documents_for_offering(offering_id)
    return StandardResponse(status="success", message="Documents retrieved successfully", data=data)

@router.get("/{document_id}", response_model=StandardResponse[DocumentRead])
def get_document(document_id: UUID, service: DocumentService = Depends(get_document_service), user: User = Depends(get_current_user)):
    data = service.get_document(document_id)
    return StandardResponse(status="success", message="Document retrieved successfully", data=data)

@router.patch("/{document_id}", response_model=StandardResponse[DocumentRead])
def update_document(document_id: UUID, doc_update: DocumentUpdate, service: DocumentService = Depends(get_document_service), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    data = service.update_document(document_id, doc_update)
    return StandardResponse(status="success", message="Document updated successfully", data=data)
