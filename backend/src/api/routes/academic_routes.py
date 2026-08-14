from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.infrastructure.database import get_db
from src.schemas.academic_schema import (
    OrganizationalUnitCreate, OrganizationalUnitRead,
    OfferingCreate, OfferingRead,
    StudyUnitCreate, StudyUnitRead,
    FacultyInfoCreate, FacultyInfoRead
)
from src.models.user_model import User, UserRole
from src.api.middleware.auth_middleware import get_current_user, require_role
from src.repositories.postgres.academic_repository import AcademicRepository
from src.services.academic.academic_service import AcademicService
from src.schemas.response_schema import StandardResponse

router = APIRouter(prefix="/academic", tags=["Academic Organization"])

from src.repositories.redis.cache_repository import CacheRepository

def get_cache_repository() -> CacheRepository:
    return CacheRepository()

def get_academic_service(
    db: Session = Depends(get_db),
    cache_repo: CacheRepository = Depends(get_cache_repository)
) -> AcademicService:
    repo = AcademicRepository(db)
    return AcademicService(repo, cache_repo)

# --- Organizational Units ---
@router.post("/org-units", response_model=StandardResponse[OrganizationalUnitRead], status_code=status.HTTP_201_CREATED)
def create_org_unit(org_unit_in: OrganizationalUnitCreate, service: AcademicService = Depends(get_academic_service), user: User = Depends(require_role([UserRole.ADMIN]))):
    data = service.create_org_unit(org_unit_in)
    return StandardResponse(status="success", message="Organizational Unit created successfully", data=data)

@router.get("/org-units", response_model=StandardResponse[list[OrganizationalUnitRead]])
def list_org_units(service: AcademicService = Depends(get_academic_service), user: User = Depends(get_current_user)):
    data = service.get_org_units()
    return StandardResponse(status="success", message="Organizational Units retrieved successfully", data=data)

@router.get("/org-units/{org_unit_id}", response_model=StandardResponse[OrganizationalUnitRead])
def get_org_unit(org_unit_id: UUID, service: AcademicService = Depends(get_academic_service), user: User = Depends(get_current_user)):
    data = service.get_org_unit(org_unit_id)
    return StandardResponse(status="success", message="Organizational Unit retrieved successfully", data=data)

@router.delete("/org-units/{org_unit_id}", response_model=StandardResponse[OrganizationalUnitRead])
def delete_org_unit(org_unit_id: UUID, service: AcademicService = Depends(get_academic_service), user: User = Depends(require_role([UserRole.ADMIN]))):
    data = service.delete_org_unit(org_unit_id)
    return StandardResponse(status="success", message="Organizational Unit soft-deleted. Cleanup job dispatched.", data=data)

# --- Offerings ---
@router.post("/org-units/{org_unit_id}/offerings", response_model=StandardResponse[OfferingRead], status_code=status.HTTP_201_CREATED)
def create_offering(org_unit_id: UUID, offering_in: OfferingCreate, service: AcademicService = Depends(get_academic_service), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    if offering_in.org_unit_id != org_unit_id:
        offering_in.org_unit_id = org_unit_id
    data = service.create_offering(offering_in)
    return StandardResponse(status="success", message="Offering created successfully", data=data)

@router.get("/org-units/{org_unit_id}/offerings", response_model=StandardResponse[list[OfferingRead]])
def list_offerings(org_unit_id: UUID, service: AcademicService = Depends(get_academic_service), user: User = Depends(get_current_user)):
    data = service.get_offerings(org_unit_id)
    return StandardResponse(status="success", message="Offerings retrieved successfully", data=data)

@router.get("/offerings/{offering_id}", response_model=StandardResponse[OfferingRead])
def get_offering(offering_id: UUID, service: AcademicService = Depends(get_academic_service), user: User = Depends(get_current_user)):
    data = service.get_offering(offering_id)
    return StandardResponse(status="success", message="Offering retrieved successfully", data=data)

@router.delete("/offerings/{offering_id}", response_model=StandardResponse[OfferingRead])
def delete_offering(offering_id: UUID, service: AcademicService = Depends(get_academic_service), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    data = service.delete_offering(offering_id)
    return StandardResponse(status="success", message="Offering deleted successfully", data=data)

# --- Study Units ---
@router.get("/study-units", response_model=StandardResponse[list[StudyUnitRead]])
def list_all_study_units(service: AcademicService = Depends(get_academic_service), user: User = Depends(get_current_user)):
    data = service.get_study_units()
    return StandardResponse(status="success", message="All Study Units retrieved successfully", data=data)

@router.post("/org-units/{org_unit_id}/study-units", response_model=StandardResponse[StudyUnitRead], status_code=status.HTTP_201_CREATED)
def create_study_unit(org_unit_id: UUID, study_unit_in: StudyUnitCreate, service: AcademicService = Depends(get_academic_service), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    if study_unit_in.org_unit_id != org_unit_id:
        study_unit_in.org_unit_id = org_unit_id
    data = service.create_study_unit(study_unit_in)
    return StandardResponse(status="success", message="Study Unit created successfully", data=data)

@router.get("/org-units/{org_unit_id}/study-units", response_model=StandardResponse[list[StudyUnitRead]])
def list_org_study_units(org_unit_id: UUID, service: AcademicService = Depends(get_academic_service), user: User = Depends(get_current_user)):
    data = service.get_study_units(org_unit_id=org_unit_id)
    return StandardResponse(status="success", message="Study Units retrieved successfully", data=data)

@router.get("/offerings/{offering_id}/study-units", response_model=StandardResponse[list[StudyUnitRead]])
def list_study_units(offering_id: UUID, service: AcademicService = Depends(get_academic_service), user: User = Depends(get_current_user)):
    data = service.get_study_units(offering_id=offering_id)
    return StandardResponse(status="success", message="Study Units retrieved successfully", data=data)

@router.post("/study-units/{study_unit_id}/offerings", response_model=StandardResponse[StudyUnitRead], status_code=status.HTTP_200_OK)
def link_offering(study_unit_id: UUID, req: dict, service: AcademicService = Depends(get_academic_service), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    offering_id = UUID(req["offering_id"])
    data = service.link_offering(study_unit_id, offering_id)
    return StandardResponse(status="success", message="Offering linked successfully", data=data)

@router.delete("/study-units/{study_unit_id}/offerings/{offering_id}", response_model=StandardResponse[StudyUnitRead])
def unlink_offering(study_unit_id: UUID, offering_id: UUID, service: AcademicService = Depends(get_academic_service), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    data = service.unlink_offering(study_unit_id, offering_id)
    return StandardResponse(status="success", message="Offering unlinked successfully", data=data)

@router.get("/study-units/{study_unit_id}", response_model=StandardResponse[StudyUnitRead])
def get_study_unit(study_unit_id: UUID, service: AcademicService = Depends(get_academic_service), user: User = Depends(get_current_user)):
    data = service.get_study_unit(study_unit_id)
    return StandardResponse(status="success", message="Study Unit retrieved successfully", data=data)

@router.delete("/study-units/{study_unit_id}", response_model=StandardResponse[StudyUnitRead])
def delete_study_unit(study_unit_id: UUID, service: AcademicService = Depends(get_academic_service), user: User = Depends(require_role([UserRole.ADMIN]))):
    data = service.delete_study_unit(study_unit_id)
    return StandardResponse(status="success", message="Study Unit soft-deleted. Cleanup job dispatched.", data=data)

# --- Prerequisites ---
@router.post("/study-units/{study_unit_id}/prerequisites", response_model=StandardResponse[StudyUnitRead], status_code=status.HTTP_201_CREATED)
def add_prerequisite(study_unit_id: UUID, req: dict, service: AcademicService = Depends(get_academic_service), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    prerequisite_id = UUID(req["prerequisite_id"])
    data = service.add_prerequisite(study_unit_id, prerequisite_id)
    return StandardResponse(status="success", message="Prerequisite added successfully", data=data)

@router.delete("/study-units/{study_unit_id}/prerequisites/{prereq_id}", response_model=StandardResponse[StudyUnitRead])
def remove_prerequisite(study_unit_id: UUID, prereq_id: UUID, service: AcademicService = Depends(get_academic_service), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    data = service.remove_prerequisite(study_unit_id, prereq_id)
    return StandardResponse(status="success", message="Prerequisite removed successfully", data=data)

# --- Faculty ---
@router.post("/offerings/{offering_id}/faculty", response_model=StandardResponse[FacultyInfoRead], status_code=status.HTTP_201_CREATED)
def add_faculty_to_offering(offering_id: UUID, faculty_in: FacultyInfoCreate, service: AcademicService = Depends(get_academic_service), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    if faculty_in.offering_id != offering_id:
        faculty_in.offering_id = offering_id
    data = service.create_faculty(faculty_in)
    return StandardResponse(status="success", message="Faculty added to offering successfully", data=data)

@router.get("/offerings/{offering_id}/faculty", response_model=StandardResponse[list[FacultyInfoRead]])
def list_faculty_for_offering(offering_id: UUID, service: AcademicService = Depends(get_academic_service), user: User = Depends(get_current_user)):
    data = service.get_faculty_for_offering(offering_id)
    return StandardResponse(status="success", message="Faculty retrieved successfully", data=data)

@router.delete("/faculty/{faculty_id}", response_model=StandardResponse[FacultyInfoRead])
def delete_faculty(faculty_id: UUID, service: AcademicService = Depends(get_academic_service), user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))):
    data = service.delete_faculty(faculty_id)
    return StandardResponse(status="success", message="Faculty deleted successfully", data=data)
