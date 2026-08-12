from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.infrastructure.database import get_db
from src.models.user_model import User, UserRole
from src.api.middleware.auth_middleware import get_current_user, require_role
from src.schemas.response_schema import StandardResponse
from src.models.analysis_job_model import AnalysisJob, AnalysisType, AnalysisJobStatus
from src.infrastructure.s3 import S3Storage

router = APIRouter(prefix="/analysis", tags=["Analysis"])

class SummarizeRequest(BaseModel):
    document_id: UUID

class MultiDocumentRequest(BaseModel):
    document_ids: list[UUID]

class AnalysisJobResponse(BaseModel):
    id: UUID
    analysis_type: str
    status: str
    result_s3_key: str | None
    result_md_s3_key: str | None
    error_message: str | None

@router.post("/summarize", response_model=StandardResponse[dict])
def summarize_document(
    req: SummarizeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    job = AnalysisJob(
        user_id=user.id,
        analysis_type=AnalysisType.SUMMARIZE,
        status=AnalysisJobStatus.PENDING,
        input_metadata={"document_id": str(req.document_id)}
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    from src.workers.tasks.analysis_tasks import summarize_document_task, generate_quiz_task, generate_formula_revision_task
    summarize_document_task.delay(str(new_job.id), str(req.document_id), str(user.id))
    
    return StandardResponse(
        status="success",
        message="Summarization job started successfully",
        data={"analysis_id": new_job.id}
    )

@router.post("/quiz", response_model=StandardResponse)
async def generate_quiz(req: SummarizeRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Starts an asynchronous LLM job to generate a study quiz."""
    new_job = AnalysisJob(
        id=uuid4(),
        user_id=user.id,
        analysis_type=AnalysisType.QUIZ,
        status=AnalysisJobStatus.PENDING,
        input_metadata={"document_id": str(req.document_id)}
    )
    db.add(new_job)
    db.commit()
    
    from src.workers.tasks.analysis_tasks import generate_quiz_task
    generate_quiz_task.delay(str(new_job.id), str(req.document_id), str(user.id))
    
    return StandardResponse(
        status="success",
        message="Quiz generation job started successfully",
        data={"analysis_id": new_job.id}
    )

@router.post("/formula-revision", response_model=StandardResponse)
async def generate_formula_revision(req: SummarizeRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Starts an asynchronous LLM job to generate a formula revision sheet."""
    new_job = AnalysisJob(
        id=uuid4(),
        user_id=user.id,
        analysis_type=AnalysisType.FORMULA_REVISION,
        status=AnalysisJobStatus.PENDING,
        input_metadata={"document_id": str(req.document_id)}
    )
    db.add(new_job)
    db.commit()
    
    from src.workers.tasks.analysis_tasks import generate_formula_revision_task
    generate_formula_revision_task.delay(str(new_job.id), str(req.document_id), str(user.id))
    
    return StandardResponse(
        status="success",
        message="Formula revision job started successfully",
        data={"analysis_id": new_job.id}
    )

@router.post("/course-summary", response_model=StandardResponse)
async def generate_course_summary(req: MultiDocumentRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Starts an asynchronous LLM job to generate a course summary across multiple documents."""
    new_job = AnalysisJob(
        id=uuid4(),
        user_id=user.id,
        analysis_type=AnalysisType.COURSE_SUMMARY,
        status=AnalysisJobStatus.PENDING,
        input_metadata={"document_ids": [str(d) for d in req.document_ids]}
    )
    db.add(new_job)
    db.commit()
    
    from src.workers.tasks.analysis_tasks import course_summary_task
    course_summary_task.delay(str(new_job.id), [str(d) for d in req.document_ids], str(user.id))
    
    return StandardResponse(
        status="success",
        message="Course summary job started successfully",
        data={"analysis_id": new_job.id}
    )

@router.post("/compare", response_model=StandardResponse)
async def compare_documents(req: MultiDocumentRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Starts an asynchronous job to compare concepts and formulas across documents."""
    if len(req.document_ids) < 2:
        raise HTTPException(status_code=400, detail="Comparison requires at least 2 documents.")
        
    new_job = AnalysisJob(
        id=uuid4(),
        user_id=user.id,
        analysis_type=AnalysisType.DOCUMENT_COMPARISON,
        status=AnalysisJobStatus.PENDING,
        input_metadata={"document_ids": [str(d) for d in req.document_ids]}
    )
    db.add(new_job)
    db.commit()
    
    from src.workers.tasks.analysis_tasks import document_comparison_task
    document_comparison_task.delay(str(new_job.id), [str(d) for d in req.document_ids], str(user.id))
    
    return StandardResponse(
        status="success",
        message="Document comparison job started successfully",
        data={"analysis_id": new_job.id}
    )

@router.get("/{analysis_id}", response_model=StandardResponse[AnalysisJobResponse])
def get_analysis_status(
    analysis_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == analysis_id, AnalysisJob.user_id == user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")
        
    return StandardResponse(status="success", message="Analysis status retrieved", data={
        "id": job.id,
        "analysis_type": job.analysis_type.value,
        "status": job.status.value,
        "result_s3_key": job.result_s3_key,
        "result_md_s3_key": job.result_md_s3_key,
        "error_message": job.error_message
    })

@router.get("/{analysis_id}/download", response_model=StandardResponse[dict])
def get_analysis_download_url(
    analysis_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == analysis_id, AnalysisJob.user_id == user.id).first()
    if not job or job.status != AnalysisJobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Analysis job not completed or not found")
        
    s3 = S3Storage()
    json_url = s3.generate_presigned_url(job.result_s3_key, expiration=3600)
    md_url = s3.generate_presigned_url(job.result_md_s3_key, expiration=3600) if job.result_md_s3_key else None
    
    return StandardResponse(status="success", message="Download URLs generated", data={
        "json_url": json_url,
        "md_url": md_url
    })
