import logging
from typing import Any
from src.infrastructure.llm_factory import LLMFactory
from src.services.rag.base import BaseAnswerGenerator
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger("answer_service")

class AnswerService(BaseAnswerGenerator):
    def __init__(self, model_name: str | None = None):
        self.factory = LLMFactory()
        try:
            self.llm = self.factory.get_llm(model_name)
        except Exception as e:
            logger.error(f"Failed to configure LLM in AnswerService: {e}. Enabling fallback.")
            self.llm = None

        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an elite academic tutor. Answer the student's question grounded strictly on the study materials provided below.
Follow these critical guidelines:
1. Answer detailedly and accurately based ONLY on the context blocks.
2. If you use information from a block, append the citation tag (e.g. [CIT-1] or [CIT-2]) at the end of the sentence.
3. IMPORTANT: If the context contains prerequisite material from previous years/courses, clearly explain this connection. Point out that the student is missing this foundational knowledge and reference the specific prerequisite course/concept (e.g. 'I found this concept in your Discrete Math lecture notes').
4. Format formulas in LaTeX style (e.g. $$ for block math, $ for inline math)."""),
            ("user", "Context Study Materials:\n{context}\n\nStudent Query: {query}\n\nAcademic Answer:")
        ])

    def generate_answer(self, query: str, ranked_chunks: list[dict[str, Any]], citations: list[dict[str, Any]]) -> str:
        """
        Generates a grounded academic response. Highlight prerequisite sources.
        """
        if not ranked_chunks:
            return "I couldn't find any relevant study materials in your workspace matching your query. Please upload notes or lecture materials first."

        # Compile context text
        context_blocks = []
        for idx, chunk in enumerate(ranked_chunks):
            payload = chunk["payload"]
            cit_id = f"CIT-{idx + 1}"
            course_code = payload.get("course_code", "")
            is_prereq = payload.get("is_prerequisite", False)
            prereq_str = " (Prerequisite Course Content)" if is_prereq else " (Active Course Content)"
            
            context_blocks.append(
                f"Source: [{cit_id}] (Course: {course_code}{prereq_str})\n"
                f"Content: {payload.get('text', '')}\n"
                f"---"
            )
        
        context_str = "\n\n".join(context_blocks)

        if not self.llm:
            return self._generate_offline_grounded_answer(query, ranked_chunks, citations)

        try:
            chain = self.prompt_template | self.llm
            # ainvoke isn't used here since route is synchronous internally,
            # but we can use invoke. Wait, the route calls it synchronously: answer = services["answer_generator"].generate_answer(...)
            response = chain.invoke({
                "context": context_str,
                "query": query
            })
            return response.content
        except Exception as e:
            logger.error(f"LLM API generation failed: {e}. Falling back to offline synthesis.")
            return self._generate_offline_grounded_answer(query, ranked_chunks, citations)

    def _generate_offline_grounded_answer(self, query: str, ranked_chunks: list[dict[str, Any]], citations: list[dict[str, Any]]) -> str:
        """
        Offline fallback matching algorithm. Synthesizes a grounded answer from the chunk payloads locally.
        """
        answer_parts = []
        
        # Check if there is prerequisite content
        prereq_citations = [c for c in citations if c.get("is_prerequisite")]
        active_citations = [c for c in citations if not c.get("is_prerequisite")]

        if prereq_citations:
            p_cit = prereq_citations[0]
            concept = p_cit.get("prerequisite_concept", "foundational concept")
            course = p_cit.get("course_code", "previous course")
            answer_parts.append(
                f"**[Curriculum Time Travel Alert]** I noticed your query requires a foundational concept **{concept}** "
                f"from your prerequisite course **{course}** (which you completed in a previous semester). "
                f"Here is what the records show:\n\n"
            )
            # Add snippet from prereq
            snippet = p_cit.get("text_snippet", "").replace("...", "")
            answer_parts.append(f"> *{snippet}* [{p_cit['citation_id']}]\n\n")

        # Active course context
        if active_citations:
            a_cit = active_citations[0]
            answer_parts.append(f"Regarding the main course query in **{a_cit['course_code']}**:\n\n")
            for c in active_citations[:2]:
                snippet = c.get("text_snippet", "").replace("...", "")
                answer_parts.append(f"- **From {c['source_title']} (Section: {c['section']}):** {snippet} [{c['citation_id']}]\n")
        else:
            answer_parts.append("No active course notes match the details, but you can learn more using the prerequisite references.")

        answer_parts.append("\n*(Note: Grounded local synthesis mode - Offline fallback active)*")
        return "".join(answer_parts)
