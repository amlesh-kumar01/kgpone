from src.infrastructure.database import engine, Base
from src.models.academic_model import OrganizationalUnit, Offering, StudyUnit
from src.models import document_model, user_model
from sqlalchemy.orm import Session

def seed_db():
    print("Seeding database with new architecture...")
    with Session(engine) as session:
        # Create an Organizational Unit (e.g. University Department)
        cs_dept = OrganizationalUnit(
            code="CS",
            name="Computer Science Department"
        )
        session.add(cs_dept)
        session.commit()
        session.refresh(cs_dept)
        print(f"Created Org Unit: {cs_dept.name}")

        # Create an Offering (e.g. Fall 2026 Semester)
        fall_offering = Offering(
            org_unit_id=cs_dept.id,
            code="FA26",
            name="Fall 2026"
        )
        session.add(fall_offering)
        session.commit()
        session.refresh(fall_offering)
        print(f"Created Offering: {fall_offering.name}")

        # Create a Study Unit (e.g. CS101 Course)
        cs101 = StudyUnit(
            org_unit_id=cs_dept.id,
            code="CS101",
            name="Introduction to Computer Science",
            description="Fundamentals of programming.",
            credits=4
        )
        cs101.offerings.append(fall_offering)
        session.add(cs101)
        session.commit()
        print(f"Created Study Unit: {cs101.name} mapped to {fall_offering.name}")

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    seed_db()
