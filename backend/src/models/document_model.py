import enum
import uuid
from datetime import datetime
from sqlalchemy import String, Enum, Text, ForeignKey, DateTime, Uuid, BigInteger, UniqueConstraint, Integer, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database import Base
from src.models.system_model import DeletionStatus
from src.models.user_model import utcnow

class DocFormat(str, enum.Enum):
    PDF = "PDF"
    PPT = "PPT"
    PPTX = "PPTX"
    DOC = "DOC"
    DOCX = "DOCX"

class ProcessingStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_offering_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("course_offerings.id", ondelete="CASCADE"), nullable=False)
    uploader_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsing_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False) # 'PYQ', 'SLIDES', 'NOTES', 'SYLLABUS'
    format: Mapped[DocFormat] = mapped_column(Enum(DocFormat), nullable=False)
    
    # New Phase 1 columns
    s3_prefix: Mapped[str | None] = mapped_column(String(255), nullable=True)
    original_s3_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    manifest_s3_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    parser_used: Mapped[str | None] = mapped_column(String(50), nullable=True)
    parser_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    processing_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    s3_key: Mapped[str] = mapped_column(Text, nullable=False) # Legacy
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    
    status: Mapped[ProcessingStatus] = mapped_column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    qdrant_collection_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deletion_status: Mapped[str] = mapped_column(String(50), default=DeletionStatus.NONE)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    course_offering: Mapped["CourseOffering"] = relationship(
        "CourseOffering", 
        back_populates="documents",
        primaryjoin="Document.course_offering_id == CourseOffering.id"
    )
    uploader: Mapped["User"] = relationship("User", back_populates="documents")
    metadata_entries: Mapped[list["DocumentMetadata"]] = relationship("DocumentMetadata", back_populates="document", cascade="all, delete-orphan")
    
    # Knowledge extractions (Phase 3)
    extracted_entities: Mapped[list["ExtractedEntity"]] = relationship("ExtractedEntity", back_populates="document", cascade="all, delete-orphan")
    extracted_formulas: Mapped[list["ExtractedFormula"]] = relationship("ExtractedFormula", back_populates="document", cascade="all, delete-orphan")
    extracted_questions: Mapped[list["ExtractedQuestion"]] = relationship("ExtractedQuestion", back_populates="document", cascade="all, delete-orphan")


class DocumentMetadata(Base):
    __tablename__ = "document_metadata"
    __table_args__ = (UniqueConstraint('document_id', 'key'),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationship
    document: Mapped["Document"] = relationship("Document", back_populates="metadata_entries")
