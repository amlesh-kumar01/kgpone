import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.services.analysis.base import BaseAnalysisJob, AnalysisInput, AnalysisResult, AnalysisProvenance
from src.repositories.s3.storage_repository import S3Storage
from src.infrastructure.llm_factory import LLMFactory
from src.services.ingestion.artifact_manager import ArtifactManager
import logging

logger = logging.getLogger("quiz_generator")

class QuizGenerator(BaseAnalysisJob):
    def __init__(self, s3_client=None, llm=None):
        self.s3 = s3_client or S3Storage()
        self.artifact_manager = ArtifactManager()
        self.llm_factory = LLMFactory()
        self.llm = llm or self.llm_factory.get_llm("groq/llama-3.3-70b-versatile")
        
    async def run(self, input_data: AnalysisInput, analysis_id: str) -> AnalysisResult:
        logger.info(f"Generating Quiz {analysis_id}")
        
        # Load questions.json from provided documents
        all_questions = []
        source_nodes = []
        
        for doc_id in input_data.documents:
            # We assume artifact_manager.read_json can get questions.json
            try:
                # The artifact manager is designed for canonical.json, chunks.json, entities.json
                # We can construct the S3 key directly if needed or use artifact manager
                key = f"documents/{doc_id}/artifacts/questions.json"
                questions_data = self.s3.read_json(key)
                if questions_data and isinstance(questions_data, list):
                    all_questions.extend(questions_data)
                    for q in questions_data:
                        if "section_id" in q:
                            source_nodes.append(q["section_id"])
            except Exception as e:
                logger.warning(f"Failed to load questions.json for {doc_id}: {e}")
                
        if not all_questions:
            quiz_json = {"title": "Generated Quiz", "questions": []}
            md_text = "# Quiz\n\nNo questions were found in the provided documents."
        else:
            # Pick a subset of questions to avoid massive prompts (e.g. max 10)
            import random
            selected_questions = random.sample(all_questions, min(10, len(all_questions)))
            
            # Format quiz using LLM
            prompt = """You are an expert educational AI. 
            I will provide you with a list of extracted questions/statements from academic notes.
            Your task is to convert each into a structured Multiple Choice Question (MCQ).
            For each question, provide exactly 4 options, identifying the correct one, and a brief explanation.
            
            Return ONLY a valid JSON array of objects, with no markdown formatting around it. Each object must have:
            - question_text (string)
            - options (array of exactly 4 strings)
            - correct_answer (string, matching one of the options)
            - explanation (string)
            - source_node_id (string, copy exactly from input)
            - source_page (integer or null, copy exactly from input)
            
            Input Questions:
            """
            
            input_q_data = [{"text": q.get("question_text"), "source_node_id": q.get("source_node_id"), "source_page": q.get("source_page")} for q in selected_questions]
            prompt += json.dumps(input_q_data, indent=2)
            
            messages = [
                {"role": "system", "content": "You are a JSON-only generating assistant."},
                {"role": "user", "content": prompt}
            ]
            
            try:
                response = self.llm.invoke(messages)
                content = response.content.strip()
                # Remove json block ticks if any
                if content.startswith("```json"):
                    content = content[7:-3]
                elif content.startswith("```"):
                    content = content[3:-3]
                
                generated_quiz = json.loads(content)
            except Exception as e:
                logger.error(f"Failed to generate quiz via LLM: {e}")
                generated_quiz = []
                
            quiz_json = {
                "title": "Generated Study Quiz",
                "questions": generated_quiz
            }
            
            # Convert to MD
            md_lines = ["# Generated Study Quiz", ""]
            for i, q in enumerate(generated_quiz):
                md_lines.append(f"### Q{i+1}: {q.get('question_text', 'Question?')}")
                if "options" in q:
                    for j, opt in enumerate(q["options"]):
                        md_lines.append(f"{['A', 'B', 'C', 'D'][j]}) {opt}")
                md_lines.append("")
                md_lines.append(f"<details><summary><b>Show Answer</b></summary>")
                md_lines.append(f"**Answer:** {q.get('correct_answer', 'N/A')}<br>")
                md_lines.append(f"**Explanation:** {q.get('explanation', 'N/A')}<br>")
                page = q.get('source_page')
                page_str = f" (Page {page})" if page else ""
                md_lines.append(f"*(Source Node: {q.get('source_node_id', 'Unknown')}{page_str})*")
                md_lines.append(f"</details>")
                md_lines.append("")
                
            md_text = "\n".join(md_lines)
        
        # Save artifacts
        json_key = f"analysis/quiz/{analysis_id}.json"
        md_key = f"analysis/quiz/{analysis_id}.md"
        
        self.s3.upload_json(json_key, quiz_json)
        self.s3.upload_file_obj(md_key, md_text.encode('utf-8'))
        
        return AnalysisResult(
            analysis_id=analysis_id,
            analysis_type="quiz",
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
