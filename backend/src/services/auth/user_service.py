from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID
from jose import jwt, JWTError
from passlib.context import CryptContext
from src.config.settings import Settings
from src.models.user_model import User
from src.repositories.postgres.user_repository import UserRepository
from src.schemas.user_schema import UserCreate, TokenResponse
from fastapi import HTTPException, status

settings = Settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    def create_access_token(self, subject: str | Any, expires_delta: timedelta | None = None) -> str:
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode = {"exp": expire, "sub": str(subject)}
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    def register_user(self, user_in: UserCreate) -> User:
        user = self.repository.get_by_email(user_in.email)
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        hashed_password = self.get_password_hash(user_in.password)
        return self.repository.create(user_in, hashed_password)

    def authenticate_user(self, email: str, password: str) -> TokenResponse:
        user = self.repository.get_by_email(email)
        if not user or not user.hashed_password:
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        
        if not self.verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(
            subject=str(user.id), expires_delta=access_token_expires
        )
        
        # We can implement proper refresh token generation and storage here
        # For now, returning a dummy refresh token to satisfy schema
        refresh_token = "dummy_refresh_token" 

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
