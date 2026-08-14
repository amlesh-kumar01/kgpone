import logging
import asyncio
from celery import shared_task
from sqlalchemy.orm import Session
from src.infrastructure.database import SessionLocal
from src.services.analysis.base import AnalysisInput
from src.models.analysis_job_model import AnalysisJob, AnalysisJobStatus
from src.services.analysis.summarization.document_summarizer import DocumentSummarizer
from src.services.analysis.quiz.quiz_generator import QuizGenerator
from src.services.analysis.formula_revision.formula_revision import FormulaRevisionGenerator
from src.services.analysis.summarization.course_summarizer import StudyUnitSummarizer
from src.services.analysis.comparison.document_comparator import DocumentComparator

logger = logging.getLogger("analysis_tasks")

@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3)
def summarize_document_task(self, analysis_id: str, document_id: str, user_id: str):
    db = SessionLocal()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == analysis_id).first()
        if not job:
            return
            
        job.status = AnalysisJobStatus.RUNNING
        db.commit()
        
        summarizer = DocumentSummarizer()
        input_data = AnalysisInput(documents=[document_id])
        
        result = asyncio.run(summarizer.run(input_data, analysis_id))
        
        job.status = AnalysisJobStatus.COMPLETED
        job.result_s3_key = result.result_s3_key
        job.result_md_s3_key = result.result_md_s3_key
        db.commit()
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        job = db.query(AnalysisJob).filter(AnalysisJob.id == analysis_id).first()
        if job:
            job.status = AnalysisJobStatus.FAILED
            job.error_message = str(e)
            db.commit()
        raise
    finally:
        db.close()

@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3)
def generate_quiz_task(self, analysis_id: str, document_id: str, user_id: str):
    db = SessionLocal()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == analysis_id).first()
        if not job:
            return
            
        job.status = AnalysisJobStatus.RUNNING
        db.commit()
        
        quiz_gen = QuizGenerator()
        input_data = AnalysisInput(documents=[document_id])
        
        result = asyncio.run(quiz_gen.run(input_data, analysis_id))
        
        job.status = AnalysisJobStatus.COMPLETED
        job.result_s3_key = result.result_s3_key
        job.result_md_s3_key = result.result_md_s3_key
        db.commit()
        
    except Exception as e:
        logger.error(f"Quiz generation failed: {str(e)}")
        job = db.query(AnalysisJob).filter(AnalysisJob.id == analysis_id).first()
        if job:
            job.status = AnalysisJobStatus.FAILED
            job.error_message = str(e)
            db.commit()
        raise
    finally:
        db.close()

@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3)
def generate_formula_revision_task(self, analysis_id: str, document_id: str, user_id: str):
    db = SessionLocal()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == analysis_id).first()
        if not job:
            return
            
        job.status = AnalysisJobStatus.RUNNING
        db.commit()
        
        formula_gen = FormulaRevisionGenerator()
        input_data = AnalysisInput(documents=[document_id])
        
        result = asyncio.run(formula_gen.run(input_data, analysis_id))
        
        job.status = AnalysisJobStatus.COMPLETED
        job.result_s3_key = result.result_s3_key
        job.result_md_s3_key = result.result_md_s3_key
        db.commit()
        
    except Exception as e:
        logger.error(f"Formula revision generation failed: {str(e)}")
        job = db.query(AnalysisJob).filter(AnalysisJob.id == analysis_id).first()
        if job:
            job.status = AnalysisJobStatus.FAILED
            job.error_message = str(e)
            db.commit()
        raise
    finally:
        db.close()

@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3)
def course_summary_task(self, analysis_id: str, document_ids: list, user_id: str):
    db = SessionLocal()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == analysis_id).first()
        if not job:
            return
            
        job.status = AnalysisJobStatus.RUNNING
        db.commit()
        
        course_gen = StudyUnitSummarizer()
        input_data = AnalysisInput(documents=document_ids)
        
        result = asyncio.run(course_gen.run(input_data, analysis_id))
        
        job.status = AnalysisJobStatus.COMPLETED
        job.result_s3_key = result.result_s3_key
        job.result_md_s3_key = result.result_md_s3_key
        db.commit()
        
    except Exception as e:
        logger.error(f"StudyUnit summary generation failed: {str(e)}")
        job = db.query(AnalysisJob).filter(AnalysisJob.id == analysis_id).first()
        if job:
            job.status = AnalysisJobStatus.FAILED
            job.error_message = str(e)
            db.commit()
        raise
    finally:
        db.close()

@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3)
def document_comparison_task(self, analysis_id: str, document_ids: list, user_id: str):
    db = SessionLocal()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == analysis_id).first()
        if not job:
            return
            
        job.status = AnalysisJobStatus.RUNNING
        db.commit()
        
        doc_comp = DocumentComparator()
        input_data = AnalysisInput(documents=document_ids)
        
        result = asyncio.run(doc_comp.run(input_data, analysis_id))
        
        job.status = AnalysisJobStatus.COMPLETED
        job.result_s3_key = result.result_s3_key
        job.result_md_s3_key = result.result_md_s3_key
        db.commit()
        
    except Exception as e:
        logger.error(f"Document comparison generation failed: {str(e)}")
        job = db.query(AnalysisJob).filter(AnalysisJob.id == analysis_id).first()
        if job:
            job.status = AnalysisJobStatus.FAILED
            job.error_message = str(e)
            db.commit()
        raise
    finally:
        db.close()
