from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

# ----------------- Organizational Unit Schemas -----------------
class OrganizationalUnitBase(BaseModel):
    code: str
    name: str

class OrganizationalUnitCreate(OrganizationalUnitBase):
    pass

class OrganizationalUnitRead(OrganizationalUnitBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# ----------------- Offering Schemas -----------------
class OfferingBase(BaseModel):
    code: str
    name: str

class OfferingCreate(OfferingBase):
    org_unit_id: UUID | None = None

class OfferingRead(OfferingBase):
    id: UUID
    org_unit_id: UUID
    model_config = ConfigDict(from_attributes=True)

# ----------------- Study Unit Schemas -----------------
class StudyUnitBase(BaseModel):
    code: str
    name: str
    description: str | None = None
    credits: int | None = 0

class StudyUnitCreate(StudyUnitBase):
    org_unit_id: UUID | None = None

class StudyUnitRead(StudyUnitBase):
    id: UUID
    org_unit_id: UUID
    created_at: datetime
    updated_at: datetime
    offerings: list[OfferingRead] = []
    prerequisites: list[StudyUnitBase] = []
    model_config = ConfigDict(from_attributes=True)

class StudyUnitPrerequisiteAdd(BaseModel):
    prerequisite_id: UUID

# ----------------- FacultyInfo Schemas -----------------
class FacultyInfoBase(BaseModel):
    name: str
    email: str | None = None
    role: str
    office_hours: str | None = None

class FacultyInfoCreate(FacultyInfoBase):
    offering_id: UUID

class FacultyInfoRead(FacultyInfoBase):
    id: UUID
    offering_id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
