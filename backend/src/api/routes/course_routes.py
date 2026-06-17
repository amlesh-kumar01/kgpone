from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.infrastructure.database import get_db
from src.schemas.course_schema import (
    DepartmentCreate, DepartmentRead,
    CourseCreate, CourseRead,
    CourseOfferingCreate, CourseOfferingRead,
    FacultyInfoCreate, FacultyInfoRead
)
from src.models.user_model import User, UserRole
from src.api.middleware.auth_middleware import get_current_user, require_role
from src.repositories.postgres.course_repository import CourseRepository
from src.services.academic.course_service import CourseService
from src.schemas.response_schema import StandardResponse

router = APIRouter(prefix="/courses", tags=["Courses & Departments"])

def get_course_service(db: Session = Depends(get_db)) -> CourseService:
    repo = CourseRepository(db)
    return CourseService(repo)

# --- Departments ---
@router.post("/departments", response_model=StandardResponse[DepartmentRead], status_code=status.HTTP_201_CREATED)
def create_department(dept_in: DepartmentCreate, service: CourseService = Depends(get_course_service), user: User = Depends(require_role([UserRole.ADMIN]))):
    data = service.create_department(dept_in)
    return StandardResponse(status="success", message="Department created successfully", data=data)

@router.get("/departments", response_model=StandardResponse[list[DepartmentRead]])
def list_departments(service: CourseService = Depends(get_course_service), user: User = Depends(get_current_user)):
    data = service.get_departments()
    return StandardResponse(status="success", message="Departments retrieved successfully", data=data)

@router.get("/departments/{dept_id}", response_model=StandardResponse[DepartmentRead])
def get_department(dept_id: UUID, service: CourseService = Depends(get_course_service), user: User = Depends(get_current_user)):
    data = service.get_department(dept_id)
    return StandardResponse(status="success", message="Department retrieved successfully", data=data)

# --- Courses ---
@router.post("/", response_model=StandardResponse[CourseRead], status_code=status.HTTP_201_CREATED)
def create_course(course_in: CourseCreate, service: CourseService = Depends(get_course_service), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    data = service.create_course(course_in)
    return StandardResponse(status="success", message="Course created successfully", data=data)

@router.get("/", response_model=StandardResponse[list[CourseRead]])
def list_courses(department_id: UUID | None = None, service: CourseService = Depends(get_course_service), user: User = Depends(get_current_user)):
    data = service.get_courses(department_id)
    return StandardResponse(status="success", message="Courses retrieved successfully", data=data)

@router.get("/{course_id}", response_model=StandardResponse[CourseRead])
def get_course(course_id: UUID, service: CourseService = Depends(get_course_service), user: User = Depends(get_current_user)):
    data = service.get_course(course_id)
    return StandardResponse(status="success", message="Course retrieved successfully", data=data)

# --- Offerings ---
@router.post("/{course_id}/offerings", response_model=StandardResponse[CourseOfferingRead], status_code=status.HTTP_201_CREATED)
def create_offering(offering_in: CourseOfferingCreate, service: CourseService = Depends(get_course_service), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    data = service.create_offering(offering_in)
    return StandardResponse(status="success", message="Course offering created successfully", data=data)

@router.get("/{course_id}/offerings", response_model=StandardResponse[list[CourseOfferingRead]])
def list_offerings(course_id: UUID, service: CourseService = Depends(get_course_service), user: User = Depends(get_current_user)):
    data = service.get_offerings(course_id)
    return StandardResponse(status="success", message="Course offerings retrieved successfully", data=data)

@router.post("/offerings/{offering_id}/faculty", response_model=StandardResponse[FacultyInfoRead], status_code=status.HTTP_201_CREATED)
def add_faculty_to_offering(faculty_in: FacultyInfoCreate, service: CourseService = Depends(get_course_service), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    data = service.create_faculty(faculty_in)
    return StandardResponse(status="success", message="Faculty added to offering successfully", data=data)

