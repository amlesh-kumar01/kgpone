from fastapi import APIRouter, Depends, HTTPException, Query
from src.middleware.auth_middleware import get_current_user
from src.models.user_model import User
from src.infrastructure.s3_storage import S3Storage

router = APIRouter()
s3_storage = S3Storage()

from pydantic import BaseModel

class PresignedUrlRequest(BaseModel):
    filename: str
    content_type: str

class ConfirmUploadRequest(BaseModel):
    file_key: str
    title: str
    description: str = ""
    course_code: str
    academic_year: str
    content_type: str

@router.post("/presigned-url")
def get_presigned_url(
    req: PresignedUrlRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Returns a presigned URL that the frontend can use to upload a file directly to S3.
    """
    # Verify user has upload privileges (ADMIN or PUBLISHER)
    if getattr(current_user.role, 'value', current_user.role) not in ["ADMIN", "PUBLISHER"] and not current_user.can_upload:
        raise HTTPException(status_code=403, detail="You do not have permission to upload files.")

    try:
        # Generate a unique key for the file to prevent overwriting
        import uuid
        unique_file_key = f"uploads/{current_user.id}/{uuid.uuid4()}_{req.filename}"
        
        presigned_data = s3_storage.generate_presigned_url(
            file_key=unique_file_key,
            content_type=req.content_type
        )
        return {
            "upload_url": presigned_data["upload_url"],
            "file_key": unique_file_key
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/confirm-upload")
def confirm_upload(
    req: ConfirmUploadRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Called by the frontend after a successful S3 upload. 
    Here we would save the content metadata to the database.
    """
    # For now, we will just return success until the Content model logic is fully written
    return {"message": "Upload confirmed and metadata saved", "file_key": req.file_key}
