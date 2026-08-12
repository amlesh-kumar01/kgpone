from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.infrastructure.database import get_db
from src.schemas.response_schema import StandardResponse
from src.services.inspection.document_inspector import DocumentInspector, InspectionReport
from src.repositories.postgres.document_repository import DocumentRepository
from src.services.ingestion.artifact_manager import ArtifactManager
from src.infrastructure.s3 import S3Storage
from src.models.user_model import User, UserRole
from src.api.middleware.auth_middleware import get_current_user, require_role
from uuid import UUID

router = APIRouter(prefix="/inspect", tags=["Inspection"])

def get_inspector(db: Session = Depends(get_db)) -> DocumentInspector:
    return DocumentInspector(db)

def get_artifact_manager(document_id: str, db: Session = Depends(get_db)) -> ArtifactManager:
    repo = DocumentRepository(db)
    try:
        doc = repo.get_by_id(UUID(document_id))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid UUID")
        
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    s3_prefix = doc.s3_prefix or f"documents/UNKNOWN/UNKNOWN/UNKNOWN/{document_id}"
    return ArtifactManager(document_id, s3_prefix, S3Storage())

@router.get("/{document_id}", response_model=StandardResponse[InspectionReport])
def get_inspection_report(document_id: str, inspector: DocumentInspector = Depends(get_inspector), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    try:
        report = inspector.inspect(document_id)
        return StandardResponse(status="success", message="Inspection report generated", data=report)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_id}/manifest", response_model=StandardResponse[dict])
def get_manifest(document_id: str, artifact_manager: ArtifactManager = Depends(get_artifact_manager), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    if not artifact_manager.exists(artifact_manager.manifest_key()):
        raise HTTPException(status_code=404, detail="Manifest not found")
    data = artifact_manager.read_manifest()
    return StandardResponse(status="success", message="Manifest loaded", data=data)

@router.get("/{document_id}/canonical", response_model=StandardResponse[dict])
def get_canonical(document_id: str, artifact_manager: ArtifactManager = Depends(get_artifact_manager), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    key = artifact_manager.canonical_key()
    if not artifact_manager.exists(key):
        raise HTTPException(status_code=404, detail="Canonical AST not found")
    data = artifact_manager.download_json(key)
    return StandardResponse(status="success", message="Canonical AST loaded", data=data)

@router.get("/{document_id}/knowledge/{type}", response_model=StandardResponse[Any])
def get_knowledge(document_id: str, type: str, artifact_manager: ArtifactManager = Depends(get_artifact_manager), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    if type not in ["entities", "formulas", "questions", "relations", "concepts"]:
        raise HTTPException(status_code=400, detail="Invalid knowledge type")
        
    key = artifact_manager.knowledge_key(type)
    if not artifact_manager.exists(key):
        raise HTTPException(status_code=404, detail=f"{type.capitalize()} not found")
        
    data = artifact_manager.download_json(key)
    return StandardResponse(status="success", message=f"{type.capitalize()} loaded", data=data)

@router.get("/{document_id}/chunks", response_model=StandardResponse[Any])
def get_chunks(document_id: str, artifact_manager: ArtifactManager = Depends(get_artifact_manager), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    key = artifact_manager.chunks_key()
    if not artifact_manager.exists(key):
        raise HTTPException(status_code=404, detail="Chunks not found")
    data = artifact_manager.download_json(key)
    return StandardResponse(status="success", message="Chunks loaded", data=data)
