import logging
from uuid import UUID
from celery import shared_task
from src.infrastructure.database import SessionLocal
from src.models.document_model import Document
from src.models.academic_model import StudyUnit
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
    job = None
    
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
        try:
            if doc.s3_prefix:
                # Phase 1: delete everything under the prefix
                deleted = s3_storage.list_and_delete_prefix(doc.s3_prefix + "/")
                logger.info(f"Cleaned up {deleted} objects under {doc.s3_prefix}")
            else:
                # Legacy fallback
                s3_storage.delete_file(doc.s3_key)
                images_prefix = f"images/{document_id}/"
                deleted_imgs = s3_storage.list_and_delete_prefix(images_prefix)
                logger.info(f"Cleaned up legacy objects and {deleted_imgs} image(s) for document {document_id}")
        except Exception as s3_e:
            logger.warning(f"Failed to delete S3 objects (continuing): {s3_e}")
        
        # 3. Qdrant Cleanup
        qdrant_repo.delete_by_filter("documents", {"document_id": document_id})
        
        # 4. Graph Cleanup
        from src.repositories.neo4j.graph_repository import Neo4jRepo
        graph_repo = Neo4jRepo()
        graph_repo.delete_document_entities(document_id)        
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
def cleanup_study_unit_task(self, study_unit_id: str, job_id: str):
    logger.info(f"Starting cleanup for StudyUnit {study_unit_id}")
    db = SessionLocal()
    s3_storage = S3Storage()
    qdrant_repo = QdrantRepository()
    job = None
    
    try:
        job = db.get(CleanupJob, UUID(job_id))
        if not job:
            return

        job.attempt_count += 1
        job.status = DeletionStatus.PENDING
        db.commit()

        # 1. Fetch study unit to verify it exists
        study_unit = db.get(StudyUnit, UUID(study_unit_id))
        if not study_unit:
            job.status = DeletionStatus.COMPLETED
            db.commit()
            return
            
        # 2. Fetch all documents related to this study unit
        docs = db.query(Document).filter(Document.study_unit_id == UUID(study_unit_id)).all()
        
        # 3. S3 Cleanup for all docs
        for doc in docs:
            try:
                if doc.s3_prefix:
                    s3_storage.list_and_delete_prefix(doc.s3_prefix + "/")
                else:
                    s3_storage.delete_file(doc.s3_key)
            except Exception as s3_e:
                logger.warning(f"Failed to delete file from S3 (continuing DB cleanup): {s3_e}")
        
        # 4. Qdrant Cleanup
        for doc in docs:
            qdrant_repo.delete_by_filter("documents", {"document_id": str(doc.id)})
            
        # 5. Graph Cleanup
        from src.repositories.neo4j.graph_repository import Neo4jRepo
        graph_repo = Neo4jRepo()
        graph_repo.delete_course_subgraph(study_unit.code)
        
        # 6. Hard Delete the study unit (cascades to documents)
        job.status = DeletionStatus.COMPLETED
        db.delete(study_unit)
        db.commit()
        logger.info(f"Cleanup completed for StudyUnit {study_unit_id}")

    except Exception as e:
        logger.error(f"Failed to cleanup study unit {study_unit_id}: {e}")
        db.rollback()
        if job:
            job.error_message = str(e)
            job.status = DeletionStatus.FAILED
            db.commit()
        raise e
    finally:
        db.close()

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=600, max_retries=5)
def cleanup_org_unit_task(self, org_unit_id: str, job_id: str):
    from src.models.academic_model import OrganizationalUnit
    logger.info(f"Starting cleanup for OrgUnit {org_unit_id}")
    db = SessionLocal()
    s3_storage = S3Storage()
    qdrant_repo = QdrantRepository()
    job = None
    
    try:
        job = db.get(CleanupJob, UUID(job_id))
        if not job:
            return

        job.attempt_count += 1
        job.status = DeletionStatus.PENDING
        db.commit()

        # 1. Fetch org unit
        org_unit = db.get(OrganizationalUnit, UUID(org_unit_id))
        if not org_unit:
            job.status = DeletionStatus.COMPLETED
            db.commit()
            return
            
        # 2. Find ALL Study Units inside this Org Unit
        study_units = db.query(StudyUnit).filter(StudyUnit.org_unit_id == UUID(org_unit_id)).all()
        
        for study_unit in study_units:
            # Delete their documents
            docs = db.query(Document).filter(Document.study_unit_id == study_unit.id).all()
            for doc in docs:
                try:
                    if doc.s3_prefix:
                        s3_storage.list_and_delete_prefix(doc.s3_prefix + "/")
                    else:
                        s3_storage.delete_file(doc.s3_key)
                except Exception as s3_e:
                    logger.warning(f"Failed to delete file from S3: {s3_e}")
                qdrant_repo.delete_by_filter("documents", {"document_id": str(doc.id)})
            
            # Delete graph
            from src.repositories.neo4j.graph_repository import Neo4jRepo
            graph_repo = Neo4jRepo()
            graph_repo.delete_course_subgraph(study_unit.code)
            
        # 3. Hard Delete Org Unit (cascades to offerings, study units, and docs)
        job.status = DeletionStatus.COMPLETED
        db.delete(org_unit)
        db.commit()
        logger.info(f"Cleanup completed for OrgUnit {org_unit_id}")

    except Exception as e:
        logger.error(f"Failed to cleanup org unit {org_unit_id}: {e}")
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
