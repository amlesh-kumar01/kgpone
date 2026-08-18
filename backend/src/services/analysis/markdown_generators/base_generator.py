from abc import ABC, abstractmethod
from typing import List, Dict, Any
from src.infrastructure.llm_factory import LLMFactory

class BaseMarkdownGenerator(ABC):
    def __init__(self):
        self.llm = LLMFactory().get_llm()

    @abstractmethod
    async def generate(self, ast_data: Dict[str, Any], topics: List[str], prompt: str, doc_title: str) -> str:
        pass
        
    def filter_ast(self, ast_data: Dict[str, Any], topics: List[str]) -> str:
        """Helper to extract relevant text chunks from AST."""
        # Simple extraction for now, can be improved with vector search or topic filtering
        text_chunks = []
        def extract_text(nodes):
            for n in nodes:
                if n.get("text_content"):
                    text_chunks.append(n["text_content"])
                if "children" in n and n["children"]:
                    extract_text(n["children"])
        
        extract_text(ast_data.get("nodes", []))
        # Limit to avoid huge context, e.g. first 20 chunks
        # In a real scenario, filter these based on the `topics` matching their concepts
        return "\n\n".join(text_chunks[:20])
