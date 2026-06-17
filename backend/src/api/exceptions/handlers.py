from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from src.schemas.response_schema import StandardResponse

async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    response = StandardResponse(
        status="error",
        message=str(exc.detail),
        data=None
    )
    return JSONResponse(status_code=exc.status_code, content=response.model_dump())

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    response = StandardResponse(
        status="error",
        message="Validation error",
        data={"errors": exc.errors()}
    )
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=response.model_dump())

async def generic_exception_handler(request: Request, exc: Exception):
    import logging
    logger = logging.getLogger(__name__)
    logger.exception(f"Unhandled Exception: {str(exc)}")
    response = StandardResponse(
        status="error",
        message=str(exc) or "An unexpected error occurred",
        data=None
    )
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=response.model_dump())

async def value_error_handler(request: Request, exc: ValueError):
    response = StandardResponse(
        status="error",
        message=str(exc),
        data=None
    )
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=response.model_dump())

from sqlalchemy.exc import IntegrityError
async def integrity_error_handler(request: Request, exc: IntegrityError):
    response = StandardResponse(
        status="error",
        message="Database integrity error. The record might already exist or a constraint was violated.",
        data={"detail": str(exc.orig) if hasattr(exc, "orig") else str(exc)}
    )
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=response.model_dump())
