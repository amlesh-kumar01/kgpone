import logging
from typing import List, Dict, Any, Optional
from src.infrastructure.llm_factory import LLMFactory
from src.services.rag.base import BaseQueryPlanner
from src.schemas.query_schema import QueryPlan
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger("planner_service")

class PlannerService(BaseQueryPlanner):
    def __init__(self, model_name: str | None = None):
        self.factory = LLMFactory()
        try:
            llm = self.factory.get_llm(model_name)
            self.structured_llm = llm.with_structured_output(QueryPlan)
        except Exception as e:
            logger.error(f"Failed to initialize Planner LLM: {e}")
            self.structured_llm = None
            
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are the Query Planner for a University Knowledge Graph and RAG system.
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
Do not include any other text, just the structured output."""),
            ("user", "Query: '{query}'\nContext Course Code: {course}")
        ])

    async def detect_intent(self, query: str, context_course: Optional[str] = None, context_offering: Optional[str] = None) -> QueryPlan:
        """
        Classifies query into routing categories.
        """
        if not self.structured_llm:
            return self._heuristic_fallback(query, context_course, context_offering)
            
        try:
            chain = self.prompt_template | self.structured_llm
            plan: QueryPlan = await chain.ainvoke({
                "query": query,
                "course": context_course or 'None provided'
            })
            
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
                
            if not getattr(plan, "course_code", None) and context_course:
                plan.course_code = context_course
            if not getattr(plan, "course_offering_id", None) and context_offering:
                plan.course_offering_id = context_offering
                
            return plan

        except Exception as e:
            logger.error(f"LLM planner failed, falling back to heuristics: {e}")
            return self._heuristic_fallback(query, context_course, context_offering)

    def _heuristic_fallback(self, query: str, context_course: Optional[str], context_offering: Optional[str] = None) -> QueryPlan:
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
            course_offering_id=context_offering,
            entities_mentioned=[],
            backends_needed=backends
        )
