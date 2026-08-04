from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.models.user_model import User, RefreshToken, EmailOtp
from src.schemas.user_schema import UserCreate, UserUpdate

class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, user_id: UUID) -> User | None:
        return self.session.get(User, user_id)

    def get_all_users(self) -> list[User]:
        stmt = select(User).order_by(User.created_at.desc())
        return list(self.session.scalars(stmt).all())

    def count_users(self) -> int:
        from sqlalchemy import func
        stmt = select(func.count(User.id))
        return self.session.scalar(stmt) or 0

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self.session.scalars(stmt).first()

    def create(self, user_in: UserCreate, hashed_password: str) -> User:
        user = User(
            email=user_in.email,
            full_name=user_in.full_name,
            role=user_in.role,
            is_active=user_in.is_active,
            is_verified=user_in.is_verified,
            hashed_password=hashed_password
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def update(self, user: User, user_update: UserUpdate) -> User:
        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def create_refresh_token(self, user_id: UUID, token: str, expires_at) -> RefreshToken:
        rt = RefreshToken(user_id=user_id, token=token, expires_at=expires_at)
        self.session.add(rt)
        self.session.commit()
        return rt

    def get_refresh_token(self, token: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token == token)
        return self.session.scalars(stmt).first()

    def revoke_refresh_token(self, token: str) -> None:
        rt = self.get_refresh_token(token)
        if rt:
            rt.is_revoked = True
            self.session.add(rt)
            self.session.commit()
