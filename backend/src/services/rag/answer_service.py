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
            ("system", """You are an expert academic tutor for university students. Your answers are grounded EXCLUSIVELY in the provided course context — never fabricate information.

CORE RULES:
1. **Citations**: Append inline citation links [[CIT-N]](#CIT-N) at the END of every sentence that draws from a source block. Never bunch all citations at the end.
2. **Figures & Images**: When a context block mentions a figure and includes a line `[Figure — image available at: SOME_URL]` with an actual URL value, you MUST embed that image in your response using markdown: `![Figure](SOME_URL)`. Replace SOME_URL with the actual URL value from the context. If no URL is present, simply describe the figure.
3. **Equations**: Render LaTeX inline using `$...$` for inline math and `$$...$$` for block equations. Preserve all equation labels.
4. **Tables**: Present table data in clean Markdown table format when the context contains tabular rows.
5. **Code**: Only use code blocks if the context explicitly contains code. Never write code from scratch.
6. **Structure**: For multi-part questions, use headers (###) and bullet lists to organize the answer. Be concise and precise.
7. **Prerequisite Content**: If using prerequisite material, explicitly explain WHY it connects to the current query.
8. **Honesty**: If the context truly does not contain the answer, say exactly: "I cannot answer this based on the provided notes." Do NOT hallucinate.

OUTPUT FORMAT:
- Start directly with the answer. No preamble like "Based on the provided context...".
- Use markdown formatting throughout.
- End with a brief summary line if the answer is long."""),
            ("user", "Context:\n{context}\n\nStudent Query: {query}\n\nAnswer:")
        ])

        self.prompt_template_simple = ChatPromptTemplate.from_messages([
            ("system", """You are an expert academic tutor for university students. Your answers are grounded EXCLUSIVELY in the provided course context — never fabricate information.

CORE RULES:
1. **Figures & Images**: When a context block mentions a figure and includes a line `[Figure — image available at: SOME_URL]` with an actual URL value, you MUST embed that image in your response using markdown: `![Figure](SOME_URL)`. Replace SOME_URL with the actual URL value from the context. If no URL is present, simply describe the figure.
2. **Equations**: Render LaTeX equations properly.
3. **Structure**: Use headers and bullet lists for multi-part answers.
4. **Prerequisite Content**: Explicitly explain connections to prerequisite knowledge.
5. **Honesty**: If the context truly does not contain the answer, say exactly: "I cannot answer this based on the provided notes."

Start directly with the answer. No preamble."""),
            ("user", "Context:\n{context}\n\nStudent Query: {query}\n\nAnswer:")
        ])

        self.web_search_template = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful AI assistant. Answer the user's query using the provided web search results.
Synthesize the information fluently, use markdown formatting, and cite sources inline.
If the results do not contain the answer, say: "I couldn't find a good answer in the web search results."
Do not generate code unless explicitly requested."""),
            ("user", "{context}\n\nQuery: {query}\nAnswer:")
        ])

    def _build_context_string(self, ranked_chunks: list[dict[str, Any]], use_citations: bool) -> str:
        context_blocks = []
        for idx, chunk in enumerate(ranked_chunks):
            payload = chunk["payload"]
            cit_id = f"CIT-{idx + 1}"
            course_code = payload.get("course_code", "Unknown Course")
            is_prereq = payload.get("is_prereq", False)
            prereq_str = " (Prerequisite Course Content)" if is_prereq else " (Active Course Content)"
            chunk_type = payload.get("chunk_type", "text")
            page_info = f", Page {payload.get('page_number')}" if payload.get('page_number') else ""

            # Use the richly-formatted text built by the retrieval service (includes equation labels,
            # figure S3 keys, and table headers). Fall back to raw content if not present.
            rich_content = payload.get("formatted_text") or payload.get("content") or payload.get("text", "")

            # For figure chunks: if we have a presigned image_url (injected by the route handler)
            # inject it directly into the context so the LLM can embed it.
            if chunk_type == "figure":
                image_url = payload.get("image_url")  # presigned URL injected by query_routes
                image_s3_key = payload.get("image_s3_key", "")
                if image_url:
                    rich_content = f"{rich_content}\n[Figure — image available at: {image_url}]"
                elif image_s3_key:
                    rich_content = f"{rich_content}\n[Figure — image S3 key: {image_s3_key}]"

            if use_citations:
                context_blocks.append(
                    f"Source: [{cit_id}] (Course: {course_code}{prereq_str}{page_info}, Type: {chunk_type})\n"
                    f"Content:\n{rich_content}\n---"
                )
            else:
                context_blocks.append(
                    f"Course: {course_code}{prereq_str}{page_info}\n"
                    f"Content:\n{rich_content}\n---"
                )

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
