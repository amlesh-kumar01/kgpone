from typing import Any
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from src.services.ingestion.chunking.base import BaseChunker

class RecursiveChunker(BaseChunker):
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        # We first split by markdown headers to keep logical sections together
        self.headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        self.markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=self.headers_to_split_on)
        
        # Then we recursively chunk large sections down to target size
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )

    def chunk(self, text: str) -> list[dict[str, Any]]:
        # 1. Split by Markdown headers
        md_docs = self.markdown_splitter.split_text(text)
        
        # 2. Split into smaller chunks if necessary
        final_docs = self.recursive_splitter.split_documents(md_docs)
        
        chunks = []
        for i, doc in enumerate(final_docs):
            # doc.metadata will contain things like {"Header 1": "Introduction", "Header 2": "Background"}
            section_titles = " > ".join(doc.metadata.values()) if doc.metadata else ""
            chunks.append({
                "chunk_index": i,
                "section_title": section_titles,
                "content": doc.page_content
            })
            
        return chunks
