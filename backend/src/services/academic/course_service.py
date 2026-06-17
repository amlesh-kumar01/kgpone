from uuid import UUID
from fastapi import HTTPException
from src.repositories.postgres.course_repository import CourseRepository
from src.schemas.course_schema import (
    DepartmentCreate, CourseCreate, CourseOfferingCreate,
    FacultyInfoCreate
)
from src.models.course_model import Department, Course, CourseOffering, FacultyInfo

class CourseService:
    def __init__(self, repository: CourseRepository):
        self.repository = repository

    def create_department(self, dept_in: DepartmentCreate) -> Department:
        return self.repository.create_department(dept_in)

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
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        return course

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

    def create_faculty(self, faculty_in: FacultyInfoCreate) -> FacultyInfo:
        return self.repository.create_faculty_info(faculty_in)

