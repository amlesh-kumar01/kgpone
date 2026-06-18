import logging
from uuid import UUID
from celery import shared_task
from src.infrastructure.database import SessionLocal
from src.models.document_model import Document
from src.models.academic_model import Course
from src.models.system_model import CleanupJob, DeletionStatus
from src.repositories.s3.storage_repository import S3Storage
from src.repositories.qdrant.vector_repository import QdrantRepository

logger = logging.getLogger("cleanup_tasks")

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=600, max_retries=5)
def cleanup_document_task(self, document_id: str, job_id: str):
    logger.info(f"Starting cleanup for Document {document_id}")
    db = SessionLocal()
    s3_storage = S3Storage()
    qdrant_repo = QdrantRepository()
    
    try:
        job = db.get(CleanupJob, UUID(job_id))
        if not job:
            logger.warning(f"CleanupJob {job_id} not found.")
            return

        job.attempt_count += 1
        job.status = DeletionStatus.PENDING
        db.commit()

        # 1. Fetch document
        doc = db.get(Document, UUID(document_id))
        if not doc:
            logger.warning(f"Document {document_id} not found in DB.")
            job.status = DeletionStatus.COMPLETED
            db.commit()
            return
            
        # 2. S3 Cleanup
        s3_storage.delete_file(doc.s3_url)
        
        # 3. Qdrant Cleanup
        qdrant_repo.delete_by_filter("documents", {"document_id": document_id})
        
        # 4. Graph Cleanup (Placeholder)
        # graph_repo.delete_document_nodes(document_id)
        
        # 5. Mark Document and Job Completed
        job.status = DeletionStatus.COMPLETED
        doc.deletion_status = DeletionStatus.COMPLETED
        # Hard Delete or Soft Delete completion? User said: "Mark deletion_status = COMPLETED OR Delete database record"
        # We will Hard Delete to keep DB clean if cleanup succeeds.
        db.delete(doc)
        db.commit()
        logger.info(f"Cleanup completed for Document {document_id}")

    except Exception as e:
        logger.error(f"Failed to cleanup document {document_id}: {e}")
        db.rollback()
        if job:
            job.error_message = str(e)
            job.status = DeletionStatus.FAILED
            db.commit()
        raise e
    finally:
        db.close()


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=600, max_retries=5)
def cleanup_course_task(self, course_id: str, job_id: str):
    logger.info(f"Starting cleanup for Course {course_id}")
    db = SessionLocal()
    s3_storage = S3Storage()
    qdrant_repo = QdrantRepository()
    
    try:
        job = db.get(CleanupJob, UUID(job_id))
        if not job:
            return

        job.attempt_count += 1
        job.status = DeletionStatus.PENDING
        db.commit()

        # 1. Fetch course to verify it exists
        course = db.get(Course, UUID(course_id))
        if not course:
            job.status = DeletionStatus.COMPLETED
            db.commit()
            return
            
        # 2. Fetch all documents related to this course
        # A bit tricky: Document -> CourseOffering -> Course
        from src.models.academic_model import CourseOffering
        docs = db.query(Document).join(CourseOffering, Document.course_offering_id == CourseOffering.id).join(Course, CourseOffering.course_id == Course.id).filter(Course.id == UUID(course_id)).all()
        
        # 3. S3 Cleanup for all docs
        for doc in docs:
            s3_storage.delete_file(doc.s3_url)
        
        # 4. Qdrant Cleanup (We indexed course_id? Wait, we indexed course_code and course_offering_id)
        # Wait, the Qdrant payload contains course_code, but not course_id?
        # Let's delete by document_id for each document to be safe, or by course_code.
        for doc in docs:
            qdrant_repo.delete_by_filter("documents", {"document_id": str(doc.id)})
            
        # 5. Graph Cleanup (Placeholder)
        # graph_repo.delete_course_nodes(course_id)
        
        # 6. Hard Delete the course (cascades to offerings and documents)
        job.status = DeletionStatus.COMPLETED
        db.delete(course)
        db.commit()
        logger.info(f"Cleanup completed for Course {course_id}")

    except Exception as e:
        logger.error(f"Failed to cleanup course {course_id}: {e}")
        db.rollback()
        if job:
            job.error_message = str(e)
            job.status = DeletionStatus.FAILED
            db.commit()
        raise e
    finally:
        db.close()

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=600, max_retries=5)
def delete_old_vectors_task(self, document_id: str, old_version: int):
    logger.info(f"Deleting old vectors for Document {document_id} version {old_version}")
    qdrant_repo = QdrantRepository()
    try:
        qdrant_repo.delete_by_filter("documents", {"document_id": document_id, "document_version": old_version})
    except Exception as e:
        logger.error(f"Failed to delete old vectors for document {document_id}: {e}")
        raise e
