import enum
import uuid
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime, Uuid, Enum as SQLAlchemyEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database import Base
from src.models.user_model import utcnow

class AnalysisJobStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class AnalysisType(str, enum.Enum):
    SUMMARIZE = "SUMMARIZE"
    QUIZ = "QUIZ"
    FORMULA_REVISION = "FORMULA_REVISION"
    PYQ_MAPPING = "PYQ_MAPPING"
    COURSE_SUMMARY = "COURSE_SUMMARY"
    DOCUMENT_COMPARISON = "DOCUMENT_COMPARISON"

class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # E.g., user who triggered the analysis
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    analysis_type: Mapped[AnalysisType] = mapped_column(SQLAlchemyEnum(AnalysisType), nullable=False)
    status: Mapped[AnalysisJobStatus] = mapped_column(SQLAlchemyEnum(AnalysisJobStatus), default=AnalysisJobStatus.PENDING, nullable=False)
    
    # Store parameters like which document(s) it runs on
    input_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    # S3 paths for outputs
    result_s3_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_md_s3_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
