from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from src.api.exceptions.handlers import (
    http_exception_handler, validation_exception_handler, 
    generic_exception_handler, value_error_handler, 
    integrity_error_handler
)
from sqlalchemy.exc import IntegrityError

# Load environment variables from .env file before importing local modules
load_dotenv()
from src.api.routes import user_routes, course_routes, document_routes
from src.api.middleware.security_middleware import SecurityHeadersMiddleware
from src.api.middleware.request_logger import RequestLoggerMiddleware
from src.config.settings import Settings

from src.infrastructure.database import Base, engine

app = FastAPI(title="KgpOne Backend API")

# Database tables are now managed by Alembic migrations
# Base.metadata.create_all(bind=engine)

# Setup CORS for the frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Apply custom Security Headers (CSP, HSTS, etc.)
app.add_middleware(SecurityHeadersMiddleware)

# Apply Centralized Request Logging
app.add_middleware(RequestLoggerMiddleware)

# Setup CSRF Protection Configuration
class CsrfSettings(BaseModel):
    secret_key: str = Settings().SECRET_KEY
    cookie_samesite: str = "lax"
    cookie_secure: bool = False # Set to True in production (HTTPS)
    cookie_httponly: bool = False # Important: Needs to be readable by frontend JS to send back as X-CSRF-Token

@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()

@app.exception_handler(CsrfProtectError)
def csrf_protect_exception_handler(request: Request, exc: CsrfProtectError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

# Apply Rate Limiter Handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply Global Exception Handlers for Standard Responses
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValueError, value_error_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)
# RBAC Routers
app.include_router(user_routes.router, prefix="/api")
app.include_router(course_routes.router, prefix="/api")
app.include_router(document_routes.router, prefix="/api")

@app.get("/api")
def read_root():
    return {"message": "Welcome to KgpOne Secure API"}
