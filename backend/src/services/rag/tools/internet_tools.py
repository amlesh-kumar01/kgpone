from langchain_core.tools import tool
import logging

logger = logging.getLogger("internet_tools")

@tool
def internet_search(query: str) -> str:
    """
    Search the public internet for general knowledge, recent events, or information 
    not found in the student's local university course materials.
    Returns a summary of search results.
    """
    logger.info(f"[Internet Search] Query: {query}")
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=5)]
        
        if not results:
            return "No internet results found for this query."
            
        context_str = ""
        for i, r in enumerate(results):
            context_str += f"[{i+1}] {r.get('title', '')}\n{r.get('body', '')}\n\n"
        return context_str
    except Exception as e:
        logger.error(f"Internet search failed: {e}")
        return "Internet search is currently unavailable."
