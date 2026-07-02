import logging
from typing import Any
import os

logger = logging.getLogger("model_factory")

class NLPModelFactory:
    """
    Factory for loading interchangeable NLP models (GLiNER, spaCy)
    Provides singleton instances to preserve VRAM limits.
    """
    _gliner_model = None
    _spacy_model = None

    @classmethod
    def get_gliner(cls) -> Any:
        if cls._gliner_model is None:
            model_name = os.environ.get("GLINER_MODEL_NAME", "urchade/gliner_medium-v2.1")
            logger.info(f"Loading GLiNER model: {model_name}")
            try:
                from gliner import GLiNER
                cls._gliner_model = GLiNER.from_pretrained(model_name)
            except ImportError:
                logger.error("gliner package not installed. Cannot load model.")
                raise
        return cls._gliner_model

    @classmethod
    def get_spacy(cls) -> Any:
        if cls._spacy_model is None:
            model_name = os.environ.get("SPACY_MODEL_NAME", "en_core_web_sm")
            logger.info(f"Loading spaCy model: {model_name}")
            try:
                import spacy
                if not spacy.util.is_package(model_name):
                    logger.info(f"Downloading spaCy model {model_name}...")
                    spacy.cli.download(model_name)
                cls._spacy_model = spacy.load(model_name)
            except ImportError:
                logger.error("spacy package not installed. Cannot load model.")
                raise
        return cls._spacy_model

    @classmethod
    def unload_gliner(cls):
        """Releases GLiNER model to free VRAM."""
        if cls._gliner_model is not None:
            import gc
            import torch
            del cls._gliner_model
            cls._gliner_model = None
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("Unloaded GLiNER model from memory.")
