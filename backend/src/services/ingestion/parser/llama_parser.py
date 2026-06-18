import os
import asyncio
import logging
from typing import Optional
from llama_parse import LlamaParse
from src.services.ingestion.parser.base import BaseParser

logger = logging.getLogger("llama_parser")

class LlamaParserImpl(BaseParser):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("LLAMA_CLOUD_API_KEY")
        self.use_fallback = False
        if not self.api_key:
            logger.warning("LLAMA_CLOUD_API_KEY is not configured. Falling back to local offline PDF parsing via pypdf.")
            self.use_fallback = True

    async def parse(self, file_path: str, parsing_instructions: Optional[str] = None) -> str:
        """
        Parses a PDF asynchronously using LlamaParse and returns the extracted markdown.
        Falls back to pypdf if API key is missing or parsing fails.
        """
        if self.use_fallback:
            return await self._parse_local(file_path)

        math_instructions = (
            "The provided document contains complex mathematical and thermodynamic equations, tables, and multi-column layouts. "
            "Extract the entire text and content of the document in full. "
            "Ensure all mathematical expressions, equations, and inline math are formatted clearly in standard LaTeX "
            "(e.g., using $$ for block equations or $ for inline math). Keep all tables formatted in standard markdown tables."
        )
        
        if parsing_instructions:
            math_instructions += f"\n\nAdditional instructions from user:\n{parsing_instructions}"

        try:
            parser = LlamaParse(
                api_key=self.api_key,
                result_type="markdown",
                parsing_instruction=math_instructions,
                verbose=False
            )
            # load_data is blocking, so run it in a threadpool to avoid blocking the async event loop if needed
            documents = await asyncio.to_thread(parser.load_data, str(file_path))
            
            if not documents:
                raise RuntimeError("No content was returned from LlamaParse.")

            full_text = "\n\n".join([doc.text for doc in documents])
            return full_text
        except Exception as e:
            logger.warning(f"LlamaParse failed: {e}. Falling back to local offline PDF parsing via pypdf.")
            return await self._parse_local(file_path)

    async def _parse_local(self, file_path: str) -> str:
        """Extracts text from PDF locally using pypdf."""
        import pypdf
        
        def extract_text():
            text_parts = []
            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                for page_num, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")
            return "\n\n".join(text_parts)

        try:
            return await asyncio.to_thread(extract_text)
        except Exception as e:
            logger.error(f"Local offline parsing failed: {e}")
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
            except Exception:
                return "Failed to parse document content."
