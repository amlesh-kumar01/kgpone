import logging
import warnings

warnings.filterwarnings("ignore", message="The `resume_download` argument is deprecated")
from typing import Dict, Any, List
from src.services.ingestion.extraction.base import BaseEntityExtractor
from src.infrastructure.model_factory import NLPModelFactory

logger = logging.getLogger("gliner_extractor")

class GLiNERExtractor(BaseEntityExtractor):
    def __init__(self, labels: List[str] = None):
        self.labels = labels or [
            "Concept", "Algorithm", "Dataset", "Metric", 
            "Author", "Tool", "Task", "Methodology"
        ]
        
    async def extract(self, chunks: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extracts entities from text chunks using GLiNER deterministically.
        """
        try:
            model = NLPModelFactory.get_gliner()
        except Exception as e:
            logger.error(f"Failed to load GLiNER: {e}")
            return {"entities": []}

        extracted_entities = []
        
        # We can process in batches or individually.
        for chunk in chunks:
            # GLiNER predict_entities
            try:
                entities = model.predict_entities(chunk, self.labels)
                for ent in entities:
                    extracted_entities.append({
                        "text": ent["text"],
                        "label": ent["label"],
                        "score": ent.get("score", 1.0)
                    })
            except Exception as e:
                logger.error(f"Error during GLiNER extraction on chunk: {e}")
                
        # Deduplicate naive implementation (EntityResolver will handle proper resolution)
        seen = set()
        unique_entities = []
        for ent in extracted_entities:
            key = (ent["text"].lower(), ent["label"])
            if key not in seen:
                seen.add(key)
                unique_entities.append(ent)
                
        return {"entities": unique_entities}
