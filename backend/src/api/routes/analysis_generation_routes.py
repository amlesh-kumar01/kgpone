from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel
from typing import List, Optional
import logging
import uuid

from src.infrastructure.database import get_db
from src.api.middleware.auth_middleware import get_current_user, require_role
from src.models.user_model import User, UserRole
from src.models.document_model import Document
from src.models.analysis_generation_model import AnalysisGeneration, AnalysisType, AnalysisStatus
from src.schemas.response_schema import StandardResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/generations", tags=["Generations"])

class AnalysisGenerationRequest(BaseModel):
    type: AnalysisType
    title: str
    prompt: str
    topics: List[str]

@router.get("/{document_id}/history", response_model=StandardResponse[list[dict]])
def get_analysis_generations(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER, UserRole.STUDENT]))
):
    """Get all analysis generations for a document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    generations = db.query(AnalysisGeneration).filter(AnalysisGeneration.document_id == document_id).order_by(AnalysisGeneration.created_at.desc()).all()
    
    from src.repositories.s3.storage_repository import S3Storage
    s3 = S3Storage()
    
    result = []
    for gen in generations:
        output_url = None
        if gen.output_s3_key:
            try:
                output_url = s3.generate_presigned_url(gen.output_s3_key, action="get_object")["url"]
            except Exception as e:
                logger.error(f"Failed to generate presigned URL for {gen.output_s3_key}: {e}")
                
        result.append({
            "id": str(gen.id),
            "type": gen.type.value,
            "title": gen.title,
            "prompt": gen.prompt,
            "topics": gen.topics,
            "status": gen.status.value,
            "error_message": gen.error_message,
            "created_at": gen.created_at,
            "output_s3_key": gen.output_s3_key,
            "output_url": output_url
        })
        
    return StandardResponse(status="success", message="Analysis generations retrieved", data=result)

@router.post("/{document_id}/trigger", response_model=StandardResponse[dict])
def trigger_analysis_generation(
    document_id: UUID,
    request: AnalysisGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))
):
    """Trigger a new analysis generation."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    new_gen = AnalysisGeneration(
        document_id=document_id,
        type=request.type,
        title=request.title,
        prompt=request.prompt,
        topics=request.topics,
        status=AnalysisStatus.PENDING
    )
    
    db.add(new_gen)
    db.commit()
    db.refresh(new_gen)
    
    # Trigger celery task
    from src.workers.tasks.analysis_tasks import generate_analysis_task
    generate_analysis_task.delay(str(document_id), str(new_gen.id))
    
    return StandardResponse(status="success", message="Generation triggered successfully", data={"id": str(new_gen.id)})

@router.get("/{document_id}/topics", response_model=StandardResponse[list[dict]])
def get_document_topics(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER, UserRole.STUDENT]))
):
    """Fetch entities from Knowledge Graph to use as selectable topics."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    from src.services.ingestion.artifact_manager import ArtifactManager
    from src.repositories.s3.storage_repository import S3Storage
    s3_prefix = doc.s3_prefix or f"documents/{doc.study_unit_id}/{document_id}"
    am = ArtifactManager(str(document_id), s3_prefix, S3Storage())
    
    entities_data = None
    try:
        entities_data = am.download_json(am.knowledge_key("entities"))
        if isinstance(entities_data, str):
            import json
            entities_data = json.loads(entities_data)
    except Exception as e:
        logger.warning(f"Failed to fetch entities for document {document_id}: {e}")
        
    entities = entities_data.get("entities", []) if isinstance(entities_data, dict) else []
    
    # Deduplicate and sort by relevance or simply name
    topics = []
    seen = set()
    for e in entities:
        name = e.get("canonical_name", "")
        if name and name not in seen:
            seen.add(name)
            topics.append({
                "name": name,
                "type": e.get("type", "UNKNOWN"),
                "description": e.get("description", "")
            })
            
    topics = sorted(topics, key=lambda x: x["name"])
    
    return StandardResponse(status="success", message="Topics retrieved", data=topics)

@router.delete("/{document_id}/delete/{generation_id}", response_model=StandardResponse[dict])
def delete_analysis_generation(
    document_id: UUID,
    generation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))
):
    """Delete a generation and its S3 file."""
    gen = db.query(AnalysisGeneration).filter(AnalysisGeneration.id == generation_id, AnalysisGeneration.document_id == document_id).first()
    if not gen:
        raise HTTPException(status_code=404, detail="Generation not found")
        
    if gen.output_s3_key:
        from src.repositories.s3.storage_repository import S3Storage
        try:
            S3Storage().delete_file(gen.output_s3_key)
        except Exception:
            pass
        
    db.delete(gen)
    db.commit()
    
    return StandardResponse(status="success", message="Generation deleted", data={})
