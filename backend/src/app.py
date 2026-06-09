from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel


# Load environment variables from .env file before importing local modules
load_dotenv()

from src.routes import workspace_routes as workspace, auth_routes as auth, marketplace_routes as marketplace, task_routes as tasks, upload_routes as upload
from src.middleware.logging_middleware import SecurityHeadersMiddleware
from src.services.auth.jwt_service import SECRET_KEY

from src.config.database import Base, engine

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

# Setup CSRF Protection Configuration
class CsrfSettings(BaseModel):
    secret_key: str = SECRET_KEY
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

# Include Routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(marketplace.router, prefix="/api/marketplace", tags=["marketplace"])
app.include_router(workspace.router, prefix="/api/workspace", tags=["workspace"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(upload.router, prefix="/api/content", tags=["content"])

@app.get("/api")
def read_root():
    return {"message": "Welcome to KgpOne Secure API"}
