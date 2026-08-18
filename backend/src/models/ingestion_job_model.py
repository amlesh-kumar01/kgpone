import enum
import uuid
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime, Uuid, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database import Base
from src.models.user_model import utcnow

class IngestionStage(str, enum.Enum):
    PARSE = "PARSE"
    AST = "AST"
    CHUNK = "CHUNK"
    EMBED = "EMBED"
    ENTITY = "ENTITY"
    RELATION = "RELATION"
    GRAPH = "GRAPH"
    MANIFEST = "MANIFEST"

class IngestionJobStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    stage: Mapped[IngestionStage] = mapped_column(SQLAlchemyEnum(IngestionStage), nullable=False)
    status: Mapped[IngestionJobStatus] = mapped_column(SQLAlchemyEnum(IngestionJobStatus), default=IngestionJobStatus.PENDING, nullable=False)
    
    input_s3_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_s3_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
