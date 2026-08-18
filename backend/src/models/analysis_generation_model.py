import enum
import uuid
from datetime import datetime
from sqlalchemy import String, Enum, Text, ForeignKey, DateTime, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database import Base
from src.models.user_model import utcnow

class AnalysisType(str, enum.Enum):
    FORMULA_SHEET = "FORMULA_SHEET"
    QUESTION_BANK = "QUESTION_BANK"
    CONCEPT_SUMMARY = "CONCEPT_SUMMARY"
    REVISION_NOTES = "REVISION_NOTES"

class AnalysisStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class AnalysisGeneration(Base):
    __tablename__ = "analysis_generations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[AnalysisType] = mapped_column(Enum(AnalysisType), nullable=False)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    topics: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    
    output_s3_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[AnalysisStatus] = mapped_column(Enum(AnalysisStatus), default=AnalysisStatus.PENDING, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
