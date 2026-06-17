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
    response = StandardResponse(
        status="error",
        message="An unexpected error occurred",
        data=None
    )
    # Log the full exception `exc` here in a real app
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=response.model_dump())
