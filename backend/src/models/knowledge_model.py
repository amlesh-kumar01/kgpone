import uuid
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, Uuid, Float, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database import Base
from src.models.user_model import utcnow

class ExtractedEntity(Base):
    __tablename__ = "extracted_entities"
    
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    canonical_name: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    
    document = relationship("Document", back_populates="extracted_entities")

class ExtractedFormula(Base):
    __tablename__ = "extracted_formulas"
    
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    latex: Mapped[str] = mapped_column(Text, nullable=False)
    equation_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    
    document = relationship("Document", back_populates="extracted_formulas")

class ExtractedQuestion(Base):
    __tablename__ = "extracted_questions"
    
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    question_type: Mapped[str] = mapped_column(String(100), nullable=False)
    marks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    exam: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    
    document = relationship("Document", back_populates="extracted_questions")
