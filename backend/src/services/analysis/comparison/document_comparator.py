import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.services.analysis.base import BaseAnalysisJob, AnalysisInput, AnalysisResult, AnalysisProvenance
from src.repositories.s3.storage_repository import S3Storage
from src.infrastructure.llm_factory import LLMFactory
from src.infrastructure.database import SessionLocal
from src.models.document_model import Document
import logging

logger = logging.getLogger("document_comparator")

class DocumentComparator(BaseAnalysisJob):
    def __init__(self, s3_client=None, llm=None):
        self.s3 = s3_client or S3Storage()
        self.llm_factory = LLMFactory()
        self.llm = llm or self.llm_factory.get_llm("groq/llama-3.3-70b-versatile")
        
    async def run(self, input_data: AnalysisInput, analysis_id: str) -> AnalysisResult:
        logger.info(f"Generating Document Comparison {analysis_id}")
        
        if len(input_data.documents) < 2:
            raise ValueError("Comparison requires at least 2 documents.")
            
        doc_data = {}
        source_nodes = []
        
        with SessionLocal() as db:
            for doc_id in input_data.documents:
                doc_data[doc_id] = {"entities": [], "formulas": []}
                try:
                    doc = db.query(Document).filter(Document.id == doc_id).first()
                    s3_prefix = doc.s3_prefix if doc and doc.s3_prefix else f"documents/UNKNOWN/{doc_id}"
                    e_key = f"{s3_prefix}/artifacts/entities.json"
                    entities_data = self.s3.read_json(e_key)
                    if entities_data and isinstance(entities_data, list):
                        doc_data[doc_id]["entities"] = [e.get("name") for e in entities_data if isinstance(e, dict) and e.get("name")]
                    
                    f_key = f"{s3_prefix}/artifacts/formulas.json"
                    formulas_data = self.s3.read_json(f_key)
                    if formulas_data and isinstance(formulas_data, list):
                        doc_data[doc_id]["formulas"] = [f.get("name") for f in formulas_data if isinstance(f, dict) and f.get("name")]
                except Exception as e:
                    logger.warning(f"Failed to load artifacts for {doc_id}: {e}")
                
        # For simplicity, we just compare Doc A vs everything else if > 2, but usually it's [A, B]
        doc_ids = input_data.documents
        doc_a = doc_ids[0]
        doc_b = doc_ids[1]
        
        entities_a = set(doc_data[doc_a]["entities"])
        entities_b = set(doc_data[doc_b]["entities"])
        
        formulas_a = set(doc_data[doc_a]["formulas"])
        formulas_b = set(doc_data[doc_b]["formulas"])
        
        common_entities = entities_a.intersection(entities_b)
        unique_a = entities_a - entities_b
        unique_b = entities_b - entities_a
        
        common_formulas = formulas_a.intersection(formulas_b)
        f_unique_a = formulas_a - formulas_b
        f_unique_b = formulas_b - formulas_a
        
        json_data = {
            "title": "Document Comparison Report",
            "document_a": doc_a,
            "document_b": doc_b,
            "comparison": {
                "entities": {
                    "common": list(common_entities),
                    "unique_to_a": list(unique_a),
                    "unique_to_b": list(unique_b)
                },
                "formulas": {
                    "common": list(common_formulas),
                    "unique_to_a": list(f_unique_a),
                    "unique_to_b": list(f_unique_b)
                }
            }
        }
        
        md_lines = [
            "# Document Comparison Report", 
            f"Comparing Document A (`{doc_a}`) and Document B (`{doc_b}`).",
            "",
            "## Entity Coverage",
            f"**Common Concepts ({len(common_entities)}):** {', '.join(common_entities) if common_entities else 'None'}",
            f"**Only in Document A ({len(unique_a)}):** {', '.join(unique_a) if unique_a else 'None'}",
            f"**Only in Document B ({len(unique_b)}):** {', '.join(unique_b) if unique_b else 'None'}",
            "",
            "## Formula Coverage",
            f"**Common Formulas ({len(common_formulas)}):** {', '.join(common_formulas) if common_formulas else 'None'}",
            f"**Only in Document A ({len(f_unique_a)}):** {', '.join(f_unique_a) if f_unique_a else 'None'}",
            f"**Only in Document B ({len(f_unique_b)}):** {', '.join(f_unique_b) if f_unique_b else 'None'}",
            ""
        ]
        md_text = "\n".join(md_lines)
        
        # Save artifacts
        json_key = f"analysis/comparison/{analysis_id}.json"
        md_key = f"analysis/comparison/{analysis_id}.md"
        
        self.s3.upload_json(json_key, json_data)
        self.s3.upload_file_obj(md_key, md_text.encode('utf-8'))
        
        return AnalysisResult(
            analysis_id=analysis_id,
            analysis_type="document_comparison",
            result_s3_key=json_key,
            result_md_s3_key=md_key,
            provenance=AnalysisProvenance(
                source_documents=input_data.documents,
                source_nodes=list(set(source_nodes)),
                model="deterministic_set_intersection",
                model_version="1.0",
                prompt_version="1.0",
                created_at=datetime.utcnow()
            )
        )
