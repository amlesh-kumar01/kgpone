import os
import tempfile
import logging
import asyncio
from datetime import datetime, timezone
from celery import shared_task
from sqlalchemy.orm import Session
from src.infrastructure.database import SessionLocal
from src.repositories.postgres.document_repository import DocumentRepository
from src.repositories.s3.storage_repository import S3Storage
from src.models.document_model import ProcessingStatus, Document
from src.models.ingestion_job_model import IngestionJob, IngestionStage, IngestionJobStatus
from src.services.ingestion.artifact_manager import ArtifactManager

logger = logging.getLogger("ingestion_tasks")

def get_artifact_manager(document_id: str, db: Session) -> ArtifactManager:
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise ValueError(f"Document {document_id} not found")
    s3_prefix = doc.s3_prefix or f"documents/{doc.study_unit_id}/{document_id}"
    return ArtifactManager(document_id, s3_prefix, S3Storage())

def set_job_running(db: Session, document_id: str, stage: IngestionStage):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        return
    job = db.query(IngestionJob).filter_by(document_id=document_id, stage=stage).first()
    if not job:
        job = IngestionJob(document_id=document_id, stage=stage)
        db.add(job)
    job.status = IngestionJobStatus.RUNNING
    job.started_at = datetime.now(timezone.utc)
    job.error_message = None
    db.commit()

def set_job_completed(db: Session, document_id: str, stage: IngestionStage, output_s3_key: str = None):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        return
    job = db.query(IngestionJob).filter_by(document_id=document_id, stage=stage).first()
    if job:
        job.status = IngestionJobStatus.COMPLETED
        job.completed_at = datetime.now(timezone.utc)
        job.output_s3_key = output_s3_key
        
    if output_s3_key:
        import copy
        new_artifacts = copy.deepcopy(doc.artifacts or {})
        new_artifacts[stage.value.lower()] = output_s3_key
        doc.artifacts = new_artifacts
        
    db.commit()

def set_job_failed(db: Session, document_id: str, stage: IngestionStage, error: str):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        return
    job = db.query(IngestionJob).filter_by(document_id=document_id, stage=stage).first()
    if job:
        job.status = IngestionJobStatus.FAILED
        job.completed_at = datetime.now(timezone.utc)
        job.error_message = error
        db.commit()

@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3)
def parse_document_task(self, document_id: str):
    db = SessionLocal()
    stage = IngestionStage.PARSE
    try:
        set_job_running(db, document_id, stage)
        
        doc = db.query(Document).filter(Document.id == document_id).first()
        file_key = doc.original_s3_key if doc.original_s3_key else doc.s3_key
        
        s3 = S3Storage()
        ext = os.path.splitext(file_key)[1] or ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            temp_path = tmp.name
        s3.download_file(file_key, temp_path)
        
        am = get_artifact_manager(document_id, db)
        am.init_manifest()
        
        try:
            from src.services.ingestion.parser.docling_parser import DoclingParser
            logger.info(f"Attempting to parse document {document_id} with DoclingParser")
            parser = DoclingParser(artifact_manager=am)
            canonical_doc = parser.parse(temp_path)
            
            # Save the canonical document immediately (Docling combines PARSE and AST)
            am.upload_json(am.canonical_key(), canonical_doc.model_dump(mode="json"))
            
            parser_key = am.parser_key("docling")
            set_job_completed(db, document_id, stage, parser_key)
            logger.info(f"Docling parsing succeeded for {document_id}")
            
        except Exception as docling_err:
            logger.warning(f"Docling failed ({docling_err}). Falling back to LlamaParse.")
            from src.services.ingestion.parser.llama_parser import LlamaParserImpl
            
            parser = LlamaParserImpl(document_id=document_id, s3_storage=s3)
            parsed_data = asyncio.run(parser.parse(temp_path, ""))
            
            parser_key = am.parser_key("llamaparse")
            am.upload_json(parser_key, {"raw": parsed_data.model_dump(mode="json")})
            
            set_job_completed(db, document_id, stage, parser_key)
            logger.info(f"LlamaParse fallback succeeded for {document_id}")
            
        os.remove(temp_path)
        
        # Auto-chain to AST stage
        build_canonical_ast_task.delay(document_id)
    except Exception as e:
        db.rollback()
        set_job_failed(db, document_id, stage, str(e))
        db.query(Document).filter(Document.id == document_id).update({"status": ProcessingStatus.FAILED})
        db.commit()
        raise
    finally:
        db.close()

@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3)
def build_canonical_ast_task(self, document_id: str):
    db = SessionLocal()
    stage = IngestionStage.AST
    try:
        set_job_running(db, document_id, stage)
        am = get_artifact_manager(document_id, db)
        
        # Check if canonical doc was already generated by Docling during PARSE stage
        existing_canonical = am.download_json(am.canonical_key())
        if existing_canonical:
            logger.info(f"Canonical AST already generated by Docling for {document_id}. Skipping AST build.")
            set_job_completed(db, document_id, stage, am.canonical_key())
            return
            
        logger.info(f"Building AST from LlamaParse fallback for {document_id}")
        doc = db.query(Document).filter(Document.id == document_id).first()
        file_key = doc.original_s3_key if doc.original_s3_key else doc.s3_key
        s3 = S3Storage()
        ext = os.path.splitext(file_key)[1] or ".pdf"
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            temp_path = tmp.name
        s3.download_file(file_key, temp_path)
        
        from src.services.ingestion.parser.llama_parser import LlamaParserImpl
        from src.services.ingestion.canonical.ast_builder import ASTBuilder
        
        parser = LlamaParserImpl(document_id=document_id, s3_storage=s3)
        ast_builder = ASTBuilder(am, parser)
        
        canonical_doc = asyncio.run(ast_builder.build(temp_path, ""))
        os.remove(temp_path)
        
        set_job_completed(db, document_id, stage, am.canonical_key())
        
        extract_entities_task.delay(document_id)
        
    except Exception as e:
        db.rollback()
        set_job_failed(db, document_id, stage, str(e))
        db.query(Document).filter(Document.id == document_id).update({"status": ProcessingStatus.FAILED})
        db.commit()
        raise
    finally:
        db.close()

@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3)
def extract_entities_task(self, document_id: str):
    db = SessionLocal()
    stage = IngestionStage.ENTITY
    try:
        set_job_running(db, document_id, stage)
        am = get_artifact_manager(document_id, db)
        
        canonical_doc = am.download_json(am.canonical_key())
        
        from src.services.ingestion.extraction.gliner_extractor import GLiNERExtractor
        from src.services.ingestion.extraction.llm_extractor import LLMEntityExtractor
        from src.services.ingestion.canonical.ast_schema import CanonicalDocument
        import asyncio
        
        canonical_model = CanonicalDocument(**canonical_doc)
        
        # 1. Heuristic Extraction (GLiNER)
        extractor = GLiNERExtractor()
        entities_res = asyncio.run(extractor.extract(canonical_model.nodes, {}))
        entities = entities_res.get("entities", [])
        
        # 2. Neural Fallback (LLM) for high-value chunks
        llm_extractor = LLMEntityExtractor()
        # Collect top 10 longest paragraphs to send to LLM
        text_chunks = [n.text_content for n in canonical_model.nodes if getattr(n, "text_content", None)]
        text_chunks = sorted(text_chunks, key=len, reverse=True)[:10]
        
        if text_chunks:
            llm_entities_res = asyncio.run(llm_extractor.extract(text_chunks, {"title": canonical_model.title, "doc_type": canonical_model.doc_type}))
            # Merge LLM entities (topics, concepts, algorithms) into the main entities list
            for category in ["topics", "concepts", "algorithms", "technologies"]:
                for item in llm_entities_res.get(category, []):
                    entities.append({
                        "canonical_name": item.get("name", ""),
                        "surface_forms": [item.get("name", "")],
                        "type": category.upper()[:-1], # e.g. CONCEPT
                        "confidence": 0.9,
                        "description": item.get("description", "")
                    })
                    
        out_key = am.knowledge_key("entities")
        am.upload_json(out_key, {"entities": entities})
        
        set_job_completed(db, document_id, stage, out_key)
        extract_relations_task.delay(document_id)
        
    except Exception as e:
        db.rollback()
        set_job_failed(db, document_id, stage, str(e))
        db.query(Document).filter(Document.id == document_id).update({"status": ProcessingStatus.FAILED})
        db.commit()
        raise
    finally:
        db.close()

@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3)
def extract_relations_task(self, document_id: str):
    db = SessionLocal()
    stage = IngestionStage.RELATION
    try:
        set_job_running(db, document_id, stage)
        am = get_artifact_manager(document_id, db)
        
        canonical_doc = am.download_json(am.canonical_key())
        if isinstance(canonical_doc, str):
            import json
            canonical_doc = json.loads(canonical_doc)
            
        entities_data = am.download_json(am.knowledge_key("entities"))
        if isinstance(entities_data, str):
            import json
            entities_data = json.loads(entities_data)
        entities = entities_data.get("entities", []) if isinstance(entities_data, dict) else []
        
        from src.services.ingestion.extraction.relation_extractor import RelationExtractor
        from src.services.ingestion.canonical.ast_schema import CanonicalDocument
        extractor = RelationExtractor()
        canonical_model = CanonicalDocument(**canonical_doc)
        import asyncio
        relations = asyncio.run(extractor.extract_relations(canonical_model.nodes, entities))
        
        out_key = am.knowledge_key("relations")
        am.upload_json(out_key, {"relations": relations})
        
        set_job_completed(db, document_id, stage, out_key)
        build_neo4j_task.delay(document_id)
        
    except Exception as e:
        db.rollback()
        set_job_failed(db, document_id, stage, str(e))
        db.query(Document).filter(Document.id == document_id).update({"status": ProcessingStatus.FAILED})
        db.commit()
        raise
    finally:
        db.close()

@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3)
def build_chunks_task(self, document_id: str):
    db = SessionLocal()
    stage = IngestionStage.CHUNK
    try:
        set_job_running(db, document_id, stage)
        am = get_artifact_manager(document_id, db)
        
        canonical_doc = am.download_json(am.canonical_key())
        if isinstance(canonical_doc, str):
            import json
            canonical_doc = json.loads(canonical_doc)
            
        entities_data = am.download_json(am.knowledge_key("entities"))
        if isinstance(entities_data, str):
            import json
            entities_data = json.loads(entities_data)
        entities = entities_data.get("entities", []) if isinstance(entities_data, dict) else []
        
        formulas_data = am.download_json(am.knowledge_key("formulas"))
        if isinstance(formulas_data, str):
            import json
            formulas_data = json.loads(formulas_data)
        formulas = formulas_data.get("formulas", []) if isinstance(formulas_data, dict) else []
        
        from src.services.ingestion.chunking.ast_chunker import ASTChunker
        from src.services.ingestion.canonical.ast_schema import CanonicalDocument
        chunker = ASTChunker()
        chunks = chunker.chunk(CanonicalDocument(**canonical_doc), entities, formulas)
        
        out_key = am.chunks_key()
        am.upload_json(out_key, {"chunks": chunks})
        
        set_job_completed(db, document_id, stage, out_key)
        
        index_qdrant_task.delay(document_id)
        
    except Exception as e:
        db.rollback()
        set_job_failed(db, document_id, stage, str(e))
        db.query(Document).filter(Document.id == document_id).update({"status": ProcessingStatus.FAILED})
        db.commit()
        raise
    finally:
        db.close()

@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3)
def index_qdrant_task(self, document_id: str):
    db = SessionLocal()
    stage = IngestionStage.EMBED
    try:
        set_job_running(db, document_id, stage)
        am = get_artifact_manager(document_id, db)
        
        chunks_data = am.download_json(am.chunks_key())
        if isinstance(chunks_data, str):
            import json
            chunks_data = json.loads(chunks_data)
        chunks = chunks_data.get("chunks", []) if isinstance(chunks_data, dict) else []
        if not chunks:
            set_job_completed(db, document_id, stage, None)
            extract_entities_task.delay(document_id)
            return
            
        texts = [c["text"] for c in chunks]
        
        from src.services.ingestion.embedding.llm_embedding import LLMEmbedder
        embedder = LLMEmbedder()
        embeddings = asyncio.run(embedder.embed(texts))
        
        from src.repositories.qdrant.vector_repository import QdrantRepository
        repo = QdrantRepository()
        
        # Delete old vectors to prevent orphan chunks upon retry
        repo.delete_by_filter("documents", {"document_id": document_id})
        
        doc = db.query(Document).filter(Document.id == document_id).first()
        study_unit = doc.study_unit
        
        metadatas = []
        for c in chunks:
            meta = {
                "document_id": document_id,
                "study_unit_code": study_unit.code,
                "document_type": doc.doc_type,
                "chunk_id": c["chunk_id"],
                "text": c["text"],
                "section_id": c.get("section_id"),
                "heading_path": " > ".join(c.get("heading_path", [])),
                "concept_ids": c.get("concept_ids", []),
                "formula_ids": c.get("formula_ids", [])
            }
            metadatas.append(meta)
            
        asyncio.run(repo.upsert("documents", embeddings, metadatas))
        
        set_job_completed(db, document_id, stage, None)
        finalize_manifest_task.delay(document_id)
        
    except Exception as e:
        db.rollback()
        set_job_failed(db, document_id, stage, str(e))
        db.query(Document).filter(Document.id == document_id).update({"status": ProcessingStatus.FAILED})
        db.commit()
        raise
    finally:
        db.close()

@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3)
def build_neo4j_task(self, document_id: str):
    db = SessionLocal()
    stage = IngestionStage.GRAPH
    try:
        set_job_running(db, document_id, stage)
        set_job_completed(db, document_id, stage, None)
        build_chunks_task.delay(document_id)
    except Exception as e:
        db.rollback()
        set_job_failed(db, document_id, stage, str(e))
        db.query(Document).filter(Document.id == document_id).update({"status": ProcessingStatus.FAILED})
        db.commit()
        raise
    finally:
        db.close()

@shared_task(bind=True, autoretry_for=(Exception,), max_retries=3)
def finalize_manifest_task(self, document_id: str):
    db = SessionLocal()
    stage = IngestionStage.MANIFEST
    try:
        set_job_running(db, document_id, stage)
        
        am = get_artifact_manager(document_id, db)
        doc = db.query(Document).filter(Document.id == document_id).first()
        
        # Gather stats
        chunks_data = am.download_json(am.chunks_key()) or {}
        if isinstance(chunks_data, str):
            import json
            chunks_data = json.loads(chunks_data)
        num_chunks = len(chunks_data.get("chunks", []))
        
        entities_data = am.download_json(am.knowledge_key("entities")) or {}
        if isinstance(entities_data, str):
            import json
            entities_data = json.loads(entities_data)
        num_entities = len(entities_data.get("entities", []))
        
        manifest_data = {
            "document_id": document_id,
            "title": doc.title,
            "status": "COMPLETED",
            "stats": {
                "chunks": num_chunks,
                "entities": num_entities,
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Generate Markdown Summary
        summary_md = f"# Summary for {doc.title}\n\n"
        summary_md += f"**Document ID**: {document_id}\n\n"
        summary_md += f"This document has been successfully processed into {num_chunks} logical chunks and {num_entities} key entities.\n\n"
        
        # Try to generate an LLM summary of the first few chunks
        if chunks_data.get("chunks"):
            try:
                from src.infrastructure.llm_factory import LLMFactory
                from langchain_core.prompts import ChatPromptTemplate
                import asyncio
                llm = LLMFactory().get_llm()
                prompt = ChatPromptTemplate.from_messages([
                    ("system", "Write a concise, 3-paragraph study guide summary of the provided text. Format it beautifully in Markdown."),
                    ("user", "Text:\n\n{text}")
                ])
                chain = prompt | llm
                
                # Take first 5 chunks to summarize
                sample_text = "\n\n".join([c["text"] for c in chunks_data["chunks"][:5]])
                res = asyncio.run(chain.ainvoke({"text": sample_text}))
                content_str = res.content
                if isinstance(content_str, list):
                    content_str = "".join([c.get("text", "") if isinstance(c, dict) else str(c) for c in content_str])
                
                summary_md += "## Executive Summary\n\n" + str(content_str)
            except Exception as e:
                logger.warning(f"Failed to generate LLM summary: {e}")
                summary_md += "*(LLM Summary generation failed or skipped)*"
        
        # Upload Summary to S3
        summary_key = am.s3_prefix + "/summary.md"
        am.upload_text(summary_key, summary_md)
        
        # Upload Manifest to S3
        manifest_key = am.manifest_key()
        am.upload_json(manifest_key, manifest_data)
        
        # Also update Document record with summary key
        import copy
        new_artifacts = copy.deepcopy(doc.artifacts or {})
        new_artifacts["summary"] = summary_key
        doc.artifacts = new_artifacts
        
        db.query(Document).filter(Document.id == document_id).update({"status": ProcessingStatus.COMPLETED})
        db.commit()
        
        set_job_completed(db, document_id, stage, manifest_key)
        logger.info(f"Pipeline completed for document {document_id}")
    except Exception as e:
        db.rollback()
        set_job_failed(db, document_id, stage, str(e))
        db.query(Document).filter(Document.id == document_id).update({"status": ProcessingStatus.FAILED})
        db.commit()
        raise
    finally:
        db.close()

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_document_task(self, document_id: str, old_version: int = None):
    parse_document_task.delay(document_id)
    if old_version is not None:
        from src.workers.tasks.cleanup_tasks import delete_old_vectors_task
        delete_old_vectors_task.delay(document_id, old_version)
