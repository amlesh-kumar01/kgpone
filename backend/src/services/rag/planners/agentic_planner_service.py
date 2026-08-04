"""
agentic_planner_service.py — Tool-calling Agent Planner for KgpOne.

This planner uses a LangChain ReAct/Tool-Calling Agent to:
  1. Reason about the user's query.
  2. Autonomously call tools (semantic search, graph lookup, doc catalog, etc.)
  3. Synthesise the tool outputs into pre-fetched context chunks that the
     existing RetrievalService / AnswerService pipeline can consume.

This is the "Advanced Mode" pipeline. The fast NLPPlannerService is still
used for "Basic Mode".
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage

from src.schemas.query_schema import QueryPlan
from src.services.rag.tools.agent_tools import ALL_TOOLS
from src.services.rag.tools.internet_tools import internet_search
from src.services.rag.planners.nlp_planner_service import NLPPlannerService

AGENT_TOOLS_WITH_INTERNET = ALL_TOOLS + [internet_search]

logger = logging.getLogger("agentic_planner")

# System prompt that guides the agent's reasoning strategy
_SYSTEM_PROMPT = """\
You are KgpOne's Advanced Academic Research Agent. Your job is to analyse the
student's query and call the appropriate tools to gather all relevant information.

## Your Strategy
1. READ the query carefully and identify the primary intent.
2. PLAN which tools to call. You can call multiple tools if needed.
3. CALL the tools. Always start with the most targeted tool:
   - For conceptual questions → use `vector_semantic_search`
   - For relationship / prerequisite questions → use `graph_entity_lookup` AND `get_course_prerequisites`
   - For "list documents" / "what materials" → use `list_course_documents`
   - For "find document" / named document search → use `search_document_catalog`
   - For "download" / "get the PDF" → first `search_document_catalog`, then `get_document_download_url`
   - For "who teaches" / "professor" / "office hours" → use `get_faculty_info`
   - For full document details → use `get_document_metadata`
   - For "solve a problem" / mathematical or logic problems → use `vector_semantic_search` for theorems/formulas, AND `graph_entity_lookup` for conceptual relationships, iteratively combining them before answering.
   - For "summarize" / broad overarching topics → use `list_course_documents` to find relevant materials, then iteratively call `vector_semantic_search` or `get_document_metadata` across multiple sources to comprehensively synthesize the information.
   - **For "generate interview questions", "exam prep", or "extract from the whole document"** → DO NOT use `vector_semantic_search`. Instead, use `search_document_catalog` to find the exact document ID.
   - For general world knowledge, coding help, greetings, or off-topic questions → use the `internet_search` tool if you need external knowledge.
4. SET STRATEGY:
   - If the user wants comprehensive extraction across an entire document (e.g., generating exam questions from everywhere), set `execution_strategy` to `map_reduce` and populate `target_document_ids` with the found document IDs.
   - For specific factual lookups or multi-hop agent research, use `standard`.
5. SYNTHESISE the results. After the tools return, summarise the key findings
   in a concise JSON response so the answer generator can use them.

## Output Format
After calling all necessary tools, respond with a JSON object:
{
  "intent": "<detected_intent>",
  "entities": ["<entity1>", "<entity2>"],
  "execution_strategy": "<'standard' or 'map_reduce'>",
  "target_document_ids": ["<doc_id_if_map_reduce>"],
  "tool_results_summary": "<brief summary of what you found>",
  "direct_answer": "<if the tools returned a definitive answer (e.g. a download URL), provide it here; otherwise leave empty>"
}
"""


class AgenticPlannerService:
    """
    Implements BaseQueryPlanner using a LangChain tool-calling agent.
    Returns a standard QueryPlan enriched with pre-fetched context injected
    as `_agent_chunks` (a custom field for the route handler to use).
    """

    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        # Bind all tools to the LLM for tool-calling
        self.llm_with_tools = llm.bind_tools(AGENT_TOOLS_WITH_INTERNET)
        # Build a quick lookup for tool execution
        self._tool_map = {t.name: t for t in AGENT_TOOLS_WITH_INTERNET}

    async def detect_intent(
        self,
        query: str,
        context_course: Optional[str] = None,
        context_offering: Optional[str] = None,
    ) -> QueryPlan:
        """
        Runs the tool-calling agent loop and returns a QueryPlan.
        The plan carries an extra `_agent_context` attribute with all tool results.
        """
        # --- Fast Pre-classification for General QA Bypass ---
        nlp_planner = NLPPlannerService()
        fast_plan = await nlp_planner.detect_intent(query, context_course, context_offering)
        if fast_plan.intent == "general_qa":
            logger.info("[AgenticPlanner] Fast pre-classification detected general_qa. Bypassing heavy agent loop.")
            return fast_plan

        user_content = query
        if context_course:
            user_content = f"[Course context: {context_course}]\n\n{query}"

        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ]

        agent_chunks: list[dict[str, Any]] = []
        direct_answer: str = ""
        intent = "advanced_agent"
        entities: list[str] = []
        execution_strategy = "standard"
        target_document_ids: list[str] = []

        try:
            # --- Agentic loop (max 5 iterations to prevent runaway) ---
            for iteration in range(5):
                ai_msg: AIMessage = await self.llm_with_tools.ainvoke(messages)
                messages.append(ai_msg)

                tool_calls = getattr(ai_msg, "tool_calls", None) or []

                if not tool_calls:
                    # No more tools — parse final JSON summary
                    raw = ai_msg.content
                    if isinstance(raw, list):
                        raw = "".join(
                            p.get("text", "") if isinstance(p, dict) else str(p)
                            for p in raw
                        )
                    try:
                        # Extract JSON from markdown code fences if present
                        if "```" in raw:
                            raw = raw.split("```")[1]
                            if raw.startswith("json"):
                                raw = raw[4:]
                        summary = json.loads(raw.strip())
                        intent = summary.get("intent", "advanced_agent")
                        entities = summary.get("entities", [])
                        execution_strategy = summary.get("execution_strategy", "standard")
                        target_document_ids = summary.get("target_document_ids", [])
                        direct_answer = summary.get("direct_answer", "")
                    except Exception:
                        # If parsing fails, treat raw text as summary
                        direct_answer = raw
                        execution_strategy = "standard"
                        target_document_ids = []
                    break

                # Execute each tool call concurrently
                tool_results = await asyncio.gather(
                    *[self._call_tool(tc) for tc in tool_calls],
                    return_exceptions=True,
                )

                for tc, result in zip(tool_calls, tool_results):
                    tool_name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", "unknown")
                    tool_id = tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", "tool_call_0")

                    if isinstance(result, Exception):
                        logger.warning(f"Tool '{tool_name}' failed: {result}")
                        result_str = json.dumps({"error": str(result)})
                    else:
                        result_str = json.dumps(result, default=str)
                        # Collect vector search results as agent_chunks for the generator
                        if tool_name == "vector_semantic_search" and isinstance(result, list):
                            for item in result:
                                agent_chunks.append({
                                    "id": f"agent_{tool_name}_{item.get('document_id', 'x')}",
                                    "score": item.get("score", 0.7),
                                    "payload": {
                                        "text": item.get("text_snippet", ""),
                                        "formatted_text": item.get("text_snippet", ""),
                                        "document_id": item.get("document_id"),
                                        "document_title": item.get("document_title"),
                                        "course_code": item.get("course_code"),
                                        "document_type": item.get("doc_type"),
                                        "page_number": item.get("page"),
                                    },
                                })

                    logger.info(f"[Agent] Tool '{tool_name}' completed")
                    messages.append(
                        ToolMessage(content=result_str, tool_call_id=tool_id)
                    )

            # If direct_answer exists, wrap it as a synthetic chunk for the generator
            if direct_answer:
                agent_chunks.insert(0, {
                    "id": "agent_direct_answer",
                    "score": 1.0,
                    "payload": {
                        "text": direct_answer,
                        "formatted_text": direct_answer,
                        "document_id": "AGENT",
                    },
                })

        except Exception as e:
            logger.error(f"Agentic planner failed: {e}", exc_info=True)
            # Fall back to a safe generic plan so the basic pipeline can still respond
            return QueryPlan(
                intent="semantic_search",
                course_code=context_course,
                course_offering_id=context_offering,
                entities_mentioned=[],
                backends_needed=["qdrant", "neo4j"],
                confidence_score=0.5,
            )

        # Build the QueryPlan; attach agent_chunks as a private attribute
        plan = QueryPlan(
            intent=intent,
            course_code=context_course,
            course_offering_id=context_offering,
            entities_mentioned=entities,
            backends_needed=["qdrant", "neo4j"],
            confidence_score=0.95,
            execution_strategy=execution_strategy,
            target_document_ids=target_document_ids,
        )
        # Attach extra context for the route handler to inject into the generator
        object.__setattr__(plan, "_agent_chunks", agent_chunks)
        return plan

    async def _call_tool(self, tool_call: Any) -> Any:
        """Execute a single tool call from the agent."""
        if isinstance(tool_call, dict):
            name = tool_call.get("name")
            args = tool_call.get("args", {})
        else:
            name = getattr(tool_call, "name", None)
            args = getattr(tool_call, "args", {})

        tool_fn = self._tool_map.get(name)
        if tool_fn is None:
            return {"error": f"Unknown tool: {name}"}

        # All tools are async — invoke directly
        return await tool_fn.ainvoke(args)
