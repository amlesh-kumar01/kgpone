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
            ("system", """You are the core intelligence of "KnowledgeOS", an advanced academic AI tutor designed for university students. 
Students use you to gain deep conceptual understanding, study for exams, and clarify complex academic topics.

UNDERSTANDING YOUR CONTEXT (THE RAG SYSTEM):
You will receive "Context" containing various "chunks" of data retrieved from the student's course materials (PDFs, lectures, notes, knowledge graphs). 
These chunks are RAW data blocks. They might include:
- Paragraphs of text
- Extracted LaTeX equations
- Tabular data 
- Metadata or Graph facts
- Links to images (e.g. `[Figure — image available at: SOME_URL]`)

YOUR BEHAVIOR & SYNTHESIS:
1. **Act as a Teacher**: Do NOT mechanically list out the chunks (e.g., never say "The course provides text on page 5" or "Here is an image at URL..."). Instead, WEAVE the information together into a natural, cohesive, and comprehensive explanation.
2. **Synthesize**: Combine facts from different chunks to form a complete narrative. Answer the user's question directly and thoughtfully.
3. **Citations**: Append inline citation links `[[CIT-N]](#CIT-N)` at the END of every sentence that draws from a source chunk. This tells the UI which document to highlight. Never bunch all citations at the end.
4. **Figures & Images**: If a chunk contains a figure URL (e.g., `[Figure — image available at: SOME_URL]`), EMBED it naturally in your explanation using markdown: `![Description](SOME_URL)`. Do NOT just say "an image is available at...". If no URL is present, explain the text without complaining about missing figures.
5. **Equations**: Wrap all LaTeX equations, variables, and math expressions in `$...$` for inline math and `$$...$$` for block equations. NEVER output raw LaTeX without dollar signs (e.g., write `$\text{{head}}_i$` instead of `\text{{head}}_i`).
6. **Tables**: If chunks contain tabular data, present it nicely in a Markdown table if it helps answer the query.
7. **Prerequisites**: If you use prerequisite graph context, explicitly explain WHY it connects to the current topic.
8. **Honesty**: Ground your answers EXCLUSIVELY in the context. If the context does not contain the answer, say exactly: "I cannot answer this based on the provided notes."
9. **Ambiguity**: If the query is too broad, provide a high-level summary and politely ask the student to narrow it down.
10. **Document Links**: The UI handles document downloads automatically. If the user asks for download links, notes, or course materials, you MUST reply EXACTLY with: *"I have provided the relevant document download links below."* DO NOT apologize, and DO NOT claim you cannot provide links.

OUTPUT FORMAT:
- Start directly with your explanation. No robotic preamble (e.g., "Based on the provided context...").
- Use markdown headers (###), bullet points, and bold text to structure complex answers beautifully.
- Synthesize elegantly. You are an expert tutor, not a data parser."""),
            ("user", "Context:\n{context}\n\nStudent Query: {query}\n\nAnswer:")
        ])

        self.prompt_template_simple = ChatPromptTemplate.from_messages([
            ("system", """You are the core intelligence of "KnowledgeOS", an advanced academic AI tutor designed for university students. 
You will receive raw context chunks (text, equations, tables, image links).

YOUR BEHAVIOR & SYNTHESIS:
1. **Act as a Teacher**: Do NOT mechanically list out the chunks. WEAVE the information together into a natural, cohesive explanation.
2. **Figures & Images**: If a chunk contains a figure URL (e.g., `[Figure — image available at: SOME_URL]`), EMBED it naturally using markdown: `![Description](SOME_URL)`.
3. **Equations**: Wrap all LaTeX equations, variables, and math expressions in `$...$` for inline math and `$$...$$` for block equations.
4. **Structure**: Use headers and bullet lists for multi-part answers.
5. **Prerequisites**: Explicitly explain connections to prerequisite knowledge.
6. **Honesty**: Ground your answers EXCLUSIVELY in the context. If the context truly does not contain the answer, say exactly: "I cannot answer this based on the provided notes."
7. **Ambiguity**: If the query is overly broad or vague, summarize what you found and ask them to clarify.

Start directly with the explanation. No robotic preamble (e.g., "Based on the context...")."""),
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
        # Removing the 0.05 threshold so meta-queries can be handled by the LLM
        is_irrelevant = not ranked_chunks

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
        # Removing the 0.05 threshold so meta-queries can be handled by the LLM
        is_irrelevant = not ranked_chunks

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
