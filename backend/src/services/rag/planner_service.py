import logging
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from google import genai
from src.config.settings import Settings
from src.services.rag.base import BaseQueryPlanner
from src.schemas.query_schema import QueryPlan

logger = logging.getLogger("planner_service")

class PlannerService(BaseQueryPlanner):
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name
        self.client = genai.Client(api_key=Settings.GEMINI_API_KEY)

    async def detect_intent(self, query: str, context_course: Optional[str] = None) -> QueryPlan:
        """
        Classifies query into routing categories.
        """
        prompt = f"""
        You are the Query Planner for a University Knowledge Graph and RAG system.
        Categorize the following user query into one of these intents:
        - download: "Download lecture 5 PDF", "get the syllabus"
        - faculty_lookup: "Who teaches CS60001?", "professor's email"
        - list_documents: "Give all PYQs for CS101", "show my notes"
        - list_courses: "What courses does CSE offer?"
        - prerequisites: "What are the prerequisites of OS?", "do I need math for ML?"
        - topic_explain: "Explain Attention Mechanism", "what is a CNN?"
        - compare: "Compare CNN and ViT", "difference between DFS and BFS"
        - concept_search: "What topics does CS20006 cover?", "what is in chapter 2?"
        - semantic_search: "Notes on dynamic programming", "where did the professor mention arrays"
        - relationship: "How is DFS related to BFS?", "connection between A and B"
        - general_qa: "Explain backpropagation with formulas", "how to solve this?"
        
        Also extract any course codes or entities (topics, concepts) mentioned.
        
        Query: "{query}"
        Context Course Code: {context_course or 'None provided'}
        """

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=QueryPlan,
                    temperature=0.0
                )
            )
            
            result = json.loads(response.text)
            plan = QueryPlan(**result)
            
            # Map intents to backends
            intent = plan.intent
            if intent in ["download", "faculty_lookup", "list_documents", "list_courses"]:
                plan.backends_needed = ["postgresql"]
            elif intent in ["prerequisites", "concept_search"]:
                plan.backends_needed = ["neo4j"]
            elif intent in ["semantic_search"]:
                plan.backends_needed = ["qdrant"]
            else:
                plan.backends_needed = ["neo4j", "qdrant"]
                
            if not plan.course_code and context_course:
                plan.course_code = context_course
                
            return plan

        except Exception as e:
            logger.error(f"LLM planner failed, falling back to heuristics: {e}")
            return self._heuristic_fallback(query, context_course)

    def _heuristic_fallback(self, query: str, context_course: Optional[str]) -> QueryPlan:
        q = query.lower()
        intent = "general_qa"
        backends = ["neo4j", "qdrant"]
        
        if "download" in q or "get pdf" in q or "pyq" in q:
            intent = "list_documents"
            backends = ["postgresql"]
        elif "who teaches" in q or "professor" in q or "faculty" in q:
            intent = "faculty_lookup"
            backends = ["postgresql"]
        elif "prerequisite" in q or "need to know" in q:
            intent = "prerequisites"
            backends = ["neo4j"]
        elif "difference" in q or "compare" in q or "vs" in q:
            intent = "compare"
        elif "related" in q or "connection" in q:
            intent = "relationship"
            
        return QueryPlan(
            intent=intent,
            course_code=context_course,
            entities_mentioned=[],
            backends_needed=backends
        )
