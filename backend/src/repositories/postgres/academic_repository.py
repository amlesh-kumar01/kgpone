from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.models.academic_model import Department, Course, CourseOffering, FacultyInfo
from src.schemas.academic_schema import (
    DepartmentCreate, CourseCreate, CourseOfferingCreate,
    FacultyInfoCreate
)

class AcademicRepository:
    def __init__(self, session: Session):
        self.session = session

    # --- Department ---
    def get_department(self, dept_id: UUID) -> Department | None:
        return self.session.get(Department, dept_id)

    def get_departments(self) -> list[Department]:
        return list(self.session.scalars(select(Department)).all())

    def create_department(self, dept_in: DepartmentCreate) -> Department:
        dept = Department(code=dept_in.code, name=dept_in.name)
        self.session.add(dept)
        self.session.commit()
        self.session.refresh(dept)
        return dept

    # --- Course ---
    def get_course(self, course_id: UUID) -> Course | None:
        return self.session.get(Course, course_id)

    def get_courses(self, department_id: UUID | None = None) -> list[Course]:
        stmt = select(Course)
        if department_id:
            stmt = stmt.where(Course.department_id == department_id)
        return list(self.session.scalars(stmt).all())

    def create_course(self, course_in: CourseCreate) -> Course:
        course = Course(
            department_id=course_in.department_id,
            code=course_in.code,
            title=course_in.title,
            description=course_in.description,
            credits=course_in.credits
        )
        self.session.add(course)
        self.session.commit()
        self.session.refresh(course)
        return course

    # --- CourseOffering ---
    def get_offering(self, offering_id: UUID) -> CourseOffering | None:
        return self.session.get(CourseOffering, offering_id)

    def get_offerings(self, course_id: UUID) -> list[CourseOffering]:
        stmt = select(CourseOffering).where(CourseOffering.course_id == course_id)
        return list(self.session.scalars(stmt).all())

    def create_offering(self, offering_in: CourseOfferingCreate) -> CourseOffering:
        offering = CourseOffering(
            course_id=offering_in.course_id,
            year=offering_in.year,
            semester=offering_in.semester
        )
        self.session.add(offering)
        self.session.commit()
        self.session.refresh(offering)
        return offering

    # --- FacultyInfo ---
    def create_faculty_info(self, faculty_in: FacultyInfoCreate) -> FacultyInfo:
        faculty = FacultyInfo(
            course_offering_id=faculty_in.course_offering_id,
            name=faculty_in.name,
            email=faculty_in.email,
            role=faculty_in.role,
            office_hours=faculty_in.office_hours
        )
        self.session.add(faculty)
        self.session.commit()
        self.session.refresh(faculty)
        return faculty

