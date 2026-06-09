import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, Enum, Text, ForeignKey, DateTime, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    PUBLISHER = "PUBLISHER"
    STUDENT = "STUDENT"

class ContentStatus(str, enum.Enum):
    PUBLISHED = "PUBLISHED"
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"

def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    
    # Dynamic capability flag to allow specific students to upload content
    can_upload: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=utcnow, 
        onupdate=utcnow, 
        nullable=False
    )

    contents: Mapped[list["Content"]] = relationship("Content", back_populates="uploader")


class Content(Base):
    __tablename__ = "content"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_url: Mapped[str] = mapped_column(String, nullable=False)
    content_type: Mapped[str] = mapped_column(String, nullable=False)
    course_code: Mapped[str] = mapped_column(String, nullable=False)
    academic_year: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[ContentStatus] = mapped_column(Enum(ContentStatus), default=ContentStatus.PUBLISHED, nullable=False)
    
    uploader_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=utcnow, 
        onupdate=utcnow, 
        nullable=False
    )

    uploader: Mapped["User"] = relationship("User", back_populates="contents")
