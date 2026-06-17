import os
import asyncio
from typing import Optional
from llama_parse import LlamaParse
from src.services.ingestion.parser.base import BaseParser

class LlamaParserImpl(BaseParser):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("LLAMA_CLOUD_API_KEY")
        if not self.api_key:
            raise ValueError("LLAMA_CLOUD_API_KEY is not configured.")

    async def parse(self, file_path: str, parsing_instructions: Optional[str] = None) -> str:
        """
        Parses a PDF asynchronously using LlamaParse and returns the extracted markdown.
        """
        math_instructions = (
            "The provided document contains complex mathematical and thermodynamic equations, tables, and multi-column layouts. "
            "Extract the entire text and content of the document in full. "
            "Ensure all mathematical expressions, equations, and inline math are formatted clearly in standard LaTeX "
            "(e.g., using $$ for block equations or $ for inline math). Keep all tables formatted in standard markdown tables."
        )
        
        if parsing_instructions:
            math_instructions += f"\n\nAdditional instructions from user:\n{parsing_instructions}"

        parser = LlamaParse(
            api_key=self.api_key,
            result_type="markdown",
            parsing_instruction=math_instructions,
            verbose=False
        )

        # load_data is blocking, so run it in a threadpool to avoid blocking the async event loop if needed,
        # but since we're in a celery worker, it can be sync or async. We wrap it in asyncio.to_thread just in case.
        documents = await asyncio.to_thread(parser.load_data, str(file_path))
        
        if not documents:
            raise RuntimeError("No content was returned from LlamaParse.")

        full_text = "\n\n".join([doc.text for doc in documents])
        return full_text
