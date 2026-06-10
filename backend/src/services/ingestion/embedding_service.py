import os
import hashlib
import numpy as np
import logging
from typing import List

logger = logging.getLogger("embedding_service")

class EmbeddingService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.use_fallback = False
        
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            logger.warning("GEMINI_API_KEY is missing or template value. Using local feature hashing for embeddings.")
            self.use_fallback = True
        else:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to configure google-generativeai client: {e}. Enabling fallback.")
                self.use_fallback = True

    def get_embedding(self, text: str) -> List[float]:
        """
        Generates a 768-dimensional embedding vector for the given text.
        """
        if self.use_fallback:
            return self._generate_fallback_embedding(text)

        try:
            import google.generativeai as genai
            response = genai.embed_content(
                model="models/text-embedding-004",
                contents=text,
                task_type="retrieval_document"
            )
            return response['embedding'][0] if isinstance(response['embedding'][0], list) else response['embedding']
        except Exception as e:
            logger.error(f"Gemini embedding API call failed: {e}. Using local feature hashing fallback.")
            # Fall back to local LSH/hashing embedding
            return self._generate_fallback_embedding(text)

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generates embeddings for a list of texts.
        """
        return [self.get_embedding(t) for t in texts]

    def _generate_fallback_embedding(self, text: str, dimension: int = 768) -> List[float]:
        """
        Feature hashing trick (LSH-style) to generate a deterministic unit-length vector.
        Splits the text into words/tokens, hashes them to indices, and builds a normalized bag-of-words.
        """
        vector = np.zeros(dimension, dtype=np.float32)
        
        # Clean text and split to words
        words = re_words = [w.lower() for w in text.split() if w.strip()]
        if not words:
            # Return a unit vector pointing to index 0 if empty
            vector[0] = 1.0
            return vector.tolist()

        for word in words:
            # Deterministic hash of word using SHA256
            h = hashlib.sha256(word.encode('utf-8')).hexdigest()
            val = int(h, 16)
            index = val % dimension
            # Use sign bit of hash to determine +1 or -1 weight (reduces collision bias)
            sign = 1 if (val >> 8) & 1 else -1
            vector[index] += sign

        # Normalize to unit length
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
            
        return vector.tolist()
