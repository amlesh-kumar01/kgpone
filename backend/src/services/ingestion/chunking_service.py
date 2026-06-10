import re
from typing import List, Dict, Any

class ChunkingService:
    def chunk_markdown(self, markdown_text: str, chunk_size: int = 800, overlap: int = 150) -> List[Dict[str, Any]]:
        """
        Splits a markdown document into chunks. Preserves headers where possible.
        Each chunk is returned as a dict:
        {
            "text": str,
            "header": str,
            "page_number": int
        }
        """
        # Search for page marker patterns like "Page X" or "--- (page change)" from LlamaParse
        # Often llama-parse outputs markdown pages separated by horizontal rules or page breaks.
        pages = re.split(r'---', markdown_text)
        if len(pages) <= 1:
            pages = [markdown_text]

        chunks = []
        
        for page_idx, page_content in enumerate(pages):
            page_num = page_idx + 1
            
            # Simple header extraction heuristic
            current_header = "Introduction"
            lines = page_content.split("\n")
            
            text_buffer = []
            current_char_count = 0
            
            for line in lines:
                # Detect header
                header_match = re.match(r'^(#{1,6})\s+(.*)$', line)
                if header_match:
                    current_header = header_match.group(2).strip()
                
                text_buffer.append(line)
                current_char_count += len(line) + 1 # +1 for newline
                
                if current_char_count >= chunk_size:
                    # Flush buffer
                    chunk_text = "\n".join(text_buffer)
                    chunks.append({
                        "text": chunk_text,
                        "header": current_header,
                        "page_number": page_num
                    })
                    # Keep some lines for overlap
                    overlap_lines = text_buffer[-3:] if len(text_buffer) > 3 else text_buffer
                    text_buffer = list(overlap_lines)
                    current_char_count = sum(len(l) + 1 for l in text_buffer)
            
            # Flush remaining buffer for this page
            if text_buffer:
                chunk_text = "\n".join(text_buffer)
                chunks.append({
                    "text": chunk_text,
                    "header": current_header,
                    "page_number": page_num
                })
                
        return chunks
