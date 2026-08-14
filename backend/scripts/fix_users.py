from src.infrastructure.database import SessionLocal, engine
from src.models.user_model import User, UserRole
from src.models import document_model, academic_model
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()

def get_password_hash(password: str) -> str:
    return password_hash.hash(password)

def fix_users():
    db = SessionLocal()
    try:
        # Delete invalid users created by my earlier script
        db.query(User).delete()
        db.commit()

        # Create properly hashed Admin user
        admin = User(
            email="admin@kgpone.edu",
            hashed_password=get_password_hash("admin123"),
            full_name="System Administrator",
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin)

        # Create properly hashed Student user
        student = User(
            email="student@kgpone.edu",
            hashed_password=get_password_hash("student123"),
            full_name="Test Student",
            role=UserRole.STUDENT,
            is_active=True
        )
        db.add(student)
        db.commit()
        print("Users successfully seeded with proper hashes!")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    fix_users()
