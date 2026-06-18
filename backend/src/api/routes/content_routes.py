from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from src.infrastructure.database import get_db
from src.models.user_model import User
from src.models.academic_model import Department, Course, CourseOffering, SemesterType
from src.models.document_model import Document, DocFormat, ProcessingStatus
from src.api.middleware.auth_middleware import get_current_user
from src.repositories.s3.storage_repository import S3Storage
from src.workers.tasks.ingestion_tasks import process_document_task, run_document_ingestion
import logging
import uuid
import re

router = APIRouter(tags=["Content"])
logger = logging.getLogger("content_routes")

class PresignedUrlRequest(BaseModel):
    filename: str
    content_type: str

class PresignedUrlResponse(BaseModel):
    upload_url: str
    file_key: str

class ConfirmUploadRequest(BaseModel):
    file_key: str
    title: str
    description: str | None = None
    course_code: str
    academic_year: str
    content_type: str

@router.post("/presigned-url", response_model=PresignedUrlResponse)
def get_presigned_url(req: PresignedUrlRequest, user: User = Depends(get_current_user)):
    """Generates an S3 presigned URL for direct document upload from the client."""
    s3_storage = S3Storage()
    unique_file_key = f"documents/{user.id}/{uuid.uuid4()}_{req.filename}"
    
    try:
        presigned_data = s3_storage.generate_presigned_url(
            file_key=unique_file_key,
            content_type=req.content_type
        )
        return PresignedUrlResponse(
            upload_url=presigned_data["upload_url"],
            file_key=presigned_data["file_key"]
        )
    except Exception as e:
        logger.error(f"S3 Presigned URL generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate upload target URL"
        )

@router.post("/confirm-upload", status_code=status.HTTP_201_CREATED)
def confirm_upload(
    req: ConfirmUploadRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Called by the client after S3 upload is complete. 
    Resolves course/offering records, registers document metadata, 
    and triggers the background ingestion pipeline.
    """
    # 1. Resolve or create Department ("CSE" as default base)
    dept = db.query(Department).filter(Department.code == "CSE").first()
    if not dept:
        dept = Department(code="CSE", name="Computer Science and Engineering")
        db.add(dept)
        db.commit()
        db.refresh(dept)

    # 2. Resolve or create Course
    course_code = req.course_code.strip().upper()
    course = db.query(Course).filter(Course.code == course_code).first()
    if not course:
        course = Course(
            department_id=dept.id,
            code=course_code,
            title=f"{course_code} Academic Course",
            credits=4
        )
        db.add(course)
        db.commit()
        db.refresh(course)

    # 3. Resolve or create CourseOffering (map academic year string, e.g. "3rd Year" -> 2026/2025/etc)
    digits = re.findall(r"\d+", req.academic_year)
    if digits:
        # Standardize matching to a base academic year
        year_val = 2026 - int(digits[0]) + 1
    else:
        year_val = 2026

    offering = db.query(CourseOffering).filter(
        CourseOffering.course_id == course.id,
        CourseOffering.year == year_val,
        CourseOffering.semester == SemesterType.AUTUMN
    ).first()
    if not offering:
        offering = CourseOffering(
            course_id=course.id,
            year=year_val,
            semester=SemesterType.AUTUMN
        )
        db.add(offering)
        db.commit()
        db.refresh(offering)

    # 4. Map content_type / extension to DocFormat
    file_ext = req.file_key.split(".")[-1].upper() if "." in req.file_key else "PDF"
    doc_format = DocFormat.PDF
    if file_ext in ["PDF", "PPT", "PPTX", "DOC", "DOCX"]:
        doc_format = DocFormat[file_ext]
    else:
        # Failsafe mapping based on MIME type
        ct = req.content_type.lower()
        if "pdf" in ct:
            doc_format = DocFormat.PDF
        elif "ppt" in ct:
            doc_format = DocFormat.PPTX if "pptx" in ct else DocFormat.PPT
        elif "doc" in ct:
            doc_format = DocFormat.DOCX if "docx" in ct else DocFormat.DOC

    # 5. Create Document record
    doc = Document(
        course_offering_id=offering.id,
        uploader_id=user.id,
        title=req.title,
        description=req.description,
        doc_type="NOTES",
        format=doc_format,
        s3_key=req.file_key,
        status=ProcessingStatus.PENDING
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 6. Trigger Document Ingestion Pipeline
    use_celery = False
    try:
        from src.config.settings import Settings
        import redis
        # Set socket_timeout to 1 second so it fails fast if Redis is down
        r = redis.Redis.from_url(Settings.CELERY_BROKER_URL, socket_timeout=1.0)
        r.ping()
        use_celery = True
    except Exception:
        logger.warning("Redis broker is offline. Bypassing Celery and running ingestion in FastAPI background task.")

    if use_celery:
        try:
            process_document_task.delay(str(doc.id))
            logger.info(f"Dispatched document {doc.id} to Celery worker.")
        except Exception as e:
            logger.warning(f"Could not dispatch Celery task: {e}. Falling back to background task.")
            background_tasks.add_task(run_document_ingestion, str(doc.id))
    else:
        background_tasks.add_task(run_document_ingestion, str(doc.id))

    return {"status": "success", "message": "Document record created. Ingestion started.", "document_id": str(doc.id)}

@router.get("/my-content")
def get_my_content(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Retrieves all documents uploaded by the current user."""
    docs = db.query(Document).filter(
        Document.uploader_id == user.id,
        Document.is_deleted == False
    ).all()
    
    response_list = []
    for doc in docs:
        course_code = "GEN101"
        try:
            if doc.course_offering and doc.course_offering.course:
                course_code = doc.course_offering.course.code
        except Exception:
            pass
            
        response_list.append({
            "title": doc.title,
            "course_code": course_code,
            "content_type": f"application/{doc.format.value.lower()}" if doc.format else "application/pdf",
            "status": doc.status.value
        })
        
    return response_list

class QueryRequest(BaseModel):
    query: str
    course_code: str

@router.post("/query")
async def execute_query(req: QueryRequest, user: User = Depends(get_current_user)):
    """Runs the hybrid vector + graph recursive retrieval pipeline and returns the grounded answer."""
    from src.services.rag.retrieval_service import RetrievalService
    from src.services.rag.rerank_service import RerankService
    from src.services.rag.citation_service import CitationService
    from src.services.rag.answer_service import AnswerService

    retriever = RetrievalService()
    reranker = RerankService()
    citer = CitationService()
    generator = AnswerService()

    # 1. Retrieve context
    retrieved_data = await retriever.retrieve_context(req.query, req.course_code)
    chunks = retrieved_data["retrieved_chunks"]

    # 2. Rerank
    ranked = reranker.rerank_chunks(req.query, chunks, top_n=4)

    # 3. Format citations
    citations = citer.format_citations(ranked)

    # 4. Generate response
    answer = generator.generate_answer(req.query, ranked, citations)

    return {
        "answer": answer,
        "citations": citations,
        "graph": retrieved_data["graph_visualization"]
    }

@router.get("/courses")
def get_workspace_courses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Returns all unique courses listed in offerings for selection."""
    from src.models.academic_model import Course
    courses = db.query(Course).filter(Course.is_deleted == False).all()
    return [
        {
            "id": str(c.id),
            "code": c.code,
            "title": c.title
        }
        for c in courses
    ]
