from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def customize_openapi(app: FastAPI) -> None:
    """
    Overrides the default FastAPI OpenAPI schema generator to customize 
    the validation error (422) schema to match the StandardResponse structure.
    """
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        
        # Override the HTTPValidationError schema to match StandardResponse
        if "HTTPValidationError" in openapi_schema["components"]["schemas"]:
            openapi_schema["components"]["schemas"]["HTTPValidationError"] = {
                "title": "ValidationErrorResponse",
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "example": "error"
                    },
                    "message": {
                        "type": "string",
                        "example": "Validation error"
                    },
                    "data": {
                        "type": "object",
                        "properties": {
                            "errors": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "description": "Details about each validation failure"
                                }
                            }
                        }
                    }
                }
            }
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi
