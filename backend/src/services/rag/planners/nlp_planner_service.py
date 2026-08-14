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


_CLASSIFIER = None
_VECTORIZER = None
_MODELS_LOADED = False
_MODELS_LOAD_ATTEMPTED = False

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
        global _CLASSIFIER, _VECTORIZER, _MODELS_LOADED, _MODELS_LOAD_ATTEMPTED
        self.classifier = None
        self.vectorizer = None

        if not _MODELS_LOAD_ATTEMPTED:
            _MODELS_LOAD_ATTEMPTED = True
            if os.path.exists(classifier_path) and os.path.exists(vectorizer_path):
                try:
                    _CLASSIFIER = joblib.load(classifier_path)
                    _VECTORIZER = joblib.load(vectorizer_path)
                    _MODELS_LOADED = True
                    logger.info("NLP Planner models loaded successfully.")
                except Exception as e:
                    logger.warning(f"Failed to load NLP models ({e}). Falling back to heuristic-only routing.")
            else:
                logger.warning(f"NLP model files not found at {classifier_path}. Falling back to heuristic-only routing. This warning will only be shown once.")
        
        self.classifier = _CLASSIFIER
        self.vectorizer = _VECTORIZER

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

        # ── Pre-check overrides (highest priority, beats ML classifier) ──
        # Figure/image queries must always go to Qdrant regardless of what
        # the ML classifier predicts (e.g. "list all figures" → list_documents).
        _FIGURE_KEYWORDS = {
            "figure", "figures", "diagram", "diagrams", "image", "images",
            "chart", "charts", "plot", "plots", "illustration", "illustrations",
            "picture", "pictures", "visual", "visuals", "graph", "graphs",
        }
        query_words = set(re.findall(r"\b\w+\b", clean_query))
        if query_words & _FIGURE_KEYWORDS:
            predicted_intent = "figure_search"
            confidence = 0.97
        else:
            # Step 1: Classify intent via ML or heuristics
            predicted_intent, confidence = self._classify_intent(clean_query)

        # Step 2: Extract entities
        study_unit_code = self._extract_study_unit_code(query) or context_course
        entities = self._extract_entities(query)

        # Step 3: Deterministic backend routing
        backends = self._map_backends(predicted_intent)

        return QueryPlan(
            intent=predicted_intent,
            study_unit_code=study_unit_code,
            study_unit_id=context_offering,
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
            (["image of", "show me the image", "give me the image", "give me figure", "show figure", "get figure", "figure 1", "figure 2", "figure 3", "figure 4", "figure 5", "figure 6", "figure 7", "figure 8", "figure 9", "diagram", "plot", "chart", "illustration", "picture", "visual"], "figure_search"),
            (["table", "from the table", "data row", "column"], "table_search"),
            (["chapter", "section", "heading", "under the topic"], "structural_search"),
            (["topics", "syllabus", "covers", "course content", "what is in"], "concept_search"),
            (["explain", "what is", "how does", "describe"], "topic_explain"),
            (["notes on", "search for", "find", "where", "search"], "semantic_search"),
        ]

        for keywords, intent in rules:
            if any(kw in q for kw in keywords):
                return intent, 0.75  # Medium confidence for heuristic match

        return "general_qa", 0.50

    def _extract_study_unit_code(self, query: str) -> Optional[str]:
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
            "figure_search": ["qdrant"],
            "table_search": ["neo4j", "qdrant"],
            "structural_search": ["neo4j", "qdrant"],
            "topic_explain": ["neo4j", "qdrant"],
            "compare": ["neo4j", "qdrant"],
            "concept_search": ["neo4j", "qdrant"],
            "relationship": ["neo4j"],
            "general_qa": [],
        }
        return backend_map.get(intent, ["neo4j", "qdrant"])
