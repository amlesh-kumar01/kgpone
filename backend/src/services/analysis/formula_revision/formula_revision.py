import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.services.analysis.base import BaseAnalysisJob, AnalysisInput, AnalysisResult, AnalysisProvenance
from src.repositories.s3.storage_repository import S3Storage
from src.repositories.neo4j.graph_repository import Neo4jRepo
from src.infrastructure.llm_factory import LLMFactory
from src.infrastructure.database import SessionLocal
from src.models.document_model import Document
import logging

logger = logging.getLogger("formula_revision")

class FormulaRevisionGenerator(BaseAnalysisJob):
    def __init__(self, s3_client=None, llm=None):
        self.s3 = s3_client or S3Storage()
        self.graph_repo = Neo4jRepo()
        self.llm_factory = LLMFactory()
        self.llm = llm or self.llm_factory.get_llm("groq/llama-3.3-70b-versatile")
        
    async def run(self, input_data: AnalysisInput, analysis_id: str) -> AnalysisResult:
        logger.info(f"Generating Formula Revision {analysis_id}")
        
        all_formulas = []
        source_nodes = []
        
        # Load formulas.json
        with SessionLocal() as db:
            for doc_id in input_data.documents:
                try:
                    doc = db.query(Document).filter(Document.id == doc_id).first()
                    s3_prefix = doc.s3_prefix if doc and doc.s3_prefix else f"documents/{doc.study_unit_id}/{doc_id}"
                    key = f"{s3_prefix}/artifacts/formulas.json"
                    formulas_data = self.s3.read_json(key)
                if formulas_data and isinstance(formulas_data, list):
                    all_formulas.extend(formulas_data)
                    for f in formulas_data:
                        if "section_id" in f:
                            source_nodes.append(f["section_id"])
            except Exception as e:
                logger.warning(f"Failed to load formulas.json for {doc_id}: {e}")

        # Augment with Graph Context
        for f in all_formulas:
            formula_name = f.get("name")
            if not formula_name:
                continue
                
            try:
                # Find related concepts in Neo4j
                cypher = """
                MATCH (f:Formula) WHERE toLower(f.name) CONTAINS toLower($name)
                OPTIONAL MATCH (f)-[:RELATED_TO]->(c:Concept)
                RETURN c.name as related_concept
                LIMIT 5
                """
                # For safety, since our ingestion might have called them entities, we search Entity/Topic
                cypher_fallback = """
                MATCH (e) WHERE toLower(e.name) CONTAINS toLower($name)
                OPTIONAL MATCH (e)-[]-(related)
                RETURN related.name as related_concept
                LIMIT 3
                """
                results = self.graph_repo.execute_read_query(cypher_fallback, {"name": formula_name})
                related_concepts = [r["related_concept"] for r in results if r.get("related_concept")]
                if related_concepts:
                    f["related_concepts_graph"] = list(set(related_concepts))
            except Exception as e:
                logger.warning(f"Graph lookup failed for formula {formula_name}: {e}")

        # Build JSON
        revision_json = {
            "title": "Formula Revision Sheet",
            "formulas": all_formulas
        }
        
        # Build MD
        md_lines = ["# Formula Revision Sheet", ""]
        if not all_formulas:
            md_lines.append("No formulas were found in the selected documents.")
        
        for f in all_formulas:
            name = f.get("name", "Unnamed Formula")
            equation = f.get("equation", "")
            desc = f.get("description", "")
            
            md_lines.append(f"## {name}")
            if equation:
                md_lines.append(f"$$ {equation} $$")
            if desc:
                md_lines.append(f"**Description:** {desc}")
                
            variables = f.get("variables", [])
            if variables:
                md_lines.append("\n**Variables:**")
                for var in variables:
                    v_name = var.get("symbol", "")
                    v_desc = var.get("description", "")
                    md_lines.append(f"- `{v_name}`: {v_desc}")
            
            related = f.get("related_concepts_graph") or f.get("related_concepts")
            if related:
                md_lines.append(f"\n**Related Concepts:** {', '.join(related)}")
                
            md_lines.append("\n---")
            
        md_text = "\n".join(md_lines)
        
        # Save artifacts
        json_key = f"analysis/formula_revision/{analysis_id}.json"
        md_key = f"analysis/formula_revision/{analysis_id}.md"
        
        self.s3.upload_json(json_key, revision_json)
        self.s3.upload_file_obj(md_key, md_text.encode('utf-8'))
        
        return AnalysisResult(
            analysis_id=analysis_id,
            analysis_type="formula_revision",
            result_s3_key=json_key,
            result_md_s3_key=md_key,
            provenance=AnalysisProvenance(
                source_documents=input_data.documents,
                source_nodes=list(set(source_nodes)),
                model="neo4j_graph_expansion",
                model_version="1.0",
                prompt_version="1.0",
                created_at=datetime.utcnow()
            )
        )
