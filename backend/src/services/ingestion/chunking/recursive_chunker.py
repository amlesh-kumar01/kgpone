from typing import Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.services.ingestion.chunking.base import BaseChunker

class RecursiveChunker(BaseChunker):
    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 250):
        # We recursively chunk large sections down to target size, keeping paragraphs intact
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )

    def chunk(self, text: str) -> list[dict[str, Any]]:
        # Simply split the raw text into sized chunks intelligently
        final_docs = self.recursive_splitter.create_documents([text])
        
        chunks = []
        for i, doc in enumerate(final_docs):
            chunks.append({
                "chunk_index": i,
                "section_title": "", # Removing strict markdown header tracking as it over-fragments
                "content": doc.page_content
            })
            
        return chunks
