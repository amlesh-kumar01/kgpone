from src.infrastructure.database import engine, Base
from src.models import academic_model, document_model, user_model, system_model
from src.models.user_model import User, UserRole
from sqlalchemy.orm import Session
from sqlalchemy import text

def reset_db():
    print("Dropping schema public cascade...")
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE;"))
        conn.execute(text("CREATE SCHEMA public;"))
        
    print("Recreating all tables...")
    Base.metadata.create_all(engine)
    print("Tables recreated successfully.")
    
    # Create an admin user so we can login to the frontend
    print("Creating admin user...")
    with Session(engine) as session:
        admin = User(
            email="admin@kgpone.com",
            full_name="Admin User",
            hashed_password="hashed_password", # Replace with actual hash if needed, but the frontend might mock this
            role=UserRole.ADMIN
        )
        session.add(admin)
        session.commit()
    print("Admin user created.")

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    reset_db()
