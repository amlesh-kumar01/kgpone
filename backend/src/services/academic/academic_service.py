from uuid import UUID
from fastapi import HTTPException
from src.repositories.postgres.academic_repository import AcademicRepository
from src.schemas.academic_schema import (
    OrganizationalUnitCreate, OfferingCreate, StudyUnitCreate,
    FacultyInfoCreate
)
from src.models.academic_model import OrganizationalUnit, Offering, StudyUnit, FacultyInfo
from src.models.system_model import CleanupJob, DeletionStatus
from src.workers.tasks.cleanup_tasks import cleanup_study_unit_task, cleanup_org_unit_task
from src.repositories.redis.cache_repository import CacheRepository
from src.schemas.academic_schema import OrganizationalUnitRead, OfferingRead, StudyUnitRead

class AcademicService:
    def __init__(self, repository: AcademicRepository, cache_repo: CacheRepository):
        self.repository = repository
        self.cache_repo = cache_repo

    # --- Organizational Units ---
    def create_org_unit(self, org_unit_in: OrganizationalUnitCreate) -> OrganizationalUnit:
        org_unit = self.repository.create_org_unit(org_unit_in)
        self.cache_repo.delete("academic:org_units:v1")
        return org_unit

    def get_org_units(self):
        cache_key = "academic:org_units:v1"
        cached = self.cache_repo.get(cache_key)
        if cached is not None:
            return cached

        org_units = self.repository.get_org_units()
        # filter out soft-deleted
        org_units = [ou for ou in org_units if not ou.is_deleted]
        serialized = [OrganizationalUnitRead.model_validate(o).model_dump(mode="json") for o in org_units]
        self.cache_repo.set(cache_key, serialized, ttl=3600)
        return org_units

    def get_org_unit(self, org_unit_id: UUID) -> OrganizationalUnit:
        org_unit = self.repository.get_org_unit(org_unit_id)
        if not org_unit or org_unit.is_deleted:
            raise HTTPException(status_code=404, detail="Organizational Unit not found")
        return org_unit

    def delete_org_unit(self, org_unit_id: UUID):
        org_unit = self.repository.get_org_unit(org_unit_id)
        if not org_unit or org_unit.is_deleted:
            raise HTTPException(status_code=404, detail="Organizational Unit not found")
            
        org_unit.is_deleted = True
        org_unit.deletion_status = DeletionStatus.PENDING
        self.repository.session.commit()
        
        job = CleanupJob(resource_type="ORG_UNIT", resource_id=org_unit_id)
        self.repository.session.add(job)
        self.repository.session.commit()
        self.repository.session.refresh(job)
        
        cleanup_org_unit_task.delay(str(org_unit_id), str(job.id))
        
        self.cache_repo.delete("academic:org_units:v1")
        self.cache_repo.delete_pattern("academic:offerings:v1:*")
        self.cache_repo.delete_pattern("academic:study_units:v1:*")
        
        return org_unit

    # --- Offerings ---
    def create_offering(self, offering_in: OfferingCreate) -> Offering:
        org_unit = self.repository.get_org_unit(offering_in.org_unit_id)
        if not org_unit or org_unit.is_deleted:
            raise HTTPException(status_code=404, detail="Organizational Unit not found")
        offering = self.repository.create_offering(offering_in)
        self.cache_repo.delete_pattern("academic:offerings:v1:*")
        return offering

    def get_offerings(self, org_unit_id: UUID | None = None):
        cache_key = f"academic:offerings:v1:org_unit:{org_unit_id}" if org_unit_id else "academic:offerings:v1:all"
        cached = self.cache_repo.get(cache_key)
        if cached is not None:
            return cached

        offerings = self.repository.get_offerings(org_unit_id)
        serialized = [OfferingRead.model_validate(o).model_dump(mode="json") for o in offerings]
        self.cache_repo.set(cache_key, serialized, ttl=3600)
        return offerings

    def get_offering(self, offering_id: UUID) -> Offering:
        offering = self.repository.get_offering(offering_id)
        if not offering:
            raise HTTPException(status_code=404, detail="Offering not found")
        return offering

    def delete_offering(self, offering_id: UUID):
        offering = self.repository.get_offering(offering_id)
        if not offering:
            raise HTTPException(status_code=404, detail="Offering not found")
        self.repository.session.delete(offering)
        self.repository.session.commit()
        self.cache_repo.delete_pattern("academic:offerings:v1:*")
        return offering

    # --- Study Units ---
    def create_study_unit(self, study_unit_in: StudyUnitCreate) -> StudyUnit:
        org_unit = self.repository.get_org_unit(study_unit_in.org_unit_id)
        if not org_unit or org_unit.is_deleted:
            raise HTTPException(status_code=404, detail="Organizational Unit not found")
        study_unit = self.repository.create_study_unit(study_unit_in)
        self.cache_repo.delete_pattern("academic:study_units:v1:*")
        return study_unit

    def get_study_units(self, org_unit_id: UUID | None = None, offering_id: UUID | None = None):
        cache_key = f"academic:study_units:v1:org_unit:{org_unit_id}:offering:{offering_id}"
        cached = self.cache_repo.get(cache_key)
        if cached is not None:
            return cached

        study_units = self.repository.get_study_units(org_unit_id, offering_id)
        study_units = [su for su in study_units if not su.is_deleted]
        serialized = [StudyUnitRead.model_validate(c).model_dump(mode="json") for c in study_units]
        self.cache_repo.set(cache_key, serialized, ttl=3600)
        return study_units

    def get_study_unit(self, study_unit_id: UUID) -> StudyUnit:
        study_unit = self.repository.get_study_unit(study_unit_id)
        if not study_unit or study_unit.is_deleted:
            raise HTTPException(status_code=404, detail="Study Unit not found")
        return study_unit

    def delete_study_unit(self, study_unit_id: UUID):
        study_unit = self.repository.get_study_unit(study_unit_id)
        if not study_unit or study_unit.is_deleted:
            raise HTTPException(status_code=404, detail="Study Unit not found")
            
        study_unit.is_deleted = True
        study_unit.deletion_status = DeletionStatus.PENDING
        self.repository.session.commit()
        
        job = CleanupJob(resource_type="STUDY_UNIT", resource_id=study_unit_id)
        self.repository.session.add(job)
        self.repository.session.commit()
        self.repository.session.refresh(job)
        
        cleanup_study_unit_task.delay(str(study_unit_id), str(job.id))
        
        self.cache_repo.delete_pattern("academic:study_units:v1:*")
        
        return study_unit

    def link_offering(self, study_unit_id: UUID, offering_id: UUID) -> StudyUnit:
        study_unit = self.repository.link_offering(study_unit_id, offering_id)
        self.cache_repo.delete_pattern("academic:study_units:v1:*")
        return study_unit

    def unlink_offering(self, study_unit_id: UUID, offering_id: UUID) -> StudyUnit:
        study_unit = self.repository.unlink_offering(study_unit_id, offering_id)
        self.cache_repo.delete_pattern("academic:study_units:v1:*")
        return study_unit

    def add_prerequisite(self, study_unit_id: UUID, prerequisite_id: UUID) -> StudyUnit:
        study_unit = self.get_study_unit(study_unit_id)
        prereq = self.get_study_unit(prerequisite_id)
        if not study_unit or not prereq:
            raise HTTPException(status_code=404, detail="Study Unit or prerequisite not found")
        return self.repository.add_prerequisite(study_unit_id, prerequisite_id)

    def remove_prerequisite(self, study_unit_id: UUID, prerequisite_id: UUID) -> StudyUnit:
        study_unit = self.get_study_unit(study_unit_id)
        if not study_unit:
            raise HTTPException(status_code=404, detail="Study Unit not found")
        return self.repository.remove_prerequisite(study_unit_id, prerequisite_id)


    # --- Faculty ---
    def create_faculty(self, faculty_in: FacultyInfoCreate) -> FacultyInfo:
        return self.repository.create_faculty_info(faculty_in)

    def get_faculty_for_offering(self, offering_id: UUID) -> list[FacultyInfo]:
        from sqlalchemy import select
        stmt = select(FacultyInfo).where(FacultyInfo.offering_id == offering_id)
        return list(self.repository.session.scalars(stmt).all())

    def delete_faculty(self, faculty_id: UUID):
        faculty = self.repository.session.get(FacultyInfo, faculty_id)
        if not faculty:
            raise HTTPException(status_code=404, detail="Faculty not found")
        self.repository.session.delete(faculty)
        self.repository.session.commit()
        return faculty
