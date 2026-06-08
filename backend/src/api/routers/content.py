from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.infrastructure.database import get_db
from src.infrastructure.models import User, Content, ContentStatus
from src.api.routers.auth import get_current_user
from src.infrastructure.s3_storage import S3Storage
import uuid

router = APIRouter()
s3_storage = S3Storage()

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

def require_publisher(user: User = Depends(get_current_user)):
    if user.role.value not in ["PUBLISHER", "ADMIN"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to publish content")
    return user

@router.post("/presigned-url")
def get_presigned_url(request: PresignedUrlRequest, user: User = Depends(require_publisher)):
    # Generate unique file key to prevent collisions
    unique_id = uuid.uuid4()
    file_key = f"materials/{unique_id}_{request.filename}"
    
    # Generate presigned URL via AWS S3
    return s3_storage.generate_presigned_url(file_key, request.content_type)

@router.post("/confirm-upload")
def confirm_upload(request: ConfirmUploadRequest, user: User = Depends(require_publisher), db: Session = Depends(get_db)):
    # We create the DB record only after the frontend confirms S3 received the bytes
    new_content = Content(
        title=request.title,
        description=request.description,
        file_url=f"s3://{s3_storage.bucket_name}/{request.file_key}",
        content_type=request.content_type,
        course_code=request.course_code,
        academic_year=request.academic_year,
        status=ContentStatus.PENDING_APPROVAL,
        uploader_id=user.id
    )
    
    db.add(new_content)
    db.commit()
    db.refresh(new_content)
    
    return {"message": "Upload confirmed", "content_id": new_content.id}

@router.get("/my-content")
def get_my_content(user: User = Depends(require_publisher), db: Session = Depends(get_db)):
    contents = db.query(Content).filter(Content.uploader_id == user.id).all()
    return contents
