import logging
from src.services.ingestion.canonical.ast_schema import CanonicalDocument, NodeType

logger = logging.getLogger("confidence_scorer")

class ConfidenceScorer:
    """
    Assigns a confidence score (0.0 to 1.0) to each ASTNode based on various signals.
    """
    def score(self, doc: CanonicalDocument) -> CanonicalDocument:
        for node in doc.nodes:
            self._score_node(node)
        return doc
        
    def _score_node(self, node):
        confidence = 1.0
        
        # Signal: LlamaParse fallback usually doesn't have bounding boxes (we get them from pypdf loosely, but if missing it's a guess)
        if not node.source.bbox:
            confidence = min(confidence, 0.6)
            
        # Signal: Equation but no LaTeX was successfully extracted
        if node.type in [NodeType.EQUATION, NodeType.FORMULA] and not getattr(node, "latex", None):
            confidence = min(confidence, 0.2)
            
        # Signal: Very short paragraph, might be noise or header/footer fragment
        if node.type == NodeType.PARAGRAPH:
            text = node.text_content.strip()
            if len(text) < 10:
                confidence = min(confidence, 0.4)
            if len(text) == 0:
                confidence = min(confidence, 0.1)
                
        # Signal: High non-printable character ratio (garbled text from bad OCR)
        import string
        printable = set(string.printable)
        text = node.text_content or ""
        if text:
            unprintable_ratio = sum(1 for c in text if c not in printable) / len(text)
            if unprintable_ratio > 0.2:
                confidence = min(confidence, 0.1)
            elif unprintable_ratio > 0.05:
                confidence = min(confidence, 0.5)

        node.source.confidence = confidence
        
        for child in node.children:
            self._score_node(child)
