import logging
import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, List

from src.services.analysis.base import BaseAnalysisJob, AnalysisInput, AnalysisResult, AnalysisProvenance
from src.infrastructure.llm_factory import LLMFactory
from src.services.ingestion.artifact_manager import ArtifactManager
from src.infrastructure.database import SessionLocal
from src.models.document_model import Document

logger = logging.getLogger("document_summarizer")

class DocumentSummarizer(BaseAnalysisJob):
    def __init__(self):
        self.llm = LLMFactory.get_llm()

    async def run(self, input: AnalysisInput, analysis_id: str) -> AnalysisResult:
        if not input.documents:
            raise ValueError("No documents provided for summarization")
            
        doc_id = input.documents[0]
        
        db = SessionLocal()
        try:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if not doc:
                raise ValueError(f"Document {doc_id} not found")
            s3_prefix = doc.s3_prefix or f"documents/{doc.study_unit_id}/{doc_id}"
            
            # Using synchronous ArtifactManager directly
            from src.repositories.s3.storage_repository import S3Storage
            am = ArtifactManager(doc_id, s3_prefix, S3Storage())
            
            # 1. Load canonical.json
            canonical_data = am.download_json(am.canonical_key())
            # 2. Load chunks.json
            chunks_data = am.download_json(am.chunks_key())
            # 3. Load entities.json
            entities_data = am.download_json(am.knowledge_key("entities"))
            
        finally:
            db.close()
            
        nodes = canonical_data.get("nodes", [])
        chunks = chunks_data.get("chunks", [])
        entities = entities_data.get("entities", [])
        
        from langchain_core.messages import HumanMessage
        
        text_to_summarize = ""
        used_nodes = set()
        
        for chunk in chunks[:20]: # limit chunks for safety
            text_to_summarize += chunk.get("text", "") + "\\n\\n"
            used_nodes.update(chunk.get("source_node_ids", []))
            
        prompt = f"""
        You are an academic assistant. Please summarize the following document sections.
        
        {text_to_summarize}
        
        Provide a concise, hierarchical summary.
        """
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        summary_text = response.content
        
        # Prepare output
        result_content = {
            "summary": summary_text,
            "source_nodes": list(used_nodes)
        }
        
        # 6. Save result to S3
        result_s3_key = f"{s3_prefix}/analysis/summary/{analysis_id}.json"
        result_md_s3_key = f"{s3_prefix}/analysis/summary/{analysis_id}.md"
        
        am.upload_json(result_s3_key, result_content)
        
        import io
        from src.repositories.s3.storage_repository import S3Storage
        s3 = S3Storage()
        s3.client.upload_fileobj(
            io.BytesIO(summary_text.encode('utf-8')),
            s3.bucket_name,
            result_md_s3_key,
            ExtraArgs={"ContentType": "text/markdown"}
        )
        
        provenance = AnalysisProvenance(
            source_documents=[doc_id],
            source_nodes=list(used_nodes),
            model="langchain-default",
            model_version="1.0",
            prompt_version="1.0",
            created_at=datetime.now(timezone.utc)
        )
        
        return AnalysisResult(
            analysis_id=analysis_id,
            analysis_type="SUMMARIZE",
            result_s3_key=result_s3_key,
            result_md_s3_key=result_md_s3_key,
            provenance=provenance
        )
