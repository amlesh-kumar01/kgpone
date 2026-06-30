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
            ("system", """You're an academic tutor. Answer based ONLY on the provided context.
Guidelines:
1. Append citation links (e.g. [[CIT-1]](#CIT-1)) to sentences when using info from a block.
2. If using prerequisite material, explicitly explain the connection to the student's missing knowledge.
3. Only use markdown code blocks if the context contains code or the user explicitly asks for it. Do NOT generate arbitrary code from scratch.
4. Synthesize fluently; do not just copy raw placeholders.
5. If the context does not contain the answer, say "I cannot answer this based on the provided notes." """),
            ("user", "Context:\n{context}\n\nQuery: {query}\nAnswer:")
        ])

        self.prompt_template_simple = ChatPromptTemplate.from_messages([
            ("system", """You're an academic tutor. Answer based ONLY on the provided context.
Guidelines:
1. If using prerequisite material, explicitly explain the connection to the student's missing knowledge.
2. Only use markdown code blocks if the context contains code or the user explicitly asks for it. Do NOT generate arbitrary code from scratch.
3. Synthesize fluently; do not just copy raw placeholders.
4. If the context does not contain the answer, say "I cannot answer this based on the provided notes." """),
            ("user", "Context:\n{context}\n\nQuery: {query}\nAnswer:")
        ])

        self.web_search_template = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful AI assistant. Answer the user's query using the provided web search results.
Guidelines:
1. Synthesize the information from the web search results fluently.
2. Do not generate code unless explicitly requested.
3. If the web search results do not contain the answer, say "I couldn't find a good answer in the web search results." """),
            ("user", "{context}\n\nQuery: {query}\nAnswer:")
        ])

    def _build_context_string(self, ranked_chunks: list[dict[str, Any]], use_citations: bool) -> str:
        context_blocks = []
        for idx, chunk in enumerate(ranked_chunks):
            payload = chunk["payload"]
            cit_id = f"CIT-{idx + 1}"
            course_code = payload.get("course_code", "")
            is_prereq = payload.get("is_prerequisite", False)
            prereq_str = " (Prerequisite Course Content)" if is_prereq else " (Active Course Content)"
            
            if use_citations:
                context_blocks.append(f"Source: [{cit_id}] (Course: {course_code}{prereq_str})\nContent: {payload.get('content', payload.get('text', ''))}\n---")
            else:
                context_blocks.append(f"Course: {course_code}{prereq_str}\nContent: {payload.get('content', payload.get('text', ''))}\n---")
        
        return "\n\n".join(context_blocks)

    def generate_answer(self, query: str, ranked_chunks: list[dict[str, Any]], citations: list[dict[str, Any]], use_citations: bool = True) -> str:
        """
        Generates a grounded academic response. Highlight prerequisite sources.
        """
        top_score = ranked_chunks[0].get("final_score", ranked_chunks[0].get("score", 0.0)) if ranked_chunks else 0.0
        is_irrelevant = not ranked_chunks or top_score < 0.05

        if is_irrelevant:
            try:
                from ddgs import DDGS
                with DDGS() as ddgs:
                    results = [r for r in ddgs.text(query, max_results=3)]
                if not results:
                    return "I couldn't find any relevant study materials or web results for your query."
                context_str = "Web Search Results:\n\n"
                for i, r in enumerate(results):
                    context_str += f"[{i+1}] {r.get('title', '')}\n{r.get('body', '')}\n---"
            except Exception as e:
                logger.error(f"Web search fallback failed: {e}")
                return "I couldn't find any relevant study materials in your workspace matching your query. Please upload notes or lecture materials first."
        else:
            context_str = self._build_context_string(ranked_chunks, use_citations)

        if not self.llm:
            return self._generate_offline_grounded_answer(query, ranked_chunks, citations)

        try:
            if is_irrelevant:
                template = self.web_search_template
            else:
                template = self.prompt_template if use_citations else self.prompt_template_simple
                
            chain = template | self.llm
            response = chain.invoke({
                "context": context_str,
                "query": query
            })
            return response.content
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return self._generate_offline_grounded_answer(query, ranked_chunks, citations)

    async def generate_answer_stream(self, query: str, ranked_chunks: list[dict[str, Any]], use_citations: bool = True):
        """
        Generates a streaming academic response.
        """
        top_score = ranked_chunks[0].get("final_score", ranked_chunks[0].get("score", 0.0)) if ranked_chunks else 0.0
        is_irrelevant = not ranked_chunks or top_score < 0.05

        if is_irrelevant:
            yield "*No local course materials found. Searching the web...*\n\n"
            try:
                from ddgs import DDGS
                with DDGS() as ddgs:
                    results = [r for r in ddgs.text(query, max_results=4)]
                if not results:
                    yield "I couldn't find any relevant study materials or web results for your query."
                    return
                context_str = "Web Search Results:\n\n"
                for i, r in enumerate(results):
                    context_str += f"[{i+1}] {r.get('title', '')}\n{r.get('body', '')}\n---"
            except Exception as e:
                logger.error(f"Web search fallback failed: {e}")
                yield "I couldn't find any relevant study materials in your workspace matching your query. Please upload notes or lecture materials first."
                return
        else:
            context_str = self._build_context_string(ranked_chunks, use_citations)

        if not self.llm:
            yield self._generate_offline_grounded_answer(query, ranked_chunks, [])
            return

        try:
            if is_irrelevant:
                template = self.web_search_template
            else:
                template = self.prompt_template if use_citations else self.prompt_template_simple
                
            chain = template | self.llm
            async for chunk in chain.astream({
                "context": context_str,
                "query": query
            }):
                yield chunk.content
        except Exception as e:
            logger.error(f"LLM streaming failed: {e}")
            yield "\n\n*(Network/API Error. Falling back to offline generation)*\n\n"
            # Get citations if available
            citations = []
            if use_citations:
                try:
                    from src.services.rag.citation_service import CitationService
                    citations = CitationService().format_citations(ranked_chunks)
                except:
                    pass
            yield self._generate_offline_grounded_answer(query, ranked_chunks, citations)
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
            answer_parts.append(f"> *{snippet}* [[{p_cit['citation_id']}](#{p_cit['citation_id']})]\n\n")

        # Active course context
        if active_citations:
            a_cit = active_citations[0]
            answer_parts.append(f"Regarding the main course query in **{a_cit['course_code']}**:\n\n")
            for c in active_citations[:2]:
                snippet = c.get("text_snippet", "").replace("...", "")
                answer_parts.append(f"- **From {c['source_title']} (Section: {c['section']}):** {snippet} [[{c['citation_id']}](#{c['citation_id']})]\n")
        else:
            answer_parts.append("No active course notes match the details, but you can learn more using the prerequisite references.")

        answer_parts.append("\n*(Note: Grounded local synthesis mode - Offline fallback active)*")
        return "".join(answer_parts)
