from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from src.models.document_model import DocFormat, ProcessingStatus

# ----------------- DocumentMetadata Schemas -----------------
class DocumentMetadataBase(BaseModel):
    key: str
    value: str

class DocumentMetadataCreate(DocumentMetadataBase):
    pass

class DocumentMetadataRead(DocumentMetadataBase):
    id: UUID
    document_id: UUID
    model_config = ConfigDict(from_attributes=True)

# ----------------- Document Schemas -----------------
class DocumentBase(BaseModel):
    title: str
    description: str | None = None
    parsing_instructions: str | None = None
    doc_type: str
    format: DocFormat

class DocumentCreate(DocumentBase):
    id: UUID | None = None
    study_unit_id: UUID
    uploader_id: UUID | None = None
    s3_key: str
    s3_prefix: str | None = None
    original_s3_key: str | None = None
    file_size_bytes: int | None = None
    metadata_entries: list[DocumentMetadataCreate] = []

class DocumentRead(DocumentBase):
    id: UUID
    study_unit_id: UUID
    uploader_id: UUID | None
    s3_key: str
    s3_prefix: str | None = None
    original_s3_key: str | None = None
    file_size_bytes: int | None
    status: ProcessingStatus
    qdrant_collection_id: str | None
    created_at: datetime
    updated_at: datetime
    metadata_entries: list[DocumentMetadataRead] = []
    
    model_config = ConfigDict(from_attributes=True)

class DocumentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    parsing_instructions: str | None = None
    status: ProcessingStatus | None = None
    qdrant_collection_id: str | None = None

# ----------------- S3 Upload Schemas -----------------
class PresignedUrlRequest(BaseModel):
    filename: str
    content_type: str
    study_unit_id: UUID

class PresignedUrlResponse(BaseModel):
    upload_url: str
    file_key: str
    document_id: UUID
    s3_prefix: str
    original_s3_key: str

# ----------------- Quiz Schemas -----------------
class QuizGenerationRequest(BaseModel):
    topic: str
    quiz_type: str
    prompt: str

class QuizQuestion(BaseModel):
    question: str
    options: list[str] | None = None
    answer: str
    explanation: str | None = None

class QuizGenerationResponse(BaseModel):
    title: str
    questions: list[QuizQuestion]
