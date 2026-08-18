from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.infrastructure.database import get_db
from src.schemas.document_schema import (
    DocumentCreate, DocumentRead, DocumentUpdate,
    PresignedUrlRequest, PresignedUrlResponse,
    QuizGenerationRequest, QuizGenerationResponse
)
from src.repositories.postgres.document_repository import DocumentRepository
from src.services.ingestion.upload_manager.document_service import DocumentService
from src.models.user_model import User, UserRole
from src.api.middleware.auth_middleware import get_current_user, require_role
from src.schemas.response_schema import StandardResponse

router = APIRouter(prefix="/documents", tags=["Documents"])

from src.repositories.redis.cache_repository import CacheRepository

def get_cache_repository() -> CacheRepository:
    return CacheRepository()

def get_document_service(
    db: Session = Depends(get_db),
    cache_repo: CacheRepository = Depends(get_cache_repository)
) -> DocumentService:
    repo = DocumentRepository(db)
    return DocumentService(repo, cache_repo)

@router.post("/presigned-url", response_model=StandardResponse[PresignedUrlResponse], status_code=status.HTTP_201_CREATED)
def get_presigned_url(req: PresignedUrlRequest, service: DocumentService = Depends(get_document_service), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    data = service.generate_upload_url(user.id, req.filename, req.content_type, req.study_unit_id)
    return StandardResponse(status="success", message="Presigned URL generated successfully", data=data)

@router.get("/", response_model=StandardResponse[list[DocumentRead]])
def list_documents(service: DocumentService = Depends(get_document_service), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    data = service.get_all_documents()
    return StandardResponse(status="success", message="Documents retrieved successfully", data=data)

@router.post("/", response_model=StandardResponse[DocumentRead], status_code=status.HTTP_201_CREATED)
def upload_document(doc_in: DocumentCreate, service: DocumentService = Depends(get_document_service), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    data = service.upload_document(doc_in)
    return StandardResponse(status="success", message="Document metadata saved successfully", data=data)

@router.get("/study-unit/{study_unit_id}", response_model=StandardResponse[list[DocumentRead]])
def list_documents_for_study_unit(study_unit_id: UUID, service: DocumentService = Depends(get_document_service), user: User = Depends(get_current_user)):
    data = service.get_documents_for_study_unit(study_unit_id)
    return StandardResponse(status="success", message="Documents retrieved successfully", data=data)

@router.get("/{document_id}", response_model=StandardResponse[DocumentRead])
def get_document(document_id: UUID, service: DocumentService = Depends(get_document_service), user: User = Depends(get_current_user)):
    data = service.get_document(document_id)
    return StandardResponse(status="success", message="Document retrieved successfully", data=data)

@router.get("/{document_id}/download", response_model=StandardResponse[str])
def download_document(document_id: UUID, service: DocumentService = Depends(get_document_service), user: User = Depends(get_current_user)):
    url = service.generate_download_url(document_id)
    return StandardResponse(status="success", message="Download URL generated", data=url)

@router.patch("/{document_id}", response_model=StandardResponse[DocumentRead])
def update_document(document_id: UUID, doc_update: DocumentUpdate, service: DocumentService = Depends(get_document_service), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    data = service.update_document(document_id, doc_update)
    return StandardResponse(status="success", message="Document updated successfully. Re-ingestion started.", data=data)

@router.delete("/{document_id}", response_model=StandardResponse[DocumentRead])
def delete_document(document_id: UUID, service: DocumentService = Depends(get_document_service), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    data = service.delete_document(document_id)
    return StandardResponse(status="success", message="Document soft-deleted. Cleanup job dispatched successfully.", data=data)

class RetryStageRequest(BaseModel):
    stage: str

@router.post("/{document_id}/retry-stage", response_model=StandardResponse[str])
def retry_document_stage(
    document_id: UUID, 
    req: RetryStageRequest,
    db: Session = Depends(get_db), 
    user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))
):
    from src.models.ingestion_job_model import IngestionJob, IngestionStage, IngestionJobStatus
    import src.workers.tasks.ingestion_tasks as tasks

    # 1. Map string to enum
    try:
        stage_enum = IngestionStage(req.stage.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid stage name")

    # 2. Find the job
    job = db.query(IngestionJob).filter_by(document_id=document_id, stage=stage_enum).first()
    if not job:
        raise HTTPException(status_code=404, detail="Stage job not found for this document")

    # 3. Mark as pending
    job.status = IngestionJobStatus.PENDING
    job.error_message = None
    db.commit()

    # 4. Dispatch the correct task
    doc_id_str = str(document_id)
    if stage_enum == IngestionStage.PARSE: tasks.parse_document_task.delay(doc_id_str)
    elif stage_enum == IngestionStage.AST: tasks.build_canonical_ast_task.delay(doc_id_str)
    elif stage_enum == IngestionStage.ENTITY: tasks.extract_entities_task.delay(doc_id_str)
    elif stage_enum == IngestionStage.RELATION: tasks.extract_relations_task.delay(doc_id_str)
    elif stage_enum == IngestionStage.CHUNK: tasks.build_chunks_task.delay(doc_id_str)
    elif stage_enum == IngestionStage.EMBED: tasks.index_qdrant_task.delay(doc_id_str)
    elif stage_enum == IngestionStage.GRAPH: tasks.build_neo4j_task.delay(doc_id_str)
    elif stage_enum == IngestionStage.MANIFEST: tasks.finalize_manifest_task.delay(doc_id_str)

    return StandardResponse(status="success", message=f"Stage {stage_enum.value} retry dispatched", data="")

@router.post("/{document_id}/quiz", response_model=StandardResponse[QuizGenerationResponse])
def generate_document_quiz(
    document_id: UUID, 
    req: QuizGenerationRequest,
    db: Session = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    from src.repositories.qdrant.vector_repository import QdrantRepository
    from src.infrastructure.llm_factory import LLMFactory
    from langchain_core.prompts import ChatPromptTemplate
    import asyncio
    import json
    
    # 1. Query Qdrant for topic context
    repo = QdrantRepository()
    embedder = LLMFactory().get_embedder()
    topic_embedding = asyncio.run(embedder.embed_query(req.topic))
    filter_dict = {"document_id": str(document_id)}
    
    results = repo.search("documents", topic_embedding, limit=5, filter_dict=filter_dict)
    context_text = "\n\n".join([r.payload.get("text", "") for r in results])
    
    # 2. Use LLM to generate Quiz
    llm = LLMFactory().get_llm(temperature=0.7)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert tutor. Generate a quiz based on the following text context. "
                   "The user wants a quiz about '{topic}' of type '{quiz_type}'. "
                   "User custom instructions: {prompt}\n\n"
                   "You MUST respond ONLY with valid JSON matching this schema: "
                   "{{\"title\": \"Quiz Title\", \"questions\": [{{\"question\": \"...\", \"options\": [\"A\", \"B\", \"C\", \"D\"], \"answer\": \"...\", \"explanation\": \"...\"}}]}} "
                   "Omit 'options' if it's not a multiple choice quiz."),
        ("user", "Context:\n{context}")
    ])
    
    chain = prompt | llm
    try:
        res = asyncio.run(chain.ainvoke({"topic": req.topic, "quiz_type": req.quiz_type, "prompt": req.prompt, "context": context_text}))
        
        # Parse JSON
        content = res.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        quiz_data = json.loads(content.strip())
        
        return StandardResponse(status="success", message="Quiz generated successfully", data=QuizGenerationResponse(**quiz_data))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")
