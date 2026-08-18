import logging
import re
import uuid
from typing import List, Dict, Any
from src.services.ingestion.canonical.ast_schema import ASTNode, NodeType

logger = logging.getLogger("question_extractor")

class QuestionExtractor:
    def __init__(self):
        # Q1., Q1), 1., 1) followed by text, allowing spaces
        self.question_markers = re.compile(r'^(?:Q?\s*\d+\s*[.)\]]|(?:[a-d]\s*[.)\]]))\s*(.+)', re.IGNORECASE)
        # Ends with question mark
        self.question_mark_end = re.compile(r'.*\?\s*$')
        
    def extract(self, nodes: List[ASTNode], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts questions from AST nodes.
        """
        questions = []
        
        # Determine document-level exam/year context if available
        doc_type = context.get("doc_type", "")
        year = context.get("year")
        exam = context.get("exam", context.get("title") if doc_type == "PYQ" else None)
        
        for node in nodes:
            if not node.text_content:
                continue
                
            text = node.text_content.strip()
            
            is_question = False
            q_type = "Short"
            marks = None
            
            # Check native AST type if added in future
            # if node.type == NodeType.QUESTION: is_question = True
            
            # Check regex
            if self.question_mark_end.match(text):
                is_question = True
            elif self.question_markers.match(text):
                # Ensure it's not just a numbered list of statements.
                # Usually questions have question words or ? or it's a PYQ doc.
                if doc_type == "PYQ" or "?" in text or any(w in text.lower() for w in ["what", "why", "how", "calculate", "prove", "derive", "find"]):
                    is_question = True
                
            # Basic classification
            if is_question:
                lower_text = text.lower()
                if "prove that" in lower_text or "derive" in lower_text:
                    q_type = "Proof/Derivation"
                elif "(a)" in lower_text and "(b)" in lower_text and "(c)" in lower_text:
                    q_type = "MCQ"
                elif "calculate" in lower_text or "find the value" in lower_text:
                    q_type = "Numerical"
                    
                # Look for marks like [5] or (10 Marks)
                marks_match = re.search(r'\[(\d+)\]|\((\d+)\s*[Mm]arks?\)', text)
                if marks_match:
                    marks_str = marks_match.group(1) or marks_match.group(2)
                    try:
                        marks = int(marks_str)
                    except ValueError:
                        pass
                
                questions.append({
                    "id": str(uuid.uuid4()),
                    "question_text": text,
                    "question_type": q_type,
                    "marks": marks,
                    "year": year,
                    "exam": exam,
                    "source_node_id": node.id,
                    "source_page": node.source.page_start if node.source else None
                })
                
        return {"questions": questions}
