import logging
import asyncio
from celery import shared_task
from sqlalchemy.orm import Session
from src.infrastructure.database import SessionLocal
from src.models.document_model import Document
from src.models.analysis_generation_model import AnalysisGeneration, AnalysisStatus, AnalysisType
from src.services.ingestion.artifact_manager import ArtifactManager
from src.repositories.s3.storage_repository import S3Storage

logger = logging.getLogger("analysis_generation_tasks")

@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3)
def generate_analysis_task(self, document_id: str, generation_id: str):
    db = SessionLocal()
    try:
        gen = db.query(AnalysisGeneration).filter(AnalysisGeneration.id == generation_id).first()
        if not gen:
            return
            
        gen.status = AnalysisStatus.RUNNING
        db.commit()
        
        doc = db.query(Document).filter(Document.id == document_id).first()
        s3_prefix = doc.s3_prefix or f"documents/{doc.study_unit_id}/{document_id}"
        am = ArtifactManager(str(document_id), s3_prefix, S3Storage())
        
        # Download AST
        ast_data = am.download_json(am.canonical_key())
        if not ast_data:
            raise ValueError("Canonical AST not found. Cannot generate analysis.")
            
        if isinstance(ast_data, str):
            import json
            ast_data = json.loads(ast_data)
            
        # Select generator based on type
        md_content = ""
        if gen.type == AnalysisType.FORMULA_SHEET:
            from src.services.analysis.markdown_generators.formula_generator import FormulaGenerator
            generator = FormulaGenerator()
            md_content = asyncio.run(generator.generate(ast_data, gen.topics, gen.prompt, doc.title))
        elif gen.type == AnalysisType.QUESTION_BANK:
            from src.services.analysis.markdown_generators.question_bank_generator import QuestionBankGenerator
            generator = QuestionBankGenerator()
            md_content = asyncio.run(generator.generate(ast_data, gen.topics, gen.prompt, doc.title))
        elif gen.type == AnalysisType.CONCEPT_SUMMARY:
            from src.services.analysis.markdown_generators.concept_summary_generator import ConceptSummaryGenerator
            generator = ConceptSummaryGenerator()
            md_content = asyncio.run(generator.generate(ast_data, gen.topics, gen.prompt, doc.title))
        elif gen.type == AnalysisType.REVISION_NOTES:
            from src.services.analysis.markdown_generators.revision_notes_generator import RevisionNotesGenerator
            generator = RevisionNotesGenerator()
            md_content = asyncio.run(generator.generate(ast_data, gen.topics, gen.prompt, doc.title))
        else:
            raise ValueError(f"Unknown generation type: {gen.type}")
            
        # Upload to S3
        import io
        out_key = f"{s3_prefix}/analysis/{generation_id}.md"
        am.s3.upload_fileobj(out_key, io.BytesIO(md_content.encode('utf-8')))
        
        gen.output_s3_key = out_key
        gen.status = AnalysisStatus.COMPLETED
        db.commit()
        
    except Exception as e:
        logger.error(f"Analysis Generation failed: {str(e)}")
        gen = db.query(AnalysisGeneration).filter(AnalysisGeneration.id == generation_id).first()
        if gen:
            gen.status = AnalysisStatus.FAILED
            gen.error_message = str(e)
            db.commit()
        raise
    finally:
        db.close()
