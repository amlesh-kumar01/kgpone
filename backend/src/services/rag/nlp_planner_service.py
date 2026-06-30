"""
NLP-based Query Planner — replaces LLM-based intent classification with a
lightweight TF-IDF + SVM classifier and regex/heuristic entity extraction.

Latency: < 10ms per query (vs 1-3s with LLM).
Cost: Zero API calls.
"""

import logging
import os
import re
from typing import List, Optional

import joblib

from src.schemas.query_schema import QueryPlan
from src.services.rag.base import BaseQueryPlanner

logger = logging.getLogger("nlp_planner_service")

# Resolved model paths (relative to backend/ root)
_MODELS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "models",
)
_DEFAULT_CLASSIFIER_PATH = os.path.join(_MODELS_DIR, "intent_classifier.pkl")
_DEFAULT_VECTORIZER_PATH = os.path.join(_MODELS_DIR, "tfidf_vectorizer.pkl")

# Minimum confidence threshold — below this we fall back to semantic_search
_MIN_CONFIDENCE = 0.60


class NLPPlannerService(BaseQueryPlanner):
    """
    Sub-millisecond intent classification and entity extraction
    using TF-IDF + SVM and regex heuristics.
    """

    def __init__(
        self,
        classifier_path: str = _DEFAULT_CLASSIFIER_PATH,
        vectorizer_path: str = _DEFAULT_VECTORIZER_PATH,
    ):
        self.classifier = None
        self.vectorizer = None

        try:
            self.classifier = joblib.load(classifier_path)
            self.vectorizer = joblib.load(vectorizer_path)
            logger.info("NLP Planner models loaded successfully.")
        except Exception as e:
            logger.warning(
                f"Failed to load NLP models ({e}). "
                "Falling back to heuristic-only routing."
            )

        # Pre-compiled regex for course code extraction (e.g. CS101, CS 60001, EE20005)
        self.course_pattern = re.compile(r"\b[A-Za-z]{2,4}\s?\d{3,5}\b")

        # Common stop words to filter from entity extraction
        self._stop_words = frozenset({
            "what", "who", "how", "where", "when", "which", "why",
            "is", "are", "was", "were", "the", "a", "an", "in", "on",
            "for", "to", "of", "and", "or", "with", "this", "that",
            "do", "does", "can", "could", "should", "would", "will",
            "explain", "compare", "difference", "between", "tell",
            "me", "about", "give", "show", "list", "find", "search",
            "all", "any", "some", "my", "i", "need", "want", "please",
            "help", "understand", "it", "its", "from", "by", "at",
        })

    async def detect_intent(
        self,
        query: str,
        context_course: Optional[str] = None,
        context_offering: Optional[str] = None,
    ) -> QueryPlan:
        """
        Sub-millisecond intent classification and entity extraction.
        """
        clean_query = query.lower().strip()

        # Step 1: Classify intent
        predicted_intent, confidence = self._classify_intent(clean_query)

        # Step 2: Extract entities
        course_code = self._extract_course_code(query) or context_course
        entities = self._extract_entities(query)

        # Step 3: Deterministic backend routing
        backends = self._map_backends(predicted_intent)

        return QueryPlan(
            intent=predicted_intent,
            course_code=course_code,
            course_offering_id=context_offering,
            entities_mentioned=entities,
            backends_needed=backends,
            confidence_score=float(confidence),
        )

    def _classify_intent(self, query: str) -> tuple[str, float]:
        """
        Classifies intent using TF-IDF + SVM.
        Falls back to heuristics if models are unavailable.
        """
        if self.classifier is not None and self.vectorizer is not None:
            try:
                X = self.vectorizer.transform([query])
                probabilities = self.classifier.predict_proba(X)[0]
                max_idx = probabilities.argmax()
                predicted_intent = self.classifier.classes_[max_idx]
                confidence = probabilities[max_idx]

                # If confidence is too low, default to semantic_search
                if confidence < _MIN_CONFIDENCE:
                    logger.info(
                        f"Low confidence ({confidence:.2f}) for intent "
                        f"'{predicted_intent}', falling back to semantic_search."
                    )
                    return "semantic_search", confidence

                return predicted_intent, confidence
            except Exception as e:
                logger.warning(f"ML classification failed: {e}")

        # Heuristic fallback
        return self._heuristic_classify(query)

    def _heuristic_classify(self, query: str) -> tuple[str, float]:
        """Rule-based intent detection when ML model is unavailable."""
        q = query.lower()

        rules = [
            (["download", "get pdf", "give me the pdf", "download pdf"], "download"),
            (["who teaches", "professor", "faculty", "instructor", "ta "], "faculty_lookup"),
            (["list documents", "show all", "what documents", "available materials", "pyq", "uploaded"], "list_documents"),
            (["list courses", "what courses", "courses offered", "available courses"], "list_courses"),
            (["prerequisite", "need to know", "before taking", "required before", "foundation for"], "prerequisites"),
            (["difference", "compare", "vs ", "versus", "distinction"], "compare"),
            (["related", "connection", "relationship", "link between", "connected"], "relationship"),
            (["topics", "syllabus", "covers", "course content", "what is in", "chapter"], "concept_search"),
            (["explain", "what is", "how does", "describe"], "topic_explain"),
            (["notes on", "search for", "find", "where", "search"], "semantic_search"),
        ]

        for keywords, intent in rules:
            if any(kw in q for kw in keywords):
                return intent, 0.75  # Medium confidence for heuristic match

        return "general_qa", 0.50

    def _extract_course_code(self, query: str) -> Optional[str]:
        """Extracts standard course codes deterministically via regex."""
        match = self.course_pattern.search(query)
        if match:
            return match.group(0).replace(" ", "").upper()
        return None

    def _extract_entities(self, query: str) -> List[str]:
        """
        Lightweight entity extraction using noun-chunk heuristics.
        Extracts multi-word phrases that are likely academic concepts.
        """
        # Remove course codes from query before entity extraction
        cleaned = self.course_pattern.sub("", query)

        # Tokenize and filter
        words = cleaned.split()
        entities = []
        current_chunk = []

        for word in words:
            clean_word = re.sub(r"[^\w\s-]", "", word).strip()
            if not clean_word:
                if current_chunk:
                    entities.append(" ".join(current_chunk))
                    current_chunk = []
                continue

            if clean_word.lower() in self._stop_words:
                if current_chunk:
                    entities.append(" ".join(current_chunk))
                    current_chunk = []
            else:
                current_chunk.append(clean_word)

        if current_chunk:
            entities.append(" ".join(current_chunk))

        # Filter: keep phrases with at least 2 chars, skip single short words
        entities = [
            e.strip()
            for e in entities
            if len(e.strip()) >= 2 and e.strip().lower() not in self._stop_words
        ]

        return entities

    def _map_backends(self, intent: str) -> List[str]:
        """Deterministic routing from intent to data backends."""
        backend_map = {
            "download": ["postgresql"],
            "faculty_lookup": ["postgresql"],
            "list_documents": ["postgresql"],
            "list_courses": ["postgresql"],
            "prerequisites": ["neo4j"],
            "semantic_search": ["qdrant"],
            "topic_explain": ["neo4j", "qdrant"],
            "compare": ["neo4j", "qdrant"],
            "concept_search": ["neo4j", "qdrant"],
            "relationship": ["neo4j"],
            "general_qa": ["neo4j", "qdrant"],
        }
        return backend_map.get(intent, ["neo4j", "qdrant"])
