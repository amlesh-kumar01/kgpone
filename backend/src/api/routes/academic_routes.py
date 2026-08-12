from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.infrastructure.database import get_db
from src.schemas.academic_schema import (
    DepartmentCreate, DepartmentRead,
    CourseCreate, CourseRead,
    CourseOfferingCreate, CourseOfferingRead,
    FacultyInfoCreate, FacultyInfoRead
)
from src.models.user_model import User, UserRole
from src.api.middleware.auth_middleware import get_current_user, require_role
from src.repositories.postgres.academic_repository import AcademicRepository
from src.services.academic.academic_service import AcademicService
from src.schemas.response_schema import StandardResponse

router = APIRouter(prefix="/academic", tags=["Academic & Departments"])

from src.repositories.redis.cache_repository import CacheRepository

def get_cache_repository() -> CacheRepository:
    return CacheRepository()

def get_academic_service(
    db: Session = Depends(get_db),
    cache_repo: CacheRepository = Depends(get_cache_repository)
) -> AcademicService:
    repo = AcademicRepository(db)
    return AcademicService(repo, cache_repo)

# --- Departments ---
@router.post("/departments", response_model=StandardResponse[DepartmentRead], status_code=status.HTTP_201_CREATED)
def create_department(dept_in: DepartmentCreate, service: AcademicService = Depends(get_academic_service), user: User = Depends(require_role([UserRole.ADMIN]))):
    data = service.create_department(dept_in)
    return StandardResponse(status="success", message="Department created successfully", data=data)

@router.get("/departments", response_model=StandardResponse[list[DepartmentRead]])
def list_departments(service: AcademicService = Depends(get_academic_service), user: User = Depends(get_current_user)):
    data = service.get_departments()
    return StandardResponse(status="success", message="Departments retrieved successfully", data=data)

@router.get("/departments/{dept_id}", response_model=StandardResponse[DepartmentRead])
def get_department(dept_id: UUID, service: AcademicService = Depends(get_academic_service), user: User = Depends(get_current_user)):
    data = service.get_department(dept_id)
    return StandardResponse(status="success", message="Department retrieved successfully", data=data)

# --- Courses ---
@router.post("/", response_model=StandardResponse[CourseRead], status_code=status.HTTP_201_CREATED)
def create_course(course_in: CourseCreate, service: AcademicService = Depends(get_academic_service), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    data = service.create_course(course_in)
    return StandardResponse(status="success", message="Course created successfully", data=data)

@router.get("/", response_model=StandardResponse[list[CourseRead]])
def list_courses(department_id: UUID | None = None, service: AcademicService = Depends(get_academic_service), user: User = Depends(get_current_user)):
    data = service.get_courses(department_id)
    return StandardResponse(status="success", message="Courses retrieved successfully", data=data)

@router.get("/{course_id}", response_model=StandardResponse[CourseRead])
def get_course(course_id: UUID, service: AcademicService = Depends(get_academic_service), user: User = Depends(get_current_user)):
    data = service.get_course(course_id)
    return StandardResponse(status="success", message="Course retrieved successfully", data=data)

@router.delete("/{course_id}", response_model=StandardResponse[CourseRead])
def delete_course(course_id: UUID, service: AcademicService = Depends(get_academic_service), user: User = Depends(require_role([UserRole.ADMIN]))):
    data = service.delete_course(course_id)
    return StandardResponse(status="success", message="Course soft-deleted. Cleanup job dispatched successfully.", data=data)

# --- Prerequisites ---
@router.post("/{course_id}/prerequisites", response_model=StandardResponse[CourseRead], status_code=status.HTTP_201_CREATED)
def add_course_prerequisite(course_id: UUID, req: dict, service: AcademicService = Depends(get_academic_service), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    # Expecting {"prerequisite_id": "uuid"} in req
    prerequisite_id = UUID(req["prerequisite_id"])
    data = service.add_prerequisite(course_id, prerequisite_id)
    return StandardResponse(status="success", message="Prerequisite added successfully", data=data)

@router.delete("/{course_id}/prerequisites/{prereq_id}", response_model=StandardResponse[CourseRead])
def remove_course_prerequisite(course_id: UUID, prereq_id: UUID, service: AcademicService = Depends(get_academic_service), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    data = service.remove_prerequisite(course_id, prereq_id)
    return StandardResponse(status="success", message="Prerequisite removed successfully", data=data)

# --- Offerings ---
@router.post("/{course_id}/offerings", response_model=StandardResponse[CourseOfferingRead], status_code=status.HTTP_201_CREATED)
def create_offering(offering_in: CourseOfferingCreate, service: AcademicService = Depends(get_academic_service), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    data = service.create_offering(offering_in)
    return StandardResponse(status="success", message="Course offering created successfully", data=data)

@router.get("/{course_id}/offerings", response_model=StandardResponse[list[CourseOfferingRead]])
def list_offerings(course_id: UUID, service: AcademicService = Depends(get_academic_service), user: User = Depends(get_current_user)):
    data = service.get_offerings(course_id)
    return StandardResponse(status="success", message="Course offerings retrieved successfully", data=data)

@router.get("/offerings/{offering_id}", response_model=StandardResponse[CourseOfferingRead])
def get_offering(offering_id: UUID, service: AcademicService = Depends(get_academic_service), user: User = Depends(get_current_user)):
    data = service.get_offering(offering_id)
    return StandardResponse(status="success", message="Course offering retrieved successfully", data=data)

@router.delete("/offerings/{offering_id}", response_model=StandardResponse[CourseOfferingRead])
def delete_offering(offering_id: UUID, service: AcademicService = Depends(get_academic_service), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    data = service.delete_offering(offering_id)
    return StandardResponse(status="success", message="Course offering deleted successfully", data=data)

@router.get("/offerings/{offering_id}/faculty", response_model=StandardResponse[list[FacultyInfoRead]])
def list_faculty_for_offering(offering_id: UUID, service: AcademicService = Depends(get_academic_service), user: User = Depends(get_current_user)):
    data = service.get_faculty_for_offering(offering_id)
    return StandardResponse(status="success", message="Faculty retrieved successfully", data=data)

@router.post("/offerings/{offering_id}/faculty", response_model=StandardResponse[FacultyInfoRead], status_code=status.HTTP_201_CREATED)
def add_faculty_to_offering(offering_id: UUID, faculty_in: FacultyInfoCreate, service: AcademicService = Depends(get_academic_service), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    if faculty_in.course_offering_id != offering_id:
        faculty_in.course_offering_id = offering_id
    data = service.create_faculty(faculty_in)
    return StandardResponse(status="success", message="Faculty added to offering successfully", data=data)

@router.delete("/faculty/{faculty_id}", response_model=StandardResponse[FacultyInfoRead])
def delete_faculty(faculty_id: UUID, service: AcademicService = Depends(get_academic_service), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    data = service.delete_faculty(faculty_id)
    return StandardResponse(status="success", message="Faculty deleted successfully", data=data)

