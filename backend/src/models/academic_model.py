import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, Text, ForeignKey, DateTime, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database import Base
from src.models.system_model import DeletionStatus
from src.models.user_model import utcnow

class OrganizationalUnit(Base):
    __tablename__ = "organizational_units"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deletion_status: Mapped[str] = mapped_column(String(50), default=DeletionStatus.NONE)

    # Relationship
    offerings: Mapped[list["Offering"]] = relationship("Offering", back_populates="org_unit", cascade="all, delete-orphan")
    study_units: Mapped[list["StudyUnit"]] = relationship("StudyUnit", back_populates="org_unit", cascade="all, delete-orphan")

class OfferingStudyUnit(Base):
    __tablename__ = "offering_study_units"
    __table_args__ = (UniqueConstraint('offering_id', 'study_unit_id'),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offering_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("offerings.id", ondelete="CASCADE"), nullable=False)
    study_unit_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("study_units.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Offering(Base):
    __tablename__ = "offerings"
    __table_args__ = (UniqueConstraint('org_unit_id', 'code'),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_unit_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("organizational_units.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Relationships
    org_unit: Mapped["OrganizationalUnit"] = relationship("OrganizationalUnit", back_populates="offerings")
    faculty: Mapped[list["FacultyInfo"]] = relationship("FacultyInfo", back_populates="offering", cascade="all, delete-orphan")
    study_units: Mapped[list["StudyUnit"]] = relationship(
        "StudyUnit",
        secondary="offering_study_units",
        back_populates="offerings"
    )

class StudyUnit(Base):
    __tablename__ = "study_units"
    __table_args__ = (UniqueConstraint('org_unit_id', 'code'),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_unit_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("organizational_units.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    credits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deletion_status: Mapped[str] = mapped_column(String(50), default=DeletionStatus.NONE)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    org_unit: Mapped["OrganizationalUnit"] = relationship("OrganizationalUnit", back_populates="study_units")
    offerings: Mapped[list["Offering"]] = relationship(
        "Offering",
        secondary="offering_study_units",
        back_populates="study_units"
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document", 
        back_populates="study_unit", 
        cascade="all, delete-orphan",
        primaryjoin="StudyUnit.id == Document.study_unit_id"
    )

    prerequisites: Mapped[list["StudyUnit"]] = relationship(
        "StudyUnit",
        secondary="study_unit_prerequisites",
        primaryjoin="StudyUnit.id==StudyUnitPrerequisite.study_unit_id",
        secondaryjoin="StudyUnit.id==StudyUnitPrerequisite.prerequisite_id",
        backref="prerequisite_for"
    )

class StudyUnitPrerequisite(Base):
    __tablename__ = "study_unit_prerequisites"
    __table_args__ = (UniqueConstraint('study_unit_id', 'prerequisite_id'),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_unit_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("study_units.id", ondelete="CASCADE"), nullable=False)
    prerequisite_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("study_units.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class FacultyInfo(Base):
    __tablename__ = "faculty_info"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offering_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("offerings.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(100), nullable=False) # 'Professor', 'TA', 'Coordinator'
    office_hours: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # Relationship
    offering: Mapped["Offering"] = relationship("Offering", back_populates="faculty")
