import logging
import uuid
from typing import List, Dict, Any, Tuple
from src.services.ingestion.canonical.ast_schema import ASTNode, NodeType, CanonicalDocument

logger = logging.getLogger("ast_chunker")

class ASTChunker:
    def __init__(self, max_chunk_tokens: int = 500):
        self.max_chunk_tokens = max_chunk_tokens
        # Very rough estimation of tokens = len(text) / 4
        self.chars_per_token = 4
        
    def chunk(self, doc: CanonicalDocument, entities: List[Dict], formulas: List[Dict]) -> List[Dict[str, Any]]:
        chunks = []
        
        # Build maps for quick lookup by node_id
        node_to_concepts = {}
        for ent in entities:
            concept_id = ent.get("canonical_name")
            for node_id in ent.get("source_node_ids", []):
                if node_id not in node_to_concepts:
                    node_to_concepts[node_id] = set()
                node_to_concepts[node_id].add(concept_id)
                
        node_to_formulas = {}
        for form in formulas:
            f_id = form.get("id")
            node_id = form.get("source_node_id")
            if node_id:
                if node_id not in node_to_formulas:
                    node_to_formulas[node_id] = set()
                node_to_formulas[node_id].add(f_id)
                
        # State during traversal
        current_heading_path = []
        current_section_id = None
        current_chapter_id = None
        
        current_text_chunk_nodes = []
        current_text_chunk_length = 0
        
        def flush_text_chunk():
            nonlocal current_text_chunk_nodes, current_text_chunk_length
            if not current_text_chunk_nodes:
                return
                
            text = "\\n".join(n.text_content for n in current_text_chunk_nodes if n.text_content)
            if not text.strip():
                current_text_chunk_nodes = []
                current_text_chunk_length = 0
                return
                
            # Aggregate metadata
            node_ids = [n.id for n in current_text_chunk_nodes]
            concept_ids = set()
            formula_ids = set()
            pages = set()
            for n in current_text_chunk_nodes:
                if n.id in node_to_concepts:
                    concept_ids.update(node_to_concepts[n.id])
                if n.id in node_to_formulas:
                    formula_ids.update(node_to_formulas[n.id])
                if n.source and n.source.page_start:
                    pages.add(n.source.page_start)
                    
            chunks.append({
                "chunk_id": str(uuid.uuid4()),
                "text": text,
                "heading_path": list(current_heading_path),
                "section_id": current_section_id,
                "chapter_id": current_chapter_id,
                "concept_ids": list(concept_ids),
                "formula_ids": list(formula_ids),
                "pages": list(pages),
                "parser": doc.provenance.parser_used,
                "quality_score": doc.provenance.quality_score,
                "source_node_ids": node_ids
            })
            
            current_text_chunk_nodes = []
            current_text_chunk_length = 0
            
        def process_node(node: ASTNode, path: List[str]):
            nonlocal current_section_id, current_chapter_id, current_heading_path, current_text_chunk_nodes, current_text_chunk_length
            
            # Handle hierarchy boundaries
            if node.type in [NodeType.CHAPTER, NodeType.SECTION, NodeType.SUBSECTION]:
                flush_text_chunk()
                title = node.title or node.text_content.strip()
                if title:
                    current_heading_path = path + [title]
                if node.type == NodeType.CHAPTER:
                    current_chapter_id = node.id
                elif node.type == NodeType.SECTION:
                    current_section_id = node.id
                    
            # Handle standalone chunks
            elif node.type in [NodeType.EQUATION, NodeType.FORMULA, NodeType.TABLE, NodeType.FIGURE, NodeType.CODE_BLOCK]:
                flush_text_chunk()
                
                concept_ids = list(node_to_concepts.get(node.id, set()))
                formula_ids = list(node_to_formulas.get(node.id, set()))
                pages = [node.source.page_start] if node.source and node.source.page_start else []
                
                text = node.text_content
                if node.type in [NodeType.EQUATION, NodeType.FORMULA] and getattr(node, "latex", None):
                    text = node.latex
                elif node.type == NodeType.TABLE and getattr(node, "headers", None):
                    text = f"Table Headers: {', '.join(node.headers)}\\n" + text
                    
                chunks.append({
                    "chunk_id": str(uuid.uuid4()),
                    "text": text,
                    "heading_path": list(current_heading_path),
                    "section_id": current_section_id,
                    "chapter_id": current_chapter_id,
                    "concept_ids": concept_ids,
                    "formula_ids": formula_ids,
                    "pages": pages,
                    "parser": doc.provenance.parser_used,
                    "quality_score": doc.provenance.quality_score,
                    "source_node_ids": [node.id]
                })
                
            # Handle text content
            else:
                if node.text_content:
                    node_len = len(node.text_content)
                    if current_text_chunk_length + node_len > self.max_chunk_tokens * self.chars_per_token and current_text_chunk_nodes:
                        flush_text_chunk()
                    
                    current_text_chunk_nodes.append(node)
                    current_text_chunk_length += node_len
                    
            # Recurse
            for child in node.children:
                process_node(child, list(current_heading_path))
                
        for root_node in doc.nodes:
            process_node(root_node, [])
            
        flush_text_chunk()
        return chunks
