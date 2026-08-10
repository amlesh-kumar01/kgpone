from uuid import UUID
from fastapi import HTTPException
from src.repositories.postgres.academic_repository import AcademicRepository
from src.schemas.academic_schema import (
    DepartmentCreate, CourseCreate, CourseOfferingCreate,
    FacultyInfoCreate
)
from src.models.academic_model import Department, Course, CourseOffering, FacultyInfo
from src.models.system_model import CleanupJob, DeletionStatus
from src.workers.tasks.cleanup_tasks import cleanup_course_task

class AcademicService:
    def __init__(self, repository: AcademicRepository):
        self.repository = repository

    def create_department(self, dept_in: DepartmentCreate) -> Department:
        dept = self.repository.create_department(dept_in)
        
        # Real-time sync to Neo4j
        import logging
        logger = logging.getLogger("academic_service")
        try:
            from src.repositories.neo4j.graph_repository import Neo4jRepo
            neo4j = Neo4jRepo()
            neo4j.merge_department(dept.code, {"name": dept.name})
            logger.info(f"Synced department {dept.code} to Neo4j")
        except Exception as e:
            logger.warning(f"Failed to sync department to Neo4j: {e}")
            
        return dept

    def get_departments(self) -> list[Department]:
        return self.repository.get_departments()

    def get_department(self, dept_id: UUID) -> Department:
        dept = self.repository.get_department(dept_id)
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found")
        return dept

    def create_course(self, course_in: CourseCreate) -> Course:
        dept = self.repository.get_department(course_in.department_id)
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found")
        return self.repository.create_course(course_in)

    def get_courses(self, department_id: UUID | None = None) -> list[Course]:
        return self.repository.get_courses(department_id)

    def get_course(self, course_id: UUID) -> Course:
        course = self.repository.get_course(course_id)
        if not course or course.is_deleted:
            raise HTTPException(status_code=404, detail="Course not found")
        return course

    def delete_course(self, course_id: UUID):
        course = self.repository.get_course(course_id)
        if not course or course.is_deleted:
            raise HTTPException(status_code=404, detail="Course not found")
            
        # Soft delete
        course.is_deleted = True
        course.deletion_status = DeletionStatus.PENDING
        self.repository.session.commit()
        
        # Create cleanup job
        job = CleanupJob(resource_type="COURSE", resource_id=course_id)
        self.repository.session.add(job)
        self.repository.session.commit()
        self.repository.session.refresh(job)
        
        # Dispatch Celery Task
        cleanup_course_task.delay(str(course_id), str(job.id))
        
        return course

    def add_prerequisite(self, course_id: UUID, prerequisite_id: UUID) -> Course:
        course = self.get_course(course_id)
        prereq = self.get_course(prerequisite_id)
        if not course or not prereq:
            raise HTTPException(status_code=404, detail="Course or prerequisite not found")
        return self.repository.add_prerequisite(course_id, prerequisite_id)

    def remove_prerequisite(self, course_id: UUID, prerequisite_id: UUID) -> Course:
        course = self.get_course(course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        return self.repository.remove_prerequisite(course_id, prerequisite_id)

    def create_offering(self, offering_in: CourseOfferingCreate) -> CourseOffering:
        course = self.repository.get_course(offering_in.course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        return self.repository.create_offering(offering_in)

    def get_offerings(self, course_id: UUID) -> list[CourseOffering]:
        return self.repository.get_offerings(course_id)

    def get_offering(self, offering_id: UUID) -> CourseOffering:
        offering = self.repository.get_offering(offering_id)
        if not offering:
            raise HTTPException(status_code=404, detail="Course Offering not found")
        return offering

    def delete_offering(self, offering_id: UUID):
        offering = self.repository.get_offering(offering_id)
        if not offering:
            raise HTTPException(status_code=404, detail="Course Offering not found")
        self.repository.session.delete(offering)
        self.repository.session.commit()
        return offering

    def create_faculty(self, faculty_in: FacultyInfoCreate) -> FacultyInfo:
        return self.repository.create_faculty_info(faculty_in)

    def get_faculty_for_offering(self, offering_id: UUID) -> list[FacultyInfo]:
        from sqlalchemy import select
        stmt = select(FacultyInfo).where(FacultyInfo.course_offering_id == offering_id)
        return list(self.repository.session.scalars(stmt).all())

    def delete_faculty(self, faculty_id: UUID):
        faculty = self.repository.session.get(FacultyInfo, faculty_id)
        if not faculty:
            raise HTTPException(status_code=404, detail="Faculty not found")
        self.repository.session.delete(faculty)
        self.repository.session.commit()
        return faculty


