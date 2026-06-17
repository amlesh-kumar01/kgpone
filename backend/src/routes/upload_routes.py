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
        
        import os
        presigned_data = s3_storage.generate_presigned_url(
            file_key=unique_file_key,
            content_type=req.content_type
        )
        upload_url = presigned_data["upload_url"]
        
        # Rewrite internal S3 endpoint to host-accessible endpoint for the client browser
        external_s3_url = os.getenv("EXTERNAL_S3_ENDPOINT_URL")
        if external_s3_url:
            internal_endpoint = os.getenv("AWS_ENDPOINT_URL") or os.getenv("S3_ENDPOINT_URL")
            if internal_endpoint and internal_endpoint in upload_url:
                upload_url = upload_url.replace(internal_endpoint, external_s3_url)

        return {
            "upload_url": upload_url,
            "file_key": unique_file_key
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from sqlalchemy.orm import Session
from src.models.user_model import Content, ContentStatus
from src.config.database import get_db
import os

@router.post("/confirm-upload")
def confirm_upload(
    req: ConfirmUploadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Called by the frontend after a successful S3 upload. 
    Here we save the content metadata to the database.
    """
    try:
        # Construct the static public S3 URL
        bucket_name = os.environ.get("S3_BUCKET_NAME")
        region = os.environ.get("AWS_DEFAULT_REGION", "eu-north-1")
        file_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{req.file_key}"

        new_content = Content(
            title=req.title,
            description=req.description,
            course_code=req.course_code,
            academic_year=req.academic_year,
            content_type=req.content_type,
            file_url=file_url,
            status=ContentStatus.PUBLISHED,
            uploader_id=current_user.id
        )

        db.add(new_content)
        db.commit()
        db.refresh(new_content)

        return {"message": "Upload confirmed and metadata saved", "content_id": str(new_content.id), "file_url": file_url}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
