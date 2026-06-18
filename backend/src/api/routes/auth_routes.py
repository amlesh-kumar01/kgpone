from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.infrastructure.database import get_db
from src.models.user_model import User
from src.schemas.user_schema import UserCreate, UserRead, TokenResponse
from src.repositories.postgres.user_repository import UserRepository
from src.services.auth.user_service import UserService
from src.api.middleware.auth_middleware import get_current_user

router = APIRouter(tags=["Authentication"])

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    repo = UserRepository(db)
    return UserService(repo)

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, service: UserService = Depends(get_user_service)):
    """Registers a new user and returns their profile details."""
    return service.register_user(user_in)

@router.post("/login", response_model=TokenResponse)
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(get_user_service)
):
    """
    Authenticates a user via form-urlencoded (username/password)
    and sets HttpOnly secure cookies for access and refresh tokens.
    """
    tokens = service.authenticate_user(form_data.username, form_data.password)
    
    # Set HttpOnly Cookie for access token
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,
        max_age=1800,  # 30 minutes
        samesite="lax",
        secure=False  # Set to True in production with HTTPS
    )
    
    # Set HttpOnly Cookie for refresh token
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        max_age=604800,  # 7 days
        samesite="lax",
        secure=False
    )
    
    return tokens

@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    """Returns the authenticated user's profile directly to ground client application state."""
    return current_user

@router.post("/logout")
def logout(response: Response):
    """Clears HTTPOnly authentication cookies."""
    response.set_cookie(
        key="access_token",
        value="",
        max_age=0,
        httponly=True,
        samesite="lax",
        secure=False
    )
    response.set_cookie(
        key="refresh_token",
        value="",
        max_age=0,
        httponly=True,
        samesite="lax",
        secure=False
    )
    return {"status": "success", "message": "Logged out successfully"}

@router.post("/refresh", response_model=TokenResponse)
def refresh(
    request: Request,
    response: Response,
    service: UserService = Depends(get_user_service)
):
    """Refreshes authorization tokens using the refresh token stored in cookies."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing from cookies"
        )
    
    tokens = service.refresh_access_token(refresh_token)
    
    # Update Cookies
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=True,
        max_age=1800,
        samesite="lax",
        secure=False
    )
    
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        max_age=604800,
        samesite="lax",
        secure=False
    )
    
    return tokens
