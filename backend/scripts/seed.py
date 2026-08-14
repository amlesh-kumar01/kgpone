import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import logging
from src.infrastructure.database import SessionLocal, Base, engine
from src.models.user_model import User, UserRole
from src.models.academic_model import Department, Course, CourseOffering, SemesterType, FacultyInfo
from src.models.document_model import Document, DocumentMetadata
from src.models.system_model import CleanupJob
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()

def get_password_hash(password: str) -> str:
    return password_hash.hash(password)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

def init_db():
    logger.info("Dropping all existing database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created successfully.")

def seed_data():
    db = SessionLocal()
    try:
        # Check if Admin already exists
        admin = db.query(User).filter(User.email == "aman@kgpone.edu").first()
        if not admin:
            logger.info("Creating default Admin user (aman@kgpone.edu / aman123)...")
            admin = User(
                email="aman@kgpone.edu",
                hashed_password=get_password_hash("aman123"),
                full_name="Aman",
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True
            )
            db.add(admin)
            db.commit()
        else:
            logger.info("Force-updating default Admin user password...")
            admin.hashed_password = get_password_hash("aman123")
            admin.full_name = "Aman"
            db.commit()

        # Check if Student already exists
        student = db.query(User).filter(User.email == "student@kgpone.edu").first()
        if not student:
            logger.info("Creating default Student user (student@kgpone.edu / student123)...")
            student = User(
                email="student@kgpone.edu",
                hashed_password=get_password_hash("student123"),
                full_name="Test Student",
                role=UserRole.STUDENT,
                is_active=True
            )
            db.add(student)
            db.commit()
        else:
            logger.info("Force-updating default Student user password...")
            student.hashed_password = get_password_hash("student123")
            student.full_name = "Test Student"
            db.commit()

        # Check if CSE Department exists
        cse_dept = db.query(Department).filter(Department.code == "CSE").first()
        if not cse_dept:
            logger.info("Creating sample Computer Science Department...")
            cse_dept = Department(code="CSE", name="Computer Science and Engineering")
            db.add(cse_dept)
            db.commit()
            db.refresh(cse_dept)

        # Check if ECE Department exists
        ece_dept = db.query(Department).filter(Department.code == "ECE").first()
        if not ece_dept:
            logger.info("Creating sample Electronics Department...")
            ece_dept = Department(code="ECE", name="Electronics and Communication Engineering")
            db.add(ece_dept)
            db.commit()
            db.refresh(ece_dept)

        # Check if CS101 exists
        course_cs101 = db.query(Course).filter(Course.code == "CS101").first()
        if not course_cs101:
            logger.info("Creating sample course CS101...")
            course_cs101 = Course(
                department_id=cse_dept.id,
                code="CS101",
                title="Introduction to Computer Science",
                description="Fundamental programming concepts and algorithms.",
                credits=4
            )
            db.add(course_cs101)
            db.commit()
            db.refresh(course_cs101)

        # Check if CS20006 exists
        course_algos = db.query(Course).filter(Course.code == "CS20006").first()
        if not course_algos:
            logger.info("Creating sample course CS20006 Algorithms...")
            course_algos = Course(
                department_id=cse_dept.id,
                code="CS20006",
                title="Design and Analysis of Algorithms",
                description="Advanced algorithms, dynamic programming, greedy algorithms, and graph theory.",
                credits=4
            )
            db.add(course_algos)
            db.commit()
            db.refresh(course_algos)

        # Check if EC10001 exists
        course_ec101 = db.query(Course).filter(Course.code == "EC10001").first()
        if not course_ec101:
            logger.info("Creating sample course EC10001...")
            course_ec101 = Course(
                department_id=ece_dept.id,
                code="EC10001",
                title="Basic Electronics Engineering",
                description="Introduction to semiconductor devices, circuits, and electronic systems.",
                credits=3
            )
            db.add(course_ec101)
            db.commit()
            db.refresh(course_ec101)

        # Check if an offering exists for CS101
        offering_cs101 = db.query(CourseOffering).filter(
            CourseOffering.course_id == course_cs101.id,
            CourseOffering.year == 2026,
            CourseOffering.semester == SemesterType.AUTUMN
        ).first()
        
        if not offering_cs101:
            logger.info("Creating Autumn 2026 offering for CS101...")
            offering_cs101 = CourseOffering(
                course_id=course_cs101.id,
                year=2026,
                semester=SemesterType.AUTUMN
            )
            db.add(offering_cs101)
            db.commit()

        # Check if an offering exists for CS20006
        offering_algos = db.query(CourseOffering).filter(
            CourseOffering.course_id == course_algos.id,
            CourseOffering.year == 2026,
            CourseOffering.semester == SemesterType.AUTUMN
        ).first()
        
        if not offering_algos:
            logger.info("Creating Autumn 2026 offering for CS20006...")
            offering_algos = CourseOffering(
                course_id=course_algos.id,
                year=2026,
                semester=SemesterType.AUTUMN
            )
            db.add(offering_algos)
            db.commit()

        logger.info("Database seeding completed successfully!")

    except Exception as e:
        logger.error(f"Failed to seed data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # init_db() # DANGEROUS: Do not use this when Alembic is active!
    seed_data()
