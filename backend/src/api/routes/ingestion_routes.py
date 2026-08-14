from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID
from src.infrastructure.database import get_db
from src.api.middleware.auth_middleware import get_current_user, require_role
from src.models.user_model import User, UserRole
from src.models.document_model import Document
from src.models.ingestion_job_model import IngestionJob, IngestionStage, IngestionJobStatus
from src.schemas.response_schema import StandardResponse
from datetime import datetime, timezone
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Map stages to celery tasks
def dispatch_stage_task(stage: IngestionStage, document_id: str):
    from src.workers.tasks.ingestion_tasks import (
        parse_document_task,
        build_canonical_ast_task,
        extract_formulas_task,
        extract_questions_task,
        extract_entities_task,
        extract_relations_task,
        build_chunks_task,
        index_qdrant_task,
        build_neo4j_task,
        finalize_manifest_task
    )
    
    if stage == IngestionStage.PARSE:
        parse_document_task.delay(document_id)
    elif stage == IngestionStage.AST:
        build_canonical_ast_task.delay(document_id)
    elif stage == IngestionStage.FORMULA:
        extract_formulas_task.delay(document_id)
    elif stage == IngestionStage.QUESTION:
        extract_questions_task.delay(document_id)
    elif stage == IngestionStage.ENTITY:
        extract_entities_task.delay(document_id)
    elif stage == IngestionStage.RELATION:
        extract_relations_task.delay(document_id)
    elif stage == IngestionStage.CHUNK:
        build_chunks_task.delay(document_id)
    elif stage == IngestionStage.EMBED:
        index_qdrant_task.delay(document_id)
    elif stage == IngestionStage.GRAPH:
        build_neo4j_task.delay(document_id)
    elif stage == IngestionStage.MANIFEST:
        finalize_manifest_task.delay(document_id)
    else:
        raise ValueError(f"Unknown stage: {stage}")

@router.get("/{document_id}/jobs", response_model=StandardResponse[list[dict]])
def get_ingestion_jobs(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))
):
    """Get all ingestion jobs (phases) for a document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    jobs = db.query(IngestionJob).filter(IngestionJob.document_id == document_id).all()
    
    all_stages = [
        IngestionStage.PARSE, IngestionStage.AST, IngestionStage.FORMULA,
        IngestionStage.QUESTION, IngestionStage.ENTITY, IngestionStage.RELATION,
        IngestionStage.CHUNK, IngestionStage.EMBED, IngestionStage.GRAPH, IngestionStage.MANIFEST
    ]
    
    job_map = {job.stage: job for job in jobs}
    from src.repositories.s3.storage_repository import S3Storage
    s3 = S3Storage()
    
    pipeline = []
    for stage in all_stages:
        job = job_map.get(stage)
        output_url = None
        if job and job.output_s3_key:
            try:
                output_url = s3.generate_presigned_url(job.output_s3_key, action="get_object")["url"]
            except Exception:
                pass
                
        pipeline.append({
            "stage": stage.value,
            "status": job.status.value if job else "PENDING",
            "error_message": job.error_message if job else None,
            "started_at": job.started_at if job else None,
            "completed_at": job.completed_at if job else None,
            "updated_at": job.updated_at if job else None,
            "output_s3_key": job.output_s3_key if job else None,
            "output_url": output_url
        })
        
    return StandardResponse(status="success", message="Jobs retrieved", data=pipeline)

@router.post("/{document_id}/jobs/{stage}/retry", response_model=StandardResponse[str])
def retry_ingestion_job(
    document_id: UUID,
    stage: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))
):
    """Retry a specific ingestion phase for a document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    try:
        stage_enum = IngestionStage(stage)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")
        
    def reset_job(stg):
        j = db.query(IngestionJob).filter_by(document_id=document_id, stage=stg).first()
        if j:
            j.status = IngestionJobStatus.PENDING
            j.error_message = None
            
    # Reset this job
    reset_job(stage_enum)
    
    # Cascade resets
    if stage_enum in [IngestionStage.PARSE, IngestionStage.AST]:
        for s in [IngestionStage.FORMULA, IngestionStage.QUESTION, IngestionStage.ENTITY, IngestionStage.RELATION, IngestionStage.CHUNK, IngestionStage.EMBED, IngestionStage.GRAPH, IngestionStage.MANIFEST]:
            reset_job(s)
            
    db.commit()
    dispatch_stage_task(stage_enum, str(document_id))
    
    return StandardResponse(status="success", message=f"Stage {stage} queued for retry", data="")
@router.post("/{document_id}/apply-node-edits", response_model=StandardResponse[dict])
def apply_node_edits(
    document_id: UUID,
    edits: Dict[str, Dict[str, str]],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))
):
    """Surgically update nodes in Canonical AST and cascade downstream pipeline."""
    from src.services.ingestion.artifact_manager import ArtifactManager
    from src.repositories.s3.storage_repository import S3Storage
    
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    s3_prefix = doc.s3_prefix or f"documents/UNKNOWN/{document_id}"
    am = ArtifactManager(str(document_id), s3_prefix, S3Storage())
    
    # 1. Fetch current AST
    ast_key = am.canonical_key()
    try:
        ast_data = am.download_json(ast_key)
    except Exception:
        raise HTTPException(status_code=404, detail="Canonical AST not found on S3")
        
    # 2. Patch nodes
    def patch_nodes(nodes):
        for n in nodes:
            if n["id"] in edits:
                patch = edits[n["id"]]
                if "text_content" in patch:
                    n["text_content"] = patch["text_content"]
                if "latex" in patch:
                    n["latex"] = patch["latex"]
                # Mark as manually edited for UI tracking
                if "source" not in n:
                    n["source"] = {}
                n["source"]["parser"] = "manual_fix"
            if "children" in n and n["children"]:
                patch_nodes(n["children"])
                
    if "nodes" in ast_data:
        patch_nodes(ast_data["nodes"])
        
    # 3. Save patched AST
    am.upload_json(ast_key, ast_data)
    
    # 4. Reset downstream jobs in DB
    downstream_stages = [
        IngestionStage.FORMULA, IngestionStage.QUESTION, IngestionStage.ENTITY,
        IngestionStage.RELATION, IngestionStage.CHUNK, IngestionStage.EMBED, IngestionStage.GRAPH
    ]
    for stage in downstream_stages:
        job = db.query(IngestionJob).filter_by(document_id=document_id, stage=stage).first()
        if job:
            job.status = IngestionJobStatus.PENDING
            job.error_message = None
            
    db.commit()
    
    # 5. Trigger cascade starting from FORMULA
    dispatch_stage_task(IngestionStage.FORMULA, str(document_id))
    
    return StandardResponse(status="success", message="Node edits applied and pipeline retriggered", data={})
