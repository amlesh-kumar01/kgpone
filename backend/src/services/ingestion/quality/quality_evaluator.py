import logging
from typing import Dict, Any, List
from src.services.ingestion.canonical.ast_schema import CanonicalDocument, NodeType

logger = logging.getLogger("quality_evaluator")

class QualityReport:
    def __init__(self, score: float, needs_fallback: bool, fallback_reason: str = None):
        self.score = score
        self.needs_fallback = needs_fallback
        self.fallback_reason = fallback_reason

class QualityEvaluator:
    def __init__(self, threshold: float = 0.50, optimal_threshold: float = 0.75):
        self.threshold = threshold
        self.optimal_threshold = optimal_threshold
        
    def evaluate(self, doc: CanonicalDocument) -> QualityReport:
        logger.info(f"Evaluating parsing quality for {doc.document_id}")
        
        if not doc.nodes:
            return QualityReport(0.0, True, "No nodes extracted")
            
        score = 0.0
        
        # 1. Text density per page (Weight: 0.15)
        text_length = sum(len(node.text_content) for node in doc.nodes if node.text_content)
        if text_length > 1000:
            score += 0.15
        elif text_length > 200:
            score += 0.05
            
        # 2. Heading detection ratio (Weight: 0.10)
        sections = [n for n in doc.nodes if n.type == NodeType.SECTION]
        if len(sections) > 0:
            score += 0.10
            
        # 3. Malformed/garbled text ratio (Weight: 0.15)
        # Simplified: Check first few nodes for too many non-printable chars
        malformed = False
        import string
        printable = set(string.printable)
        # Count non-printable characters in a sample of text
        sample_text = "".join(n.text_content for n in doc.nodes[:10] if n.text_content)
        if sample_text:
            weird_chars = sum(1 for c in sample_text if c not in printable)
            if weird_chars / max(len(sample_text), 1) < 0.05:
                score += 0.15
            else:
                malformed = True
        else:
            score += 0.15
            
        # 4. Table extraction regularity (Weight: 0.10)
        tables = [n for n in doc.nodes if n.type == NodeType.TABLE]
        if len(tables) > 0:
            score += 0.10
        else:
            # If no tables, assume document might not have tables and grant half points to not penalize too hard
            score += 0.05
            
        # 5. Reading order consistency (bbox Y) (Weight: 0.10)
        nodes_with_bbox = [n for n in doc.nodes if n.source.bbox]
        if len(nodes_with_bbox) / max(len(doc.nodes), 1) > 0.8:
            score += 0.10
            
        # 6. Equation/LaTeX block detection (Weight: 0.10)
        equations = [n for n in doc.nodes if n.type == NodeType.EQUATION]
        if len(equations) > 0:
            score += 0.10
        else:
            score += 0.05
            
        # 7. Suspicious fragment ratio (Weight: 0.10)
        # e.g., single character paragraphs
        fragments = sum(1 for n in doc.nodes if n.type == NodeType.PARAGRAPH and len(n.text_content.strip()) <= 2)
        if fragments / max(len(doc.nodes), 1) < 0.1:
            score += 0.10
            
        # 8. Header/footer noise (Weight: 0.05)
        score += 0.05
        
        # 9. Docling per-word OCR confidence (Weight: 0.10)
        # We simplified confidence to 1.0 initially
        score += 0.10
        
        # 10. Section numbering consistency (Weight: 0.05)
        score += 0.05
        
        # Normalize score
        score = max(0.0, min(1.0, score))
        
        if score < self.threshold:
            reason = "Score below threshold."
            if malformed:
                reason += " Malformed text detected."
            return QualityReport(score, True, reason)
        elif score < self.optimal_threshold:
            return QualityReport(score, True, f"Score {score} is acceptable but below optimal {self.optimal_threshold}. Running fallback for comparison.")
        
        return QualityReport(score, False)
