import logging
import warnings

warnings.filterwarnings("ignore", message="The `resume_download` argument is deprecated")
from typing import Dict, Any, List, Union
from src.services.ingestion.canonical.ast_schema import ASTNode
from src.services.ingestion.extraction.base import BaseEntityExtractor
from src.infrastructure.model_factory import NLPModelFactory

logger = logging.getLogger("gliner_extractor")

class GLiNERExtractor(BaseEntityExtractor):
    def __init__(self, labels: List[str] = None):
        self.labels = labels or [
            "Concept", "Algorithm", "Dataset", "Metric", 
            "Author", "Tool", "Task", "Methodology"
        ]
        
    async def extract(self, nodes_or_chunks: Union[List[str], List[ASTNode]], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts entities from text chunks or AST nodes using GLiNER deterministically.
        """
        try:
            model = NLPModelFactory.get_gliner()
        except Exception as e:
            logger.error(f"Failed to load GLiNER: {e}")
            return {"entities": []}

        extracted_entities = []
        
        for item in nodes_or_chunks:
            is_node = isinstance(item, ASTNode)
            text = item.text_content if is_node else item
            
            if not text or not text.strip():
                continue
                
            try:
                entities = model.predict_entities(text, self.labels)
                for ent in entities:
                    extracted_entities.append({
                        "text": ent["text"],
                        "label": ent["label"],
                        "score": ent.get("score", 1.0),
                        "source_node_id": item.id if is_node else None,
                        "source_page": item.source.page_start if is_node and item.source else None
                    })
            except Exception as e:
                logger.error(f"Error during GLiNER extraction on item: {e}")
                
        # Deduplicate naive implementation (EntityResolver will handle proper resolution)
        seen = set()
        unique_entities = []
        for ent in extracted_entities:
            key = (ent["text"].lower(), ent["label"])
            if key not in seen:
                seen.add(key)
                unique_entities.append(ent)
                
        return {"entities": unique_entities}
