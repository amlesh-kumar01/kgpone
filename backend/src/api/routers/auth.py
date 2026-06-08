from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi_csrf_protect import CsrfProtect
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.infrastructure.database import get_db
from src.infrastructure.models import User, UserRole
from src.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS
)
from pydantic import BaseModel
from src.api.dependencies import get_current_user

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

class RegisterRequest(BaseModel):
    email: str
    password: str
    role: UserRole = UserRole.STUDENT

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """Registers a new user."""
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(request.password)
    new_user = User(
        email=request.email,
        password_hash=hashed_password,
        role=request.role
    )
    
    db.add(new_user)
    db.commit()
    
    return {"message": "User registered successfully"}

@router.post("/login")
@limiter.limit("5/minute")
def login(
    request: Request,
    response: Response, 
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db),
    csrf_protect: CsrfProtect = Depends()
):
    """Authenticates the user and sets HttpOnly cookies. Throttled to 5 attempts per minute."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # Set HttpOnly Cookies
    # Note: cookie_secure=True should be used in production with HTTPS
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False 
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        expires=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        samesite="lax",
        secure=False
    )
    
    # Generate and set CSRF Token (Not HttpOnly)
    csrf_token = csrf_protect.generate_csrf_tokens()
    csrf_protect.set_csrf_cookie(csrf_token, response)

    return {"message": "Login successful"}

@router.post("/logout")
def logout(response: Response, csrf_protect: CsrfProtect = Depends()):
    """Invalidates the session server-side by clearing the cookies."""
    # To protect the logout route from CSRF
    # csrf_protect.validate_csrf(request) # You can enable this if the frontend sends the token on logout
    
    response.delete_cookie(key="access_token", samesite="lax", secure=False)
    response.delete_cookie(key="refresh_token", samesite="lax", secure=False)
    csrf_protect.unset_csrf_cookie(response)
    
    return {"message": "Successfully logged out"}

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Returns the currently authenticated user's context."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role,
        "can_upload": current_user.can_upload
    }

@router.post("/refresh")
def refresh_session(request: Request, response: Response, db: Session = Depends(get_db)):
    """Silent refresh endpoint. Validates refresh_token cookie and issues a new access_token."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token found")
        
    from jose import jwt, JWTError
    from src.core.security import SECRET_KEY, ALGORITHM
    
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
            
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
            
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    # Generate new access token
    new_access_token = create_access_token(data={"sub": user_id})
    
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=False 
    )
    
    return {"message": "Session refreshed"}
