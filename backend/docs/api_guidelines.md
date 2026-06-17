# API Guidelines

## 1. Global Versioning
All API endpoints MUST be prefixed with `/api/v1`. This is controlled centrally in `src/main.py`.

## 2. Standardized Response Format
Every successful endpoint must return the `StandardResponse` model from `src/schemas/response_schema.py`.

**Example Success Response:**
```json
{
  "status": "success",
  "message": "Resource fetched successfully",
  "data": {
    "id": "123",
    "name": "example"
  }
}
```

## 3. Error Handling
Do not return bare HTTP exceptions. The application uses global exception handlers in `src/main.py` which catch `IntegrityError`, `HTTPException`, and generic exceptions, automatically converting them into standard error payloads.
You can confidently raise standard `HTTPException` inside your services and the middleware will format it like this:

**Example Error Response:**
```json
{
  "status": "error",
  "message": "User not found",
  "error_details": {
    "type": "Not Found",
    "code": 404
  }
}
```

## 4. Role-Based Access Control
End-points are secured using dependency injection. To restrict an endpoint to certain roles, use the `require_role` dependency:
```python
from src.api.middleware.auth_middleware import require_role
from src.models.user_model import UserRole

@router.delete("/{course_id}")
def delete_course(
    course_id: UUID, 
    user: User = Depends(require_role([UserRole.ADMIN]))
):
    ...
```

## 5. Swagger UI
Because of the structured routing and response models, the auto-generated documentation is highly robust. Always access `http://localhost:8000/docs` to test new endpoints visually.
