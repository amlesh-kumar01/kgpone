import enum
import uuid
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from src.infrastructure.database import Base
from datetime import datetime, UTC

class DeletionStatus(str, enum.Enum):
    NONE = "NONE"
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class CleanupJob(Base):
    __tablename__ = "cleanup_jobs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. DOCUMENT, COURSE
    resource_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    status: Mapped[DeletionStatus] = mapped_column(String(50), default=DeletionStatus.PENDING)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
