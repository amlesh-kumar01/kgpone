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
        admin = db.query(User).filter(User.email == "admin@kgpone.edu").first()
        if not admin:
            logger.info("Creating default Admin user (admin@kgpone.edu / admin123)...")
            admin = User(
                email="admin@kgpone.edu",
                hashed_password=get_password_hash("admin123"),
                full_name="System Administrator",
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin)
            db.commit()
        else:
            logger.info("Force-updating default Admin user password...")
            admin.hashed_password = get_password_hash("admin123")
            admin.full_name = "System Administrator"
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
        dept = db.query(Department).filter(Department.code == "CSE").first()
        if not dept:
            logger.info("Creating sample Computer Science Department...")
            dept = Department(code="CSE", name="Computer Science and Engineering")
            db.add(dept)
            db.commit()
            db.refresh(dept)

        # Check if CS101 exists
        course = db.query(Course).filter(Course.code == "CS101").first()
        if not course:
            logger.info("Creating sample course CS101...")
            course = Course(
                department_id=dept.id,
                code="CS101",
                title="Introduction to Computer Science",
                description="Fundamental programming concepts and algorithms.",
                credits=4
            )
            db.add(course)
            db.commit()
            db.refresh(course)

        # Check if an offering exists
        offering = db.query(CourseOffering).filter(
            CourseOffering.course_id == course.id,
            CourseOffering.year == 2026,
            CourseOffering.semester == SemesterType.AUTUMN
        ).first()
        
        if not offering:
            logger.info("Creating Autumn 2026 offering for CS101...")
            offering = CourseOffering(
                course_id=course.id,
                year=2026,
                semester=SemesterType.AUTUMN
            )
            db.add(offering)
            db.commit()

        logger.info("Database seeding completed successfully!")

    except Exception as e:
        logger.error(f"Failed to seed data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    seed_data()
