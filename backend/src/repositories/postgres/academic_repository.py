from uuid import UUID
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from src.models.academic_model import OrganizationalUnit, Offering, StudyUnit, FacultyInfo
from src.schemas.academic_schema import (
    OrganizationalUnitCreate, OfferingCreate, StudyUnitCreate,
    FacultyInfoCreate
)

class AcademicRepository:
    def __init__(self, session: Session):
        self.session = session

    # --- Organizational Unit ---
    def get_org_unit(self, org_unit_id: UUID) -> OrganizationalUnit | None:
        return self.session.get(OrganizationalUnit, org_unit_id)

    def get_org_units(self) -> list[OrganizationalUnit]:
        return list(self.session.scalars(select(OrganizationalUnit)).all())

    def create_org_unit(self, org_unit_in: OrganizationalUnitCreate) -> OrganizationalUnit:
        org_unit = OrganizationalUnit(code=org_unit_in.code, name=org_unit_in.name)
        self.session.add(org_unit)
        self.session.commit()
        self.session.refresh(org_unit)
        return org_unit

    # --- Offering ---
    def get_offering(self, offering_id: UUID) -> Offering | None:
        return self.session.get(Offering, offering_id)

    def get_offerings(self, org_unit_id: UUID | None = None) -> list[Offering]:
        stmt = select(Offering)
        if org_unit_id:
            stmt = stmt.where(Offering.org_unit_id == org_unit_id)
        return list(self.session.scalars(stmt).all())

    def create_offering(self, offering_in: OfferingCreate) -> Offering:
        offering = Offering(
            org_unit_id=offering_in.org_unit_id,
            code=offering_in.code,
            name=offering_in.name
        )
        self.session.add(offering)
        self.session.commit()
        self.session.refresh(offering)
        return offering

    # --- Study Unit ---
    def get_study_unit(self, study_unit_id: UUID) -> StudyUnit | None:
        return self.session.get(StudyUnit, study_unit_id)

    def get_study_units(self, org_unit_id: UUID | None = None, offering_id: UUID | None = None) -> list[StudyUnit]:
        stmt = select(StudyUnit)
        if org_unit_id:
            stmt = stmt.where(StudyUnit.org_unit_id == org_unit_id)
        if offering_id:
            stmt = stmt.join(StudyUnit.offerings).where(Offering.id == offering_id)
        return list(self.session.scalars(stmt).all())

    def create_study_unit(self, study_unit_in: StudyUnitCreate) -> StudyUnit:
        study_unit = StudyUnit(
            org_unit_id=study_unit_in.org_unit_id,
            code=study_unit_in.code,
            name=study_unit_in.name,
            description=study_unit_in.description,
            credits=study_unit_in.credits
        )
        self.session.add(study_unit)
        self.session.commit()
        self.session.refresh(study_unit)
        return study_unit

    def link_offering(self, study_unit_id: UUID, offering_id: UUID) -> StudyUnit:
        study_unit = self.get_study_unit(study_unit_id)
        offering = self.get_offering(offering_id)
        if study_unit and offering and offering not in study_unit.offerings:
            study_unit.offerings.append(offering)
            self.session.commit()
            self.session.refresh(study_unit)
        return study_unit

    def unlink_offering(self, study_unit_id: UUID, offering_id: UUID) -> StudyUnit:
        study_unit = self.get_study_unit(study_unit_id)
        offering = self.get_offering(offering_id)
        if study_unit and offering and offering in study_unit.offerings:
            study_unit.offerings.remove(offering)
            self.session.commit()
            self.session.refresh(study_unit)
        return study_unit

    def add_prerequisite(self, study_unit_id: UUID, prerequisite_id: UUID) -> StudyUnit:
        from src.models.academic_model import StudyUnitPrerequisite
        study_unit = self.get_study_unit(study_unit_id)
        prerequisite = self.get_study_unit(prerequisite_id)
        if study_unit and prerequisite:
            link = StudyUnitPrerequisite(study_unit_id=study_unit_id, prerequisite_id=prerequisite_id)
            self.session.add(link)
            self.session.commit()
            self.session.refresh(study_unit)
        return study_unit

    def remove_prerequisite(self, study_unit_id: UUID, prerequisite_id: UUID) -> StudyUnit:
        from src.models.academic_model import StudyUnitPrerequisite
        link = self.session.scalar(select(StudyUnitPrerequisite).where(
            StudyUnitPrerequisite.study_unit_id == study_unit_id,
            StudyUnitPrerequisite.prerequisite_id == prerequisite_id
        ))
        if link:
            self.session.delete(link)
            self.session.commit()
        study_unit = self.get_study_unit(study_unit_id)
        return study_unit

    # --- FacultyInfo ---
    def create_faculty_info(self, faculty_in: FacultyInfoCreate) -> FacultyInfo:
        faculty = FacultyInfo(
            offering_id=faculty_in.offering_id,
            name=faculty_in.name,
            email=faculty_in.email,
            role=faculty_in.role,
            office_hours=faculty_in.office_hours
        )
        self.session.add(faculty)
        self.session.commit()
        self.session.refresh(faculty)
        return faculty
