import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.repositories.postgres.document_repository import DocumentRepository
from src.repositories.neo4j.graph_repository import Neo4jRepo
from src.services.ingestion.artifact_manager import ArtifactManager
from src.repositories.s3.storage_repository import S3Storage
from src.models.ingestion_job_model import IngestionJob

logger = logging.getLogger("document_inspector")

class ArtifactEntry(BaseModel):
    name: str
    s3_key: str
    exists: bool

class IngestionStageStatus(BaseModel):
    stage: str
    status: str
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

class InspectionReport(BaseModel):
    document_id: str
    s3_prefix: str
    manifest: dict
    stages: List[IngestionStageStatus]
    canonical_summary: dict
    knowledge_summary: dict
    qdrant_summary: dict
    neo4j_summary: dict
    artifacts: List[ArtifactEntry]

class DocumentInspector:
    def __init__(self, db: Session):
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.s3 = S3Storage()
        self.neo4j_repo = Neo4jRepo()

    def inspect(self, document_id: str) -> InspectionReport:
        # Get document
        doc = self.doc_repo.get_by_id(UUID(document_id))
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        s3_prefix = doc.s3_prefix or f"documents/UNKNOWN/UNKNOWN/UNKNOWN/{document_id}"
        artifact_manager = ArtifactManager(document_id, s3_prefix, self.s3)
        
        # 1. Manifest
        manifest = {}
        if artifact_manager.exists(artifact_manager.manifest_key()):
            manifest = artifact_manager.read_manifest()

        # 2. Artifacts existence
        keys_to_check = [
            ("Original", artifact_manager.original_key("document.pdf")),
            ("Docling JSON", artifact_manager.parser_key("docling")),
            ("LlamaParse JSON", artifact_manager.parser_key("llamaparse")),
            ("Canonical AST", artifact_manager.canonical_key()),
            ("Hierarchy", artifact_manager.hierarchy_key()),
            ("Entities", artifact_manager.knowledge_key("entities")),
            ("Concepts", artifact_manager.knowledge_key("concepts")),
            ("Relations", artifact_manager.knowledge_key("relations")),
            ("Formulas", artifact_manager.knowledge_key("formulas")),
            ("Questions", artifact_manager.knowledge_key("questions")),
            ("Chunks", artifact_manager.chunks_key()),
            ("Ingestion Log", artifact_manager.log_key())
        ]
        
        artifacts = []
        for name, key in keys_to_check:
            exists = artifact_manager.exists(key)
            artifacts.append(ArtifactEntry(name=name, s3_key=key, exists=exists))

        # 3. Stages
        stages = []
        jobs = self.db.query(IngestionJob).filter(IngestionJob.document_id == doc.id).order_by(IngestionJob.started_at).all()
        for job in jobs:
            stages.append(IngestionStageStatus(
                stage=job.stage.value if hasattr(job.stage, 'value') else str(job.stage),
                status=job.status.value if hasattr(job.status, 'value') else str(job.status),
                error_message=job.error_message,
                started_at=job.started_at.isoformat() if job.started_at else None,
                completed_at=job.completed_at.isoformat() if job.completed_at else None
            ))

        # 4. Canonical & Knowledge Summary (read from S3 if exists)
        canonical_summary = {"node_count": 0, "types": {}}
        if artifact_manager.exists(artifact_manager.canonical_key()):
            try:
                ast_data = artifact_manager.download_json(artifact_manager.canonical_key())
                nodes = ast_data.get("nodes", [])
                canonical_summary["node_count"] = len(nodes)
                for node in nodes:
                    t = node.get("type", "UNKNOWN")
                    canonical_summary["types"][t] = canonical_summary["types"].get(t, 0) + 1
            except Exception:
                pass

        knowledge_summary = {"entities": 0, "formulas": 0, "questions": 0, "relations": 0}
        for k in ["entities", "formulas", "questions", "relations"]:
            key = artifact_manager.knowledge_key(k)
            if artifact_manager.exists(key):
                try:
                    data = artifact_manager.download_json(key)
                    # Support both list and dict formats
                    items = data.get(k, data) if isinstance(data, dict) else data
                    knowledge_summary[k] = len(items) if isinstance(items, list) else 0
                except Exception:
                    pass

        # 5. Neo4j Summary
        neo4j_summary = {"node_count": 0, "rel_count": 0}
        try:
            query = """
            MATCH (d:Document {doc_id: $doc_id})
            OPTIONAL MATCH (d)-[r]->(e)
            RETURN count(e) as node_count, count(r) as rel_count
            """
            result = self.neo4j_repo.execute_read_query(query, {"doc_id": document_id})
            if result:
                neo4j_summary["node_count"] = result[0]["node_count"]
                neo4j_summary["rel_count"] = result[0]["rel_count"]
        except Exception as e:
            logger.warning(f"Neo4j query failed in inspector: {e}")

        qdrant_summary = {"chunk_count": "Not implemented"}

        return InspectionReport(
            document_id=document_id,
            s3_prefix=s3_prefix,
            manifest=manifest,
            stages=stages,
            canonical_summary=canonical_summary,
            knowledge_summary=knowledge_summary,
            qdrant_summary=qdrant_summary,
            neo4j_summary=neo4j_summary,
            artifacts=artifacts
        )
