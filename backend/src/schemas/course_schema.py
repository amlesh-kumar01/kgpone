from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from src.models.course_model import SemesterType

# ----------------- Department Schemas -----------------
class DepartmentBase(BaseModel):
    code: str
    name: str

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentRead(DepartmentBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# ----------------- Course Schemas -----------------
class CourseBase(BaseModel):
    code: str
    title: str
    description: str | None = None
    credits: int | None = None

class CourseCreate(CourseBase):
    department_id: UUID

class CourseRead(CourseBase):
    id: UUID
    department_id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# ----------------- CourseOffering Schemas -----------------
class CourseOfferingBase(BaseModel):
    year: int
    semester: SemesterType

class CourseOfferingCreate(CourseOfferingBase):
    course_id: UUID

class CourseOfferingRead(CourseOfferingBase):
    id: UUID
    course_id: UUID
    model_config = ConfigDict(from_attributes=True)

# ----------------- FacultyInfo Schemas -----------------
class FacultyInfoBase(BaseModel):
    name: str
    email: str | None = None
    role: str
    office_hours: str | None = None

class FacultyInfoCreate(FacultyInfoBase):
    course_offering_id: UUID

class FacultyInfoRead(FacultyInfoBase):
    id: UUID
    course_offering_id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
