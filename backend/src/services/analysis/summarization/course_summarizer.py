import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.services.analysis.base import BaseAnalysisJob, AnalysisInput, AnalysisResult, AnalysisProvenance
from src.repositories.s3.storage_repository import S3Storage
from src.infrastructure.llm_factory import LLMFactory
import logging

logger = logging.getLogger("course_summarizer")

class CourseSummarizer(BaseAnalysisJob):
    def __init__(self, s3_client=None, llm=None):
        self.s3 = s3_client or S3Storage()
        self.llm_factory = LLMFactory()
        self.llm = llm or self.llm_factory.get_llm("groq/llama-3.3-70b-versatile")
        
    async def run(self, input_data: AnalysisInput, analysis_id: str) -> AnalysisResult:
        logger.info(f"Generating Course Summary {analysis_id}")
        
        all_summaries = []
        source_nodes = []
        
        for doc_id in input_data.documents:
            # We assume artifact_manager.read_json can get chunks.json or canonical.json
            try:
                # We can either read the pre-existing document summary or summarize chunks.
                # Let's read the chunks and do a high level summary, or read existing document summaries.
                # If a document doesn't have an existing summary, we could summarize it on the fly,
                # but since we want course-level intelligence without PDF merging,
                # let's just grab the chunks and sample them or summarize the entities.
                # To keep it lightweight, let's grab entities and a subset of chunks.
                key = f"documents/{doc_id}/artifacts/entities.json"
                entities_data = self.s3.read_json(key)
                
                chunks_key = f"documents/{doc_id}/artifacts/chunks.json"
                chunks_data = self.s3.read_json(chunks_key)
                
                if entities_data and isinstance(entities_data, list):
                    all_summaries.append({
                        "document_id": doc_id,
                        "entities": [e.get("name") for e in entities_data[:20] if isinstance(e, dict)],
                    })
                elif chunks_data and isinstance(chunks_data, list):
                    all_summaries.append({
                        "document_id": doc_id,
                        "content": " ".join([c.get("text", "") for c in chunks_data[:10] if isinstance(c, dict)])
                    })
                    for c in chunks_data[:10]:
                        if isinstance(c, dict) and "section_id" in c:
                            source_nodes.append(c["section_id"])
            except Exception as e:
                logger.warning(f"Failed to load context for {doc_id}: {e}")
                
        # Format map-reduce for course summary
        prompt = """You are an expert educational AI. 
        I will provide you with a high-level overview (entities/chunks) from multiple documents in a course.
        Your task is to generate a single, cohesive 'Course Summary' that synthesizes the main topics across all these documents.
        
        Return a beautiful markdown string containing:
        - A high-level overview of the course themes.
        - A unified list of the most important concepts.
        - A suggested learning path through these topics.
        
        Input Context:
        """
        
        prompt += json.dumps(all_summaries, indent=2)
        
        messages = [
            {"role": "system", "content": "You are a course summarizer. Provide markdown only."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.llm.invoke(messages)
            md_text = response.content.strip()
        except Exception as e:
            logger.error(f"Failed to generate course summary via LLM: {e}")
            md_text = "# Course Summary\n\nFailed to generate summary."
            
        json_data = {
            "title": "Course Summary",
            "summary_md": md_text,
            "documents_included": input_data.documents
        }
        
        # Save artifacts
        json_key = f"analysis/course_summary/{analysis_id}.json"
        md_key = f"analysis/course_summary/{analysis_id}.md"
        
        self.s3.upload_json(json_key, json_data)
        self.s3.upload_file_obj(md_key, md_text.encode('utf-8'))
        
        return AnalysisResult(
            analysis_id=analysis_id,
            analysis_type="course_summary",
            result_s3_key=json_key,
            result_md_s3_key=md_key,
            provenance=AnalysisProvenance(
                source_documents=input_data.documents,
                source_nodes=list(set(source_nodes)),
                model=self.llm_factory.get_model_name("groq/llama-3.3-70b-versatile"),
                model_version="latest",
                prompt_version="1.0",
                created_at=datetime.utcnow()
            )
        )
