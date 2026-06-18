from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.infrastructure.database import get_db
from src.schemas.user_schema import UserCreate, UserRead, TokenResponse
from src.repositories.postgres.user_repository import UserRepository
from src.services.auth.user_service import UserService
from pydantic import BaseModel

from src.schemas.response_schema import StandardResponse
from src.models.user_model import User, UserRole
from src.api.middleware.auth_middleware import require_role

from fastapi import APIRouter, Depends, HTTPException, status, Response

router = APIRouter(prefix="/users", tags=["Users"])

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    repo = UserRepository(db)
    return UserService(repo)

class LoginRequest(BaseModel):
    email: str
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

@router.post("/register", response_model=StandardResponse[UserRead], status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserCreate, service: UserService = Depends(get_user_service)):
    # Enforce that public registration can only create students
    user_in.role = UserRole.STUDENT
    user = service.register_user(user_in)
    return StandardResponse(status="success", message="User registered successfully", data=user)

@router.post("/publishers", response_model=StandardResponse[UserRead], status_code=status.HTTP_201_CREATED)
def create_publisher(user_in: UserCreate, service: UserService = Depends(get_user_service), admin: User = Depends(require_role([UserRole.ADMIN]))):
    # Enforce PUBLISHER role
    user_in.role = UserRole.PUBLISHER
    user = service.register_user(user_in)
    return StandardResponse(status="success", message="Publisher registered successfully", data=user)

@router.post("/login", response_model=StandardResponse[TokenResponse])
def login_user(login_data: LoginRequest, response: Response, service: UserService = Depends(get_user_service)):
    tokens = service.authenticate_user(login_data.email, login_data.password)
    
    # Set HTTPOnly Cookie
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,
        max_age=1800,  # 30 minutes
        samesite="lax",
        secure=False  # In production, set to True with HTTPS
    )
    
    return StandardResponse(status="success", message="Login successful", data=tokens)

@router.post("/refresh", response_model=StandardResponse[TokenResponse])
def refresh_token(request: RefreshRequest, service: UserService = Depends(get_user_service)):
    tokens = service.refresh_access_token(request.refresh_token)
    return StandardResponse(status="success", message="Token refreshed successfully", data=tokens)
